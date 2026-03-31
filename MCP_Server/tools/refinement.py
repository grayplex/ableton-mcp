"""Refinement tools: section state reading for iterative refinement workflow."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import get_ableton_connection
from MCP_Server.devices.catalog import CATALOG
from MCP_Server.devices.convert import natural_to_normalized
from MCP_Server.mixing.catalog import get_recipe
from MCP_Server.refinement.schema import ClipSummary, SectionState, TrackStateEntry
from MCP_Server.server import mcp
from MCP_Server.tools.analysis import _infer_role
from MCP_Server.tools.intelligence import _find_track
from MCP_Server.tools.scaffold import _beat_to_bar

RECIPE_DELTA_THRESHOLD = 0.20

_PROMINENT_PARAMS = {
    "AutoFilter": ["Frequency", "Resonance", "Filter Type"],
    "Compressor2": ["Threshold", "Ratio", "Attack Time"],
    "Eq8": ["Frequency 1", "Gain 1", "Frequency 4"],
}


def _note_summary(notes: list, clip_length_beats: float, beats_per_bar: float) -> dict:
    """Compute pitch range, octave, and rhythm density for a list of notes."""
    if not notes:
        return {
            "note_count": 0,
            "pitch_min": None,
            "pitch_max": None,
            "dominant_octave": None,
            "rhythm_density": None,
        }
    pitches = [n["pitch"] for n in notes]
    pitch_min = min(pitches)
    pitch_max = max(pitches)
    dominant_octave = (pitch_min + pitch_max) // 2 // 12
    clip_length_bars = clip_length_beats / beats_per_bar if beats_per_bar > 0 else 1.0
    rhythm_density = round(len(notes) / clip_length_bars, 2) if clip_length_bars > 0 else 0.0
    return {
        "note_count": len(notes),
        "pitch_min": pitch_min,
        "pitch_max": pitch_max,
        "dominant_octave": dominant_octave,
        "rhythm_density": rhythm_density,
    }


def _device_summary(device: dict) -> dict:
    """Build a device summary with prominent parameters."""
    class_name = device["class_name"]
    param_names = _PROMINENT_PARAMS.get(class_name, None)
    all_params = {p["name"]: p["value"] for p in device.get("parameters", [])}
    if param_names:
        prominent = {k: all_params[k] for k in param_names if k in all_params}
    else:
        prominent = dict(list(all_params.items())[:3])
    return {
        "device_name": device.get("device_name", device["class_name"]),
        "class_name": class_name,
        "prominent_params": prominent,
    }


def _recipe_delta(track_devices: list, role: str, genre: str) -> list:
    """Return list of {device, param, current_normalized, recipe_normalized} for params >20% off recipe."""
    recipe = get_recipe(role, genre)
    if recipe is None:
        return []
    delta_list = []
    device_map = {d["class_name"]: d for d in track_devices}
    for device_class, recipe_params in recipe.items():
        if device_class not in device_map:
            continue
        current_params = {p["name"]: p["value"] for p in device_map[device_class].get("parameters", [])}
        display_name = CATALOG.get(device_class, {}).get("display_name", device_class)
        for param_name, recipe_natural in recipe_params.items():
            if param_name not in current_params:
                continue
            current_norm = current_params[param_name]
            suggested_norm = natural_to_normalized(device_class, param_name, recipe_natural)
            if abs(current_norm - suggested_norm) > RECIPE_DELTA_THRESHOLD:
                delta_list.append({
                    "device": display_name,
                    "param": param_name,
                    "current": round(current_norm, 4),
                    "recipe": round(suggested_norm, 4),
                })
    return delta_list


@mcp.tool()
def get_section_state(ctx: Context, section_name: str, genre: str = None) -> str:
    """Get a structured snapshot of everything built in a named arrangement section.

    Returns track-by-track state for all tracks with clips in the section:
    clips with note summaries (pitch range, density), device chains with
    prominent parameter values, and optional recipe delta when genre is provided.

    Args:
        section_name: Name of the arrangement section (matches locator name, case-insensitive)
        genre: Optional genre for recipe delta computation (e.g. "house", "techno")
    """
    conn = get_ableton_connection()

    # 1. Get arrangement state: locators + tracks + time signature
    arrangement_state = conn.send_command("get_arrangement_state", {})
    cue_points = arrangement_state.get("cue_points", [])
    sig_num = arrangement_state.get("signature_numerator", 4)
    sig_den = arrangement_state.get("signature_denominator", 4)
    song_length = arrangement_state.get("song_length", 0.0)
    arrangement_tracks = arrangement_state.get("tracks", [])

    # 2. Compute beats per bar
    beats_per_bar = sig_num * (4.0 / sig_den)

    # 3. Find the matching locator (case-insensitive)
    section_name_lower = section_name.lower()
    locator_index = None
    for i, cp in enumerate(cue_points):
        if cp.get("name", "").lower() == section_name_lower:
            locator_index = i
            break

    if locator_index is None:
        result: SectionState = {
            "section": section_name,
            "start_bar": 0,
            "end_bar": 0,
            "tracks": [],
            "error": f"Section '{section_name}' not found in arrangement",
        }
        return json.dumps(result)

    # 4. Compute section beat range
    section_start_beat = cue_points[locator_index]["time"]
    if locator_index + 1 < len(cue_points):
        section_end_beat = cue_points[locator_index + 1]["time"]
    else:
        section_end_beat = song_length

    start_bar = _beat_to_bar(section_start_beat, beats_per_bar)
    end_bar = _beat_to_bar(section_end_beat, beats_per_bar)

    # 5. Get mix state once (cached for all tracks)
    mix_state = conn.send_command("get_mix_state", {})

    # 6. Process each track
    track_entries: list[TrackStateEntry] = []

    for track_info in arrangement_tracks:
        track_index = track_info["index"]
        track_name = track_info["name"]

        # Get clips for this track
        clips_result = conn.send_command("get_arrangement_clips", {"track_index": track_index})
        all_clips = clips_result.get("clips", [])

        # Filter clips that start within section range
        section_clips = [
            c for c in all_clips
            if section_start_beat <= c["start_time"] < section_end_beat
        ]

        if not section_clips:
            continue  # D-09: omit tracks with no clips in section

        # Build ClipSummary for each clip
        clip_summaries: list[ClipSummary] = []
        for clip in section_clips:
            clip_start_beat = clip["start_time"]
            clip_end_beat = clip["end_time"]
            clip_length_beats = clip.get("length", clip_end_beat - clip_start_beat)
            clip_start_bar = _beat_to_bar(clip_start_beat, beats_per_bar)
            clip_end_bar = _beat_to_bar(clip_end_beat, beats_per_bar)
            clip_length_bars = clip_end_bar - clip_start_bar
            is_audio = clip.get("is_audio_clip", False)

            if is_audio:
                summary: ClipSummary = {
                    "name": clip.get("name", ""),
                    "start_bar": clip_start_bar,
                    "end_bar": clip_end_bar,
                    "length_bars": clip_length_bars,
                    "is_audio": True,
                    "note_count": None,
                    "pitch_min": None,
                    "pitch_max": None,
                    "dominant_octave": None,
                    "rhythm_density": None,
                }
            else:
                notes_result = conn.send_command(
                    "get_arrangement_clip_notes",
                    {"track_index": track_index, "clip_start_time": clip_start_beat},
                )
                notes = notes_result.get("notes", [])
                ns = _note_summary(notes, clip_length_beats, beats_per_bar)
                summary = {
                    "name": clip.get("name", ""),
                    "start_bar": clip_start_bar,
                    "end_bar": clip_end_bar,
                    "length_bars": clip_length_bars,
                    "is_audio": False,
                    "note_count": ns["note_count"],
                    "pitch_min": ns["pitch_min"],
                    "pitch_max": ns["pitch_max"],
                    "dominant_octave": ns["dominant_octave"],
                    "rhythm_density": ns["rhythm_density"],
                }

            clip_summaries.append(summary)

        # 7. Build mix_context
        role = _infer_role(track_name)
        mix_track = _find_track(mix_state, track_name)
        track_devices = []
        volume = None
        pan = None

        if mix_track is not None:
            volume = mix_track.get("volume")
            pan = mix_track.get("pan")
            track_devices = mix_track.get("devices", [])

        device_summaries = [_device_summary(d) for d in track_devices]

        # Compute recipe_delta only when genre is provided and role is known
        delta = []
        if genre is not None and role is not None:
            delta = _recipe_delta(track_devices, role, genre)

        mix_context = {
            "volume": volume,
            "pan": pan,
            "devices": device_summaries,
            "recipe_delta": delta,
        }

        entry: TrackStateEntry = {
            "track_name": track_name,
            "track_index": track_index,
            "role": role,
            "clips": clip_summaries,
            "mix_context": mix_context,
        }
        track_entries.append(entry)

    result = {
        "section": section_name,
        "start_bar": start_bar,
        "end_bar": end_bar,
        "tracks": track_entries,
        "error": None,
    }
    return json.dumps(result)
