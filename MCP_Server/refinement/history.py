"""Session-scoped refinement history log.

Stores applied SectionRefinementPlan operations in-memory for the current
server session. Provides conflict and redundancy detection when a new
refinement is about to be applied to a section.

Conflict: two refinements push the same vector field in opposite directions
          (e.g., "darker" sets register_shift=-3, then "brighter" sets +3).
Redundancy: the identical instruction string has already been applied to the
            same section (e.g., "make it darker" applied twice).

History is keyed by lowercase section name. It is reset when the server
process restarts (session-scoped, not persistent).
"""

import time
from typing import Optional

# ---------------------------------------------------------------------------
# In-memory log: section_key -> list of applied operation entries.
# Each entry: {section, instruction, vector, tracks, timestamp}
# ---------------------------------------------------------------------------

_REFINEMENT_LOG: dict = {}

# Vector field groups used for conflict scanning
_HARMONIC_SIGNED_FIELDS = ("register_shift_semitones", "density_delta")
_TIMBRAL_SIGNED_FIELDS = ("filter_cutoff_delta_pct", "brightness_db", "reverb_wet_delta")
_DYNAMIC_SIGNED_FIELDS = ("velocity_shift", "compression_ratio_delta")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def record_refinement(section_name: str, instruction: str,
                      vector: dict, tracks: list,
                      snapshot: Optional[dict] = None) -> None:
    """Append a successfully applied refinement to the session log.

    Args:
        section_name: The arrangement section that was refined.
        instruction: The raw instruction string that was applied.
        vector: The merged RefinementVector dict from the plan.
        tracks: The list of TrackRefinementEntry dicts from the plan.
        snapshot: Optional pre-application state snapshot produced by
                  _build_apply_snapshot(). Used by revert_section_refinement
                  to restore the exact pre-refinement state.
    """
    key = section_name.lower()
    if key not in _REFINEMENT_LOG:
        _REFINEMENT_LOG[key] = []
    _REFINEMENT_LOG[key].append({
        "section": section_name,
        "instruction": instruction,
        "vector": vector,
        "tracks": [t["track_name"] for t in tracks],
        "snapshot": snapshot or {},
        "timestamp": time.time(),
    })


def get_history(section_name: Optional[str] = None) -> list:
    """Return the log of applied refinements for a section.

    Args:
        section_name: Section to query. Pass None to get all entries as a flat list.
    """
    if section_name is None:
        flat = []
        for entries in _REFINEMENT_LOG.values():
            flat.extend(entries)
        return flat
    return list(_REFINEMENT_LOG.get(section_name.lower(), []))


def clear_history(section_name: Optional[str] = None) -> None:
    """Clear refinement history.

    Args:
        section_name: Clear only this section's history. Pass None to clear all.
    """
    if section_name is None:
        _REFINEMENT_LOG.clear()
    else:
        _REFINEMENT_LOG.pop(section_name.lower(), None)


def pop_last_refinement(section_name: str) -> Optional[dict]:
    """Remove and return the most recent refinement entry for a section.

    Used by revert_section_refinement to retrieve the snapshot and unregister
    the reverted operation from the log.

    Returns None if no history exists for the section.
    """
    key = section_name.lower()
    entries = _REFINEMENT_LOG.get(key)
    if not entries:
        return None
    entry = entries.pop()
    if not entries:
        del _REFINEMENT_LOG[key]
    return entry


def detect_conflicts(section_name: str, new_vector: dict) -> list:
    """Detect conflicts between new_vector and previously applied vectors for section.

    A conflict occurs when the same vector field was previously pushed in one
    direction (positive/negative sign) and new_vector pushes it the other way.
    Mode bias conflicts are detected when previous and new mode_bias differ.

    Returns a list of conflict dicts:
        {field, previous_instruction, previous_value, new_value}
    Empty list when there are no conflicts or no history for the section.
    """
    history = get_history(section_name)
    if not history:
        return []

    conflicts = []

    new_harmonic = new_vector.get("harmonic") or {}
    new_timbral = new_vector.get("timbral") or {}
    new_dynamic = new_vector.get("dynamic") or {}

    for entry in history:
        prev_vector = entry.get("vector") or {}
        prev_instruction = entry["instruction"]

        prev_harmonic = prev_vector.get("harmonic") or {}
        prev_timbral = prev_vector.get("timbral") or {}
        prev_dynamic = prev_vector.get("dynamic") or {}

        # Signed numeric field conflicts (harmonic)
        for field in _HARMONIC_SIGNED_FIELDS:
            prev_val = prev_harmonic.get(field)
            new_val = new_harmonic.get(field)
            if (prev_val is not None and new_val is not None
                    and prev_val != 0 and new_val != 0
                    and (prev_val > 0) != (new_val > 0)):
                conflicts.append({
                    "field": field,
                    "previous_instruction": prev_instruction,
                    "previous_value": prev_val,
                    "new_value": new_val,
                })

        # Mode bias conflict (minor vs major)
        prev_mode = prev_harmonic.get("mode_bias")
        new_mode = new_harmonic.get("mode_bias")
        if prev_mode and new_mode and prev_mode != new_mode:
            conflicts.append({
                "field": "mode_bias",
                "previous_instruction": prev_instruction,
                "previous_value": prev_mode,
                "new_value": new_mode,
            })

        # Signed numeric field conflicts (timbral)
        for field in _TIMBRAL_SIGNED_FIELDS:
            prev_val = prev_timbral.get(field)
            new_val = new_timbral.get(field)
            if (prev_val is not None and new_val is not None
                    and prev_val != 0 and new_val != 0
                    and (prev_val > 0) != (new_val > 0)):
                conflicts.append({
                    "field": field,
                    "previous_instruction": prev_instruction,
                    "previous_value": prev_val,
                    "new_value": new_val,
                })

        # Signed numeric field conflicts (dynamic)
        for field in _DYNAMIC_SIGNED_FIELDS:
            prev_val = prev_dynamic.get(field)
            new_val = new_dynamic.get(field)
            if (prev_val is not None and new_val is not None
                    and prev_val != 0 and new_val != 0
                    and (prev_val > 0) != (new_val > 0)):
                conflicts.append({
                    "field": field,
                    "previous_instruction": prev_instruction,
                    "previous_value": prev_val,
                    "new_value": new_val,
                })

    return conflicts


def detect_redundancies(section_name: str, instruction: str) -> list:
    """Detect if the same instruction has already been applied to this section.

    Comparison is case-insensitive with leading/trailing whitespace stripped.

    Returns a list of redundancy dicts: {previous_instruction, timestamp}
    Empty list when no matching previous entry exists.
    """
    history = get_history(section_name)
    instruction_norm = instruction.lower().strip()
    return [
        {"previous_instruction": e["instruction"], "timestamp": e["timestamp"]}
        for e in history
        if e["instruction"].lower().strip() == instruction_norm
    ]
