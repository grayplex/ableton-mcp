"""Refinement tools: section state reading for iterative refinement workflow."""

import json
import re

from mcp.server.fastmcp import Context

from MCP_Server.connection import get_ableton_connection
from MCP_Server.devices.catalog import CATALOG
from MCP_Server.devices.convert import natural_to_normalized
from MCP_Server.mixing.catalog import get_recipe
from MCP_Server.prompt.deriver import (
    _derive_effect_hints,
    _derive_energy_level,
    _derive_groove_feel,
    _derive_key_feel,
    _derive_tempo,
    _derive_velocity_style,
)
from MCP_Server.prompt.lexicon import GROOVE_HINTS
from MCP_Server.prompt.parser import classify_prompt
from MCP_Server.refinement.interpreter import build_section_refinement_plan
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


@mcp.tool()
def interpret_section_refinement(ctx: Context, section_name: str, instruction: str) -> str:
    """Interpret a refinement instruction for a named section — returns a read-only plan.

    Reads the current section state, maps the instruction through the refinement
    lexicon to a concrete SectionRefinementPlan: per-track note operations (semitone
    shifts, scale substitutions) and device parameter targets. Does NOT apply changes.

    Use refine_section() to apply changes from this plan.

    Args:
        section_name: Named arrangement section (matches locator, case-insensitive)
        instruction: Refinement instruction ("make it darker", "add more swing", "higher register")
    """
    conn = get_ableton_connection()
    plan = build_section_refinement_plan(section_name, instruction, conn)
    return json.dumps(plan)


@mcp.tool()
def refine_prompt(ctx: Context, brief: dict, refinement_text: str) -> str:
    """Refine an existing ProductionBrief with a follow-up instruction.

    Takes an existing ProductionBrief (from interpret_prompt) and a refinement
    string ("make it faster", "darker key feel", "add more swing"), re-derives
    only the parameters affected by the new signals, and returns the updated
    brief plus a diff showing which fields changed.

    Fields not mentioned in the refinement are preserved verbatim.

    Args:
        brief: Existing ProductionBrief dict (from interpret_prompt output)
        refinement_text: Follow-up refinement string
    """
    # 1. Classify refinement text
    signals = classify_prompt(refinement_text)

    # 2. Start with copy of original brief
    updated = dict(brief)
    reasoning = list(brief.get("reasoning", []))
    diff = {}

    # 3. Low-confidence warning
    if brief.get("confidence", 1.0) < 0.3:
        reasoning.append(
            f"Warning: original brief has low confidence ({brief['confidence']:.2f}) — some fields may be unreliable"
        )

    # 4. Genre signals → re-derive genre-dependent fields
    if signals["genre_signals"]:
        original_genre = updated.get("primary_genre")
        new_genre = signals["genre_signals"][0]
        updated["primary_genre"] = new_genre
        diff["primary_genre"] = {"before": original_genre, "after": new_genre}

        # Re-derive all genre-dependent fields using actual _derive_tempo signature:
        # _derive_tempo(genre_id, mood_signals, tempo_signals, energy_level, raw_prompt)
        energy_level = updated.get("energy_level", 5)
        new_tempo, t_reason = _derive_tempo(
            new_genre,
            signals["mood_signals"],
            signals["tempo_signals"],
            energy_level,
            refinement_text,
        )
        if new_tempo != updated.get("tempo_range"):
            diff["tempo_range"] = {"before": updated["tempo_range"], "after": new_tempo}
            updated["tempo_range"] = new_tempo
        new_key, k_reason = _derive_key_feel(new_genre, signals["mood_signals"])
        if new_key != updated.get("key_feel"):
            diff["key_feel"] = {"before": updated["key_feel"], "after": new_key}
            updated["key_feel"] = new_key
        reasoning.append(t_reason)
        reasoning.append(k_reason)

    # 5. Mood signals (without genre override)
    elif signals["mood_signals"]:
        original_key = updated.get("key_feel")
        new_key, k_reason = _derive_key_feel(updated.get("primary_genre"), signals["mood_signals"])
        if new_key != original_key:
            diff["key_feel"] = {"before": original_key, "after": new_key}
            updated["key_feel"] = new_key
            reasoning.append(k_reason)

        energy, e_reason = _derive_energy_level(signals["mood_signals"])
        if energy != updated.get("energy_level"):
            diff["energy_level"] = {"before": updated.get("energy_level"), "after": energy}
            updated["energy_level"] = energy
            reasoning.append(e_reason)

        vel, v_reason = _derive_velocity_style(updated["energy_level"], signals["mood_signals"])
        if vel != updated.get("velocity_style"):
            diff["velocity_style"] = {"before": updated.get("velocity_style"), "after": vel}
            updated["velocity_style"] = vel
            reasoning.append(v_reason)

    # 6. Tempo signals (explicit BPM or tempo words)
    # Also detect explicit BPM numbers in raw text (e.g. "140 BPM") — these are
    # extracted by _derive_tempo's regex but don't produce a tempo_signal token.
    _has_explicit_bpm = bool(
        re.search(r"\b(\d{2,3})\s*(?:bpm|beats?\s+per\s+minute)\b", refinement_text, re.IGNORECASE)
    )
    if signals["tempo_signals"] or _has_explicit_bpm:
        original_tempo = updated.get("tempo_range")
        energy_level = updated.get("energy_level", 5)
        new_tempo, t_reason = _derive_tempo(
            updated.get("primary_genre"),
            signals["mood_signals"],
            signals["tempo_signals"],
            energy_level,
            refinement_text,
        )
        if new_tempo != original_tempo:
            diff["tempo_range"] = {"before": original_tempo, "after": new_tempo}
            updated["tempo_range"] = new_tempo
            reasoning.append(t_reason)

    # 7. Groove structural hints
    groove_override = None
    for hint in signals.get("structural_hints", []):
        if hint in GROOVE_HINTS:
            groove_override = hint
            break
    if groove_override:
        original_groove = updated.get("groove_feel")
        # _derive_groove_feel(genre_id, structural_hints, raw_descriptors)
        new_groove, g_reason = _derive_groove_feel(
            updated.get("primary_genre"),
            signals["structural_hints"],
            signals.get("raw_descriptors", []),
        )
        if new_groove != original_groove:
            diff["groove_feel"] = {"before": original_groove, "after": new_groove}
            updated["groove_feel"] = new_groove
            reasoning.append(g_reason)

    # 8. Effect signals
    if signals["effect_signals"]:
        original_effects = updated.get("effect_hints", [])
        # _derive_effect_hints takes a list of effect signal strings
        new_effects, fx_reason = _derive_effect_hints(signals["effect_signals"])
        merged = list({*original_effects, *new_effects})
        if merged != original_effects:
            diff["effect_hints"] = {"before": original_effects, "after": merged}
            updated["effect_hints"] = merged
            reasoning.append(fx_reason)

    # 9. If no signals matched at all, add a note to reasoning
    if not any([
        signals["genre_signals"],
        signals["mood_signals"],
        signals["tempo_signals"],
        signals["effect_signals"],
    ]):
        reasoning.append(f"No recognized signals in '{refinement_text}' — brief unchanged")

    updated["reasoning"] = reasoning

    return json.dumps({"brief": updated, "diff": diff})


# ---------------------------------------------------------------------------
# Phase 47 helpers
# ---------------------------------------------------------------------------

def _find_track_index(arrangement_tracks: list, track_name: str):
    """Find track index by case-insensitive substring match."""
    name_lower = track_name.lower()
    for t in arrangement_tracks:
        if name_lower in t["name"].lower():
            return t["index"]
    return None


def _find_device_index(mix_state_track: dict, class_name: str):
    """Find device index by class_name match in mix state track."""
    for d in mix_state_track.get("devices", []):
        if d.get("class_name") == class_name:
            return d.get("index")
    return None


@mcp.tool()
def apply_section_note_refinement(
    ctx: Context,
    section_name: str,
    track_name: str,
    semitone_shift: int = 0,
    density_delta: int = 0,
    scale_substitutions: list = None,
    velocity_shift: int = 0,
) -> str:
    """Apply note-level changes to arrangement clips for one track within a section.

    Only clips whose start_time falls within the section's bar range are modified.
    Clips outside the section range are untouched. Audio clips are skipped.

    Operations are applied in order: transpose first, then scale substitutions +
    velocity shift + density changes in a single modify call.

    Args:
        section_name: Named arrangement section (matches locator, case-insensitive)
        track_name: Track name to modify (case-insensitive substring match)
        semitone_shift: Semitones to transpose all notes (0 = no change)
        density_delta: +1 duplicate notes, -1 halve notes, 0 = no change
        scale_substitutions: List of {from_pitch_class, to_pitch_class} dicts
        velocity_shift: +/- MIDI velocity adjustment (0 = no change)
    """
    if scale_substitutions is None:
        scale_substitutions = []

    conn = get_ableton_connection()
    arrangement_state = conn.send_command("get_arrangement_state", {})
    cue_points = arrangement_state.get("cue_points", [])
    sig_num = arrangement_state.get("signature_numerator", 4)
    sig_den = arrangement_state.get("signature_denominator", 4)
    song_length = arrangement_state.get("song_length", 0.0)
    arrangement_tracks = arrangement_state.get("tracks", [])
    beats_per_bar = sig_num * (4.0 / sig_den)

    # Find section beat range
    section_name_lower = section_name.lower()
    locator_index = None
    for i, cp in enumerate(cue_points):
        if cp.get("name", "").lower() == section_name_lower:
            locator_index = i
            break

    if locator_index is None:
        return json.dumps({
            "clips_modified": 0, "notes_modified": 0,
            "track": track_name, "section": section_name,
            "error": f"Section '{section_name}' not found",
        })

    section_start_beat = cue_points[locator_index]["time"]
    section_end_beat = (
        cue_points[locator_index + 1]["time"]
        if locator_index + 1 < len(cue_points)
        else song_length
    )

    track_index = _find_track_index(arrangement_tracks, track_name)
    if track_index is None:
        return json.dumps({
            "clips_modified": 0, "notes_modified": 0,
            "track": track_name, "section": section_name,
            "error": f"Track '{track_name}' not found",
        })

    clips_result = conn.send_command("get_arrangement_clips", {"track_index": track_index})
    all_clips = clips_result.get("clips", [])
    section_clips = [
        c for c in all_clips
        if section_start_beat <= c["start_time"] < section_end_beat
        and not c.get("is_audio_clip", False)
    ]

    clips_modified = 0
    notes_modified = 0

    for clip in section_clips:
        clip_start = clip["start_time"]

        if semitone_shift != 0:
            result = conn.send_command("transpose_arrangement_clip", {
                "track_index": track_index,
                "clip_start_time": clip_start,
                "semitones": semitone_shift,
            })
            notes_modified += result.get("transposed_count", 0)

        needs_modify = scale_substitutions or velocity_shift != 0 or density_delta != 0
        if needs_modify:
            notes_result = conn.send_command("get_arrangement_clip_notes", {
                "track_index": track_index,
                "clip_start_time": clip_start,
            })
            current_notes = notes_result.get("notes", [])

            # Apply scale substitutions
            if scale_substitutions:
                sub_map = {s["from_pitch_class"]: s["to_pitch_class"] for s in scale_substitutions}
                new_notes = []
                for n in current_notes:
                    pc = n["pitch"] % 12
                    if pc in sub_map:
                        delta = sub_map[pc] - pc
                        new_pitch = max(0, min(127, n["pitch"] + delta))
                        new_notes.append({**n, "pitch": new_pitch})
                    else:
                        new_notes.append(n)
                current_notes = new_notes

            # Apply velocity shift
            if velocity_shift != 0:
                current_notes = [
                    {**n, "velocity": max(1, min(127, n["velocity"] + velocity_shift))}
                    for n in current_notes
                ]

            # Apply density delta
            if density_delta == -1 and current_notes:
                current_notes = sorted(current_notes, key=lambda n: n["start_time"])
                current_notes = current_notes[::2]  # keep every other note
            elif density_delta == 1 and current_notes:
                doubles = []
                for n in current_notes:
                    doubles.append({
                        **n,
                        "start_time": n["start_time"] + n["duration"] / 2,
                        "velocity": max(1, n["velocity"] // 2),
                    })
                current_notes = current_notes + doubles

            if current_notes:
                mod_result = conn.send_command("modify_arrangement_clip_notes", {
                    "track_index": track_index,
                    "clip_start_time": clip_start,
                    "notes": current_notes,
                })
                notes_modified += mod_result.get("modified_count", 0)

        clips_modified += 1

    return json.dumps({
        "clips_modified": clips_modified,
        "notes_modified": notes_modified,
        "track": track_name,
        "section": section_name,
    })


@mcp.tool()
def apply_section_device_refinement(
    ctx: Context,
    section_name: str,
    track_name: str,
    param_targets: dict,
    write_automation: bool = False,
) -> str:
    """Apply device parameter changes to a track in a named section.

    param_targets format: {device_class_name: {param_name: normalized_float}}
    Example: {"AutoFilter": {"Frequency": 0.35}, "Compressor2": {"Threshold": 0.4}}

    When write_automation=False (default): applies changes globally to the track
    (affects all sections). Use for quick iteration.

    When write_automation=True: applies the same global change and returns a note
    explaining that per-section automation requires Ableton's arrangement recording.

    Args:
        section_name: Named arrangement section (for context, not filtering)
        track_name: Track name (case-insensitive substring match)
        param_targets: {device_class_name: {param_name: normalized_value}} dict
        write_automation: If True, adds guidance note about automation scoping
    """
    conn = get_ableton_connection()
    arrangement_state = conn.send_command("get_arrangement_state", {})
    arrangement_tracks = arrangement_state.get("tracks", [])
    track_index = _find_track_index(arrangement_tracks, track_name)

    if track_index is None:
        return json.dumps({
            "track": track_name, "section": section_name,
            "devices_modified": 0, "params_set": [],
            "error": f"Track '{track_name}' not found",
        })

    mix_state = conn.send_command("get_mix_state", {})
    mix_track = _find_track(mix_state, track_name)

    params_set = []
    skipped_devices = []
    devices_modified = 0

    for class_name, params_dict in param_targets.items():
        if mix_track is None:
            skipped_devices.append(class_name)
            continue

        device_index = _find_device_index(mix_track, class_name)
        if device_index is None:
            skipped_devices.append(class_name)
            continue

        result = conn.send_command("set_device_parameters", {
            "track_index": track_index,
            "device_index": device_index,
            "parameters": params_dict,
        })

        for param_name, value in params_dict.items():
            params_set.append({
                "device": class_name,
                "param": param_name,
                "value": value,
            })
        devices_modified += 1

    response = {
        "track": track_name,
        "section": section_name,
        "devices_modified": devices_modified,
        "params_set": params_set,
    }
    if write_automation:
        response["note"] = (
            "write_automation=True: parameters applied globally to track — "
            "for per-section automation, arm the track, enable arrangement overdub, "
            "and record parameter changes during playback"
        )
    if skipped_devices:
        response["skipped_devices"] = skipped_devices

    return json.dumps(response)


@mcp.tool()
def refine_section(
    ctx: Context,
    section_name: str,
    instruction: str,
    genre: str = None,
    write_automation: bool = False,
) -> str:
    """Interpret a refinement instruction and apply it to a named section end-to-end.

    Single-call workflow: reads section state → interprets instruction → applies
    note changes (transpose, scale substitutions) → applies device changes → returns
    a plain-English summary of exactly what changed.

    Use interpret_section_refinement() first if you want to preview changes before
    applying them.

    Args:
        section_name: Named arrangement section (case-insensitive locator match)
        instruction: Refinement instruction ("make it darker", "add more swing", "higher")
        genre: Optional genre for recipe context during interpretation
        write_automation: Passed to apply_section_device_refinement
    """
    conn = get_ableton_connection()
    plan = build_section_refinement_plan(section_name, instruction, conn)

    if not plan["tracks"]:
        return json.dumps({
            "section": section_name,
            "instruction": instruction,
            "tracks_modified": 0,
            "note_changes": [],
            "device_changes": [],
            "reasoning": plan["reasoning"],
        })

    note_changes = []
    device_changes = []
    tracks_with_changes = set()

    for entry in plan["tracks"]:
        track_name = entry["track_name"]
        note_op = entry["note_operation"]

        has_note_op = (
            note_op["semitone_shift"] != 0
            or note_op["scale_substitutions"]
            or note_op["velocity_shift"] != 0
            or note_op["density_delta"] != 0
        )
        if has_note_op:
            note_result_str = apply_section_note_refinement(
                ctx,
                section_name,
                track_name,
                semitone_shift=note_op["semitone_shift"],
                density_delta=note_op["density_delta"],
                scale_substitutions=note_op["scale_substitutions"],
                velocity_shift=note_op["velocity_shift"],
            )
            note_result = json.loads(note_result_str)
            note_changes.append(note_result)
            if note_result.get("clips_modified", 0) > 0:
                tracks_with_changes.add(track_name)

        if entry["device_changes"]:
            param_targets = {}
            for dc in entry["device_changes"]:
                class_name = dc["class_name"]
                if class_name not in param_targets:
                    param_targets[class_name] = {}
                param_targets[class_name][dc["param_name"]] = dc["target_normalized"]

            dev_result_str = apply_section_device_refinement(
                ctx,
                section_name,
                track_name,
                param_targets,
                write_automation=write_automation,
            )
            dev_result = json.loads(dev_result_str)
            device_changes.append(dev_result)
            if dev_result.get("devices_modified", 0) > 0:
                tracks_with_changes.add(track_name)

    return json.dumps({
        "section": section_name,
        "instruction": instruction,
        "tracks_modified": len(tracks_with_changes),
        "note_changes": note_changes,
        "device_changes": device_changes,
        "reasoning": plan["reasoning"],
    })
