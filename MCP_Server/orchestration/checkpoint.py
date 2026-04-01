"""Production checkpoint: infer phase progress from live Ableton session state."""

import logging
import time
from MCP_Server.connection import get_ableton_connection
from MCP_Server.genres.catalog import resolve_alias
from MCP_Server.orchestration.agenda import AGENDA_CATALOG
from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER
from MCP_Server.orchestration.schema import ProductionCheckpoint, SessionStats

logger = logging.getLogger("AbletonMCPServer")

# TTL cache for get_checkpoint — avoids repeated Ableton queries in agent loops
_checkpoint_cache: dict = {}  # key: genre (str|None) -> {"result": dict, "ts": float}
_CACHE_TTL = 30.0  # seconds

# Device class names local to checkpoint only (not shared with next_actions)
_DRUM_DEVICE = "DrumGroupDevice"
_EQ = "Eq8"

# Resume hints per active phase
_RESUME_HINTS = {
    "setup":       "Start with setup: call set_tempo, set_scale, then scaffold_arrangement",
    "drums":       "Continue with drum programming: create a Drums track, load Drum Rack, add kick/snare/hi-hat notes",
    "bass":        "Continue with bass: create a Bass track, load Analog, and write a bass line",
    "harmony":     "Continue with harmony: create a Chords track, load Wavetable, add chord progression",
    "melody":      "Continue with melody: create a Lead track, load Operator, write the main melody",
    "sound_design": "Continue with sound design: add Auto Filter and Reverb to synth tracks",
    "arrangement": "Continue with arrangement: copy clips across sections and vary them for dynamic flow",
    "mix":         "Continue with mixing: call apply_mix_recipe for each track role, then check_gain_staging",
    "master":      "Continue with mastering: call apply_master_recipe to complete the master bus chain",
    None:          "Production appears complete — call evaluate_session for a final quality check",
}


def _has_name_match(track_name: str, name_set: set) -> bool:
    name_lower = track_name.lower()
    return any(n in name_lower for n in name_set)


def _track_has_clips(track_name: str, clips_by_track: dict) -> bool:
    clips = clips_by_track.get(track_name, [])
    return len(clips) > 0


def _infer_completed_phases(genre_id: str, tracks: list, clips_by_track: dict,
                             master_devices: list) -> list:
    """Walk AGENDA_CATALOG phase order; return list of phase_ids inferred complete."""
    phase_order = AGENDA_CATALOG.get(genre_id, [])
    all_device_classes = set()
    for t in tracks:
        for d in t.get("devices", []):
            all_device_classes.add(d.get("class_name", ""))

    # If master chain is complete (GlueCompressor + Limiter2 present), all phases done.
    master_class_names = {d.get("class_name", "") for d in master_devices}
    if _GLUE_COMPRESSOR in master_class_names and _LIMITER in master_class_names:
        return list(phase_order)

    completed = []
    for phase_type in phase_order:
        if phase_type == "setup":
            done = len(tracks) >= 2
        elif phase_type == "drums":
            done = any(
                _has_name_match(t["name"], _DRUM_NAMES) and t.get("has_instrument")
                and _track_has_clips(t["name"], clips_by_track)
                for t in tracks
            )
        elif phase_type == "bass":
            done = any(
                _has_name_match(t["name"], _BASS_NAMES) and t.get("has_instrument")
                and _track_has_clips(t["name"], clips_by_track)
                for t in tracks
            )
        elif phase_type == "harmony":
            done = any(
                _has_name_match(t["name"], _HARMONY_NAMES) and t.get("has_instrument")
                and _track_has_clips(t["name"], clips_by_track)
                for t in tracks
            )
        elif phase_type == "melody":
            done = any(
                _has_name_match(t["name"], _MELODY_NAMES) and t.get("has_instrument")
                and _track_has_clips(t["name"], clips_by_track)
                for t in tracks
            )
        elif phase_type == "sound_design":
            # Any track has an effect device (non-instrument)
            effect_classes = {"AutoFilter", "Reverb", "Redux", "Saturator", "Chorus", "Flanger", "Phaser"}
            done = bool(all_device_classes & effect_classes)
        elif phase_type == "arrangement":
            # All tracks have instruments and at least one clip
            tracks_with_instruments = [t for t in tracks if t.get("has_instrument")]
            done = (len(tracks_with_instruments) >= 2
                    and all(_track_has_clips(t["name"], clips_by_track)
                            for t in tracks_with_instruments))
        elif phase_type == "mix":
            # At least one non-master track has Compressor2
            done = _COMPRESSOR in all_device_classes
        elif phase_type == "master":
            master_class_names = {d.get("class_name", "") for d in master_devices}
            done = _GLUE_COMPRESSOR in master_class_names and _LIMITER in master_class_names
        else:
            done = False

        if done:
            completed.append(phase_type)
        else:
            break  # stop at first incomplete phase

    return completed


def _build_session_stats(tracks: list, clips_by_track: dict, master_devices: list) -> dict:
    tracks_with_instruments = sum(1 for t in tracks if t.get("has_instrument"))
    tracks_with_clips = sum(1 for t in tracks if _track_has_clips(t["name"], clips_by_track))
    all_device_classes = set()
    for t in tracks:
        for d in t.get("devices", []):
            all_device_classes.add(d.get("class_name", ""))
    master_class_names = {d.get("class_name", "") for d in master_devices}
    return SessionStats(
        track_count=len(tracks),
        tracks_with_instruments=tracks_with_instruments,
        tracks_with_clips=tracks_with_clips,
        has_mix_applied=_COMPRESSOR in all_device_classes,
        has_master_applied=(_GLUE_COMPRESSOR in master_class_names
                            and _LIMITER in master_class_names),
    )


def get_checkpoint(genre: str = None) -> dict:
    """Read live Ableton state and return a ProductionCheckpoint.

    Results are cached for 30 seconds per genre. Call invalidate_checkpoint_cache()
    after mutating session state to force a fresh read.

    Args:
        genre: Optional genre id or alias. Required for phase inference.

    Returns:
        ProductionCheckpoint dict or {"error": "..."} on connection failure.
    """
    now = time.monotonic()
    cache_key = genre  # None is a valid key
    cached = _checkpoint_cache.get(cache_key)
    if cached and (now - cached["ts"]) < _CACHE_TTL:
        return cached["result"]

    try:
        conn = get_ableton_connection()
        arrangement_state = conn.send_command("get_arrangement_state")
        mix_state = conn.send_command("get_mix_state")
    except Exception as e:
        return {"error": f"Could not connect to Ableton: {e}"}

    tracks = arrangement_state.get("tracks", [])
    master_devices = mix_state.get("master_track", {}).get("devices", [])

    # Build clips_by_track from arrangement_state (no extra round-trips)
    clips_by_track = {}
    for track in tracks:
        # has_clips from get_arrangement_state; use sentinel list for truthy check
        clips_by_track[track["name"]] = ["_"] if track.get("has_clips") else []

    # Empty session
    if not tracks:
        stats = SessionStats(track_count=0, tracks_with_instruments=0,
                             tracks_with_clips=0, has_mix_applied=False,
                             has_master_applied=False)
        result = ProductionCheckpoint(
            genre=genre,
            completed_phases=[],
            active_phase="setup",
            active_phase_progress=0.0,
            pending_steps=["set_tempo", "set_scale", "scaffold_arrangement"],
            session_stats=stats,
            next_phase="drums",
            resume_hint="Session is empty — start with setup: set tempo, set key, and scaffold tracks",
        )
        _checkpoint_cache[cache_key] = {"result": result, "ts": now}
        return result

    # No genre provided
    if not genre:
        stats = _build_session_stats(tracks, clips_by_track, master_devices)
        result = ProductionCheckpoint(
            genre=None,
            completed_phases=[],
            active_phase=None,
            active_phase_progress=0.0,
            pending_steps=[],
            session_stats=stats,
            next_phase=None,
            resume_hint=f"Provide a genre to get phase-specific guidance. Session has {len(tracks)} tracks.",
        )
        _checkpoint_cache[cache_key] = {"result": result, "ts": now}
        return result

    # Resolve genre
    resolved = resolve_alias(genre)
    if resolved is None:
        return {"error": f"Unknown genre '{genre}'."}
    genre_id = resolved["genre_id"]

    stats = _build_session_stats(tracks, clips_by_track, master_devices)
    completed = _infer_completed_phases(genre_id, tracks, clips_by_track, master_devices)

    phase_order = AGENDA_CATALOG.get(genre_id, [])
    active_phase = None
    next_phase = None
    for i, phase_type in enumerate(phase_order):
        if phase_type not in completed:
            active_phase = phase_type
            next_phase = phase_order[i + 1] if i + 1 < len(phase_order) else None
            break

    # Progress estimate for active phase
    progress = 0.0
    if active_phase == "arrangement":
        total = len([t for t in tracks if t.get("has_instrument")])
        with_clips = sum(1 for t in tracks if t.get("has_instrument")
                         and _track_has_clips(t["name"], clips_by_track))
        progress = (with_clips / total) if total > 0 else 0.0
    elif active_phase and stats["tracks_with_instruments"] > 0:
        # Phase started if relevant tracks exist even without clips
        if active_phase == "drums" and any(_has_name_match(t["name"], _DRUM_NAMES) for t in tracks):
            progress = 0.3
        elif active_phase == "bass" and any(_has_name_match(t["name"], _BASS_NAMES) for t in tracks):
            progress = 0.3
        elif active_phase == "harmony" and any(_has_name_match(t["name"], _HARMONY_NAMES) for t in tracks):
            progress = 0.3

    pending_steps = []
    if active_phase:
        hint_map = {
            "setup": ["set_tempo", "set_scale", "scaffold_arrangement"],
            "drums": ["create_midi_track (Drums)", "load_instrument_or_effect (Drum Rack)", "add_notes_to_clip (kick)"],
            "bass": ["create_midi_track (Bass)", "load_instrument_or_effect (Analog)", "add_notes_to_clip (bass line)"],
            "harmony": ["create_midi_track (Chords)", "load_instrument_or_effect (Wavetable)", "add_notes_to_clip (chords)"],
            "melody": ["create_midi_track (Lead)", "load_instrument_or_effect (Operator)", "add_notes_to_clip (melody)"],
            "sound_design": ["load_instrument_or_effect (Auto Filter)", "set_device_parameter (Frequency)"],
            "arrangement": ["get_arrangement_overview", "evaluate_session"],
            "mix": ["apply_mix_recipe", "check_gain_staging", "suggest_mix_adjustments"],
            "master": ["apply_master_recipe", "evaluate_session"],
        }
        pending_steps = hint_map.get(active_phase, [])

    resume_hint = _RESUME_HINTS.get(active_phase, _RESUME_HINTS[None])

    result = ProductionCheckpoint(
        genre=genre_id,
        completed_phases=completed,
        active_phase=active_phase,
        active_phase_progress=round(progress, 2),
        pending_steps=pending_steps,
        session_stats=stats,
        next_phase=next_phase,
        resume_hint=resume_hint,
    )
    _checkpoint_cache[cache_key] = {"result": result, "ts": now}
    return result


def invalidate_checkpoint_cache(genre: str = None):
    """Clear cached checkpoint for a genre, or all if genre is None."""
    if genre is None:
        _checkpoint_cache.clear()
    else:
        _checkpoint_cache.pop(genre, None)
