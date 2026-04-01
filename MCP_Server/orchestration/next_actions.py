"""Next-action recommender and phase transition gate."""

import logging
from MCP_Server.connection import get_ableton_connection
from MCP_Server.genres.catalog import resolve_alias
from MCP_Server.orchestration.agenda import AGENDA_CATALOG
from MCP_Server.orchestration.checkpoint import get_checkpoint, _infer_completed_phases, _build_session_stats
from MCP_Server.orchestration.execution import get_execution_plan
from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER

logger = logging.getLogger("AbletonMCPServer")

_EFFECT_CLASSES = {"AutoFilter", "Reverb", "Redux", "Saturator", "Chorus", "Flanger", "Phaser"}


def _phase_complete(phase_type: str, tracks: list, clips_by_track: dict,
                    master_devices: list) -> tuple:
    """Check if a phase is complete. Returns (is_complete: bool, blockers: list[str])."""
    def has_name(track_name, name_set):
        name_lower = track_name.lower()
        return any(n in name_lower for n in name_set)

    def track_has_clips(track_name):
        return len(clips_by_track.get(track_name, [])) > 0

    all_device_classes = set()
    for t in tracks:
        for d in t.get("devices", []):
            all_device_classes.add(d.get("class_name", ""))
    master_class_names = {d.get("class_name", "") for d in master_devices}

    if phase_type == "setup":
        if len(tracks) >= 2:
            return True, []
        return False, ["Session has fewer than 2 tracks — run scaffold_arrangement first"]

    elif phase_type == "drums":
        drum_tracks = [t for t in tracks if has_name(t["name"], _DRUM_NAMES)]
        if not drum_tracks:
            return False, ["No drum/kick track found — create a Drums track and load a Drum Rack"]
        t = drum_tracks[0]
        if not t.get("has_instrument"):
            return False, [f"Track '{t['name']}' has no instrument loaded — load a Drum Rack"]
        if not track_has_clips(t["name"]):
            return False, [f"Track '{t['name']}' has no clips — add drum notes with add_notes_to_clip"]
        return True, []

    elif phase_type == "bass":
        bass_tracks = [t for t in tracks if has_name(t["name"], _BASS_NAMES)]
        if not bass_tracks:
            return False, ["No bass track found — create a Bass track and load a bass instrument"]
        t = bass_tracks[0]
        if not t.get("has_instrument"):
            return False, [f"Track '{t['name']}' has no instrument — load Analog or Wavetable"]
        if not track_has_clips(t["name"]):
            return False, [f"Track '{t['name']}' has no clips — write a bass line with add_notes_to_clip"]
        return True, []

    elif phase_type == "harmony":
        harmony_tracks = [t for t in tracks if has_name(t["name"], _HARMONY_NAMES)]
        if not harmony_tracks:
            return False, ["No chord/pad track found — create a Chords track and load Wavetable"]
        t = harmony_tracks[0]
        if not track_has_clips(t["name"]):
            return False, [f"Track '{t['name']}' has no clips — add chord progression with add_notes_to_clip"]
        return True, []

    elif phase_type == "melody":
        melody_tracks = [t for t in tracks if has_name(t["name"], _MELODY_NAMES)]
        if not melody_tracks:
            return False, ["No lead/melody track found — create a Lead track and load Operator"]
        t = melody_tracks[0]
        if not track_has_clips(t["name"]):
            return False, [f"Track '{t['name']}' has no clips — write a melody with add_notes_to_clip"]
        return True, []

    elif phase_type == "sound_design":
        if all_device_classes & _EFFECT_CLASSES:
            return True, []
        return False, ["No effect devices found on any track — add Auto Filter or Reverb via load_instrument_or_effect"]

    elif phase_type == "arrangement":
        instrument_tracks = [t for t in tracks if t.get("has_instrument")]
        if len(instrument_tracks) < 2:
            return False, ["Fewer than 2 tracks have instruments — complete earlier phases first"]
        empty = [t["name"] for t in instrument_tracks if not track_has_clips(t["name"])]
        if empty:
            return False, [f"Tracks with no clips: {', '.join(empty)} — add arrangement clips"]
        return True, []

    elif phase_type == "mix":
        if _COMPRESSOR in all_device_classes:
            return True, []
        return False, ["No Compressor2 found on any track — call apply_mix_recipe for each track role"]

    elif phase_type == "master":
        if _GLUE_COMPRESSOR in master_class_names and _LIMITER in master_class_names:
            return True, []
        missing = []
        if _GLUE_COMPRESSOR not in master_class_names:
            missing.append("GlueCompressor")
        if _LIMITER not in master_class_names:
            missing.append("Limiter2")
        return False, [f"Master track missing: {', '.join(missing)} — call apply_master_recipe"]

    return False, [f"Unknown phase type: {phase_type}"]


def get_next_actions_result(genre: str, phase_name: str = None, n: int = 10) -> dict:
    """Return next N execution steps for the active (or specified) phase.

    If phase_name provided: returns full checklist for that phase (no connection needed).
    If only genre provided: reads checkpoint to determine active phase first.
    """
    n = max(1, min(n, 25))

    # Explicit phase — pure computation, no Ableton connection needed
    if phase_name:
        checklist = get_execution_plan(phase_name, genre)
        if "error" in checklist:
            return checklist
        steps = checklist["steps"][:n]
        return {
            "checkpoint_summary": f"Showing full {phase_name} checklist for {genre} (phase explicitly specified)",
            "active_phase": phase_name,
            "genre": genre,
            "steps": steps,
        }

    # No explicit phase — read checkpoint from live Ableton
    try:
        checkpoint = get_checkpoint(genre)
    except Exception as e:
        # Fallback: return setup checklist
        checklist = get_execution_plan("setup", genre)
        steps = checklist.get("steps", [])[:n] if "error" not in checklist else []
        return {
            "checkpoint_summary": f"No live session — showing full setup checklist for {genre}",
            "active_phase": "setup",
            "genre": genre,
            "steps": steps,
        }

    if "error" in checkpoint:
        checklist = get_execution_plan("setup", genre)
        steps = checklist.get("steps", [])[:n] if "error" not in checklist else []
        return {
            "checkpoint_summary": f"Could not read session ({checkpoint['error']}) — showing setup checklist",
            "active_phase": "setup",
            "genre": genre,
            "steps": steps,
        }

    active_phase = checkpoint.get("active_phase") or "setup"
    completed = checkpoint.get("completed_phases", [])
    genre_id = checkpoint.get("genre") or genre

    # Build summary
    if not completed:
        summary = f"{genre_id} production starting from scratch"
    elif active_phase is None:
        summary = f"{genre_id} production complete — ready for final review"
    else:
        completed_str = ", ".join(completed) if completed else "none"
        summary = f"{genre_id} production: {completed_str} complete, next up: {active_phase}"

    checklist = get_execution_plan(active_phase, genre_id)
    if "error" in checklist:
        return {"checkpoint_summary": summary, "active_phase": active_phase,
                "genre": genre_id, "steps": []}

    # Skip steps if phase already started (progress > 0.3) — return all for now (HIST-01 deferred)
    steps = checklist["steps"][:n]

    return {
        "checkpoint_summary": summary,
        "active_phase": active_phase,
        "genre": genre_id,
        "steps": steps,
    }


def get_transition_guidance(from_phase: str, genre: str = None, to_phase: str = None) -> dict:
    """Validate whether from_phase is complete and ready to advance.

    Reads live Ableton state. Returns go/no-go with blockers and fix hints.
    """
    # Resolve genre
    genre_id = None
    if genre:
        resolved = resolve_alias(genre)
        if resolved:
            genre_id = resolved["genre_id"]

    # Determine to_phase
    if not to_phase and genre_id and genre_id in AGENDA_CATALOG:
        phase_order = AGENDA_CATALOG[genre_id]
        if from_phase in phase_order:
            idx = phase_order.index(from_phase)
            to_phase = phase_order[idx + 1] if idx + 1 < len(phase_order) else None

    # Read Ableton state
    try:
        conn = get_ableton_connection()
        arrangement_state = conn.send_command("get_arrangement_state")
        mix_state = conn.send_command("get_mix_state")
    except Exception as e:
        return {"error": f"Could not connect to Ableton: {e}"}

    tracks = arrangement_state.get("tracks", [])
    master_devices = mix_state.get("master_track", {}).get("devices", [])

    # Fetch clips for all tracks
    clips_by_track = {}
    for track in tracks:
        try:
            result = conn.send_command("get_arrangement_clips",
                                       {"track_index": track.get("index", 0)})
            clips_by_track[track["name"]] = result.get("clips", [])
        except Exception:
            clips_by_track[track["name"]] = []

    is_complete, blockers = _phase_complete(from_phase, tracks, clips_by_track, master_devices)

    # Completion percentage estimate
    if is_complete:
        completion_pct = 1.0
    elif not tracks:
        completion_pct = 0.0
    else:
        # Rough heuristic: fraction of blockers resolved
        completion_pct = max(0.0, 1.0 - (len(blockers) * 0.3))

    # Fix hints from blockers
    fix_hints = []
    for blocker in blockers:
        if "no clips" in blocker.lower() or "no clip" in blocker.lower():
            fix_hints.append(f"Call get_phase_execution_plan('{from_phase}', '{genre_id or genre}') and execute the note-writing steps")
        elif "no instrument" in blocker.lower() or "no drum rack" in blocker.lower():
            fix_hints.append(f"Call get_phase_execution_plan('{from_phase}', '{genre_id or genre}') and execute the instrument-loading steps")
        elif "scaffold" in blocker.lower():
            fix_hints.append("Call scaffold_arrangement with a production plan first")
        elif "apply_mix_recipe" in blocker.lower():
            fix_hints.append(f"Call apply_mix_recipe for each track role, then check_gain_staging")
        elif "apply_master_recipe" in blocker.lower():
            fix_hints.append(f"Call apply_master_recipe(genre='{genre_id or genre}')")
        else:
            fix_hints.append(f"Call get_phase_execution_plan('{from_phase}', '{genre_id or genre}') to get detailed steps")

    return {
        "from_phase": from_phase,
        "to_phase": to_phase,
        "ready_to_advance": is_complete,
        "completion_pct": round(completion_pct, 2),
        "blockers": blockers,
        "fix_hints": fix_hints,
        "next_phase": to_phase,
    }
