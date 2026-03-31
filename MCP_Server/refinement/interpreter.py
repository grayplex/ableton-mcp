"""Refinement interpreter: map aesthetic instructions to SectionRefinementPlan.

Bridges the REFINEMENT_LEXICON to concrete per-track note operations and device
parameter targets. Does NOT apply any changes — returns a read-only plan only.
"""

from typing import Optional

from MCP_Server.refinement.lexicon import REFINEMENT_LEXICON, RefinementVector
from MCP_Server.refinement.schema import (
    DeviceChange,
    NoteOperation,
    SectionRefinementPlan,
    TrackRefinementEntry,
)

# ---------------------------------------------------------------------------
# Clamping bounds from D-07
# ---------------------------------------------------------------------------

_CLAMP = {
    "register_shift_semitones": (-12, 12),
    "filter_cutoff_delta_pct": (-80.0, 80.0),
    "brightness_db": (-12.0, 12.0),
    "velocity_shift": (-40, 40),
    "density_delta": (-2, 2),
    "reverb_wet_delta": (-0.5, 0.5),
    "compression_ratio_delta": (-0.5, 0.5),
}


def _clamp(value, lo, hi):
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Step 1: Normalize instruction text to matched lexicon keys
# ---------------------------------------------------------------------------


def _normalize_instruction(text: str) -> list[str]:
    """Extract matched REFINEMENT_LEXICON keys from instruction text."""
    text_lower = text.lower().replace("-", " ").replace(",", " ").strip()
    words = text_lower.split()
    matched = []
    i = 0
    while i < len(words):
        found = False
        for n in (3, 2, 1):
            if i + n <= len(words):
                candidate = "_".join(words[i:i + n])
                if candidate in REFINEMENT_LEXICON:
                    if candidate not in matched:
                        matched.append(candidate)
                    i += n
                    found = True
                    break
        if not found:
            i += 1
    return matched


# ---------------------------------------------------------------------------
# Step 2: Merge multiple RefinementVectors
# ---------------------------------------------------------------------------


def _merge_vectors(keys: list[str]) -> dict:
    """Sum deltas from each matched key's RefinementVector.

    None fields are skipped (not zero-summed). Results are clamped per D-07.
    Returns a merged vector as plain dict with harmonic/timbral/dynamic sub-dicts.
    """
    harmonic: dict = {}
    timbral: dict = {}
    dynamic: dict = {}

    for key in keys:
        vec = REFINEMENT_LEXICON[key]

        h = vec.get("harmonic")
        if h is not None:
            for field in ("register_shift_semitones", "density_delta"):
                v = h.get(field)
                if v is not None:
                    harmonic[field] = harmonic.get(field, 0) + v
            # mode_bias: last non-None wins (can't sum strings)
            mb = h.get("mode_bias")
            if mb is not None:
                harmonic["mode_bias"] = mb

        t = vec.get("timbral")
        if t is not None:
            for field in ("filter_cutoff_delta_pct", "brightness_db", "reverb_wet_delta"):
                v = t.get(field)
                if v is not None:
                    timbral[field] = timbral.get(field, 0.0) + v

        d = vec.get("dynamic")
        if d is not None:
            for field in ("velocity_shift",):
                v = d.get(field)
                if v is not None:
                    dynamic[field] = dynamic.get(field, 0) + v
            for field in ("compression_ratio_delta",):
                v = d.get(field)
                if v is not None:
                    dynamic[field] = dynamic.get(field, 0.0) + v

    # Apply clamping
    if "register_shift_semitones" in harmonic:
        lo, hi = _CLAMP["register_shift_semitones"]
        harmonic["register_shift_semitones"] = _clamp(harmonic["register_shift_semitones"], lo, hi)
    if "density_delta" in harmonic:
        lo, hi = _CLAMP["density_delta"]
        harmonic["density_delta"] = _clamp(harmonic["density_delta"], lo, hi)
    if "filter_cutoff_delta_pct" in timbral:
        lo, hi = _CLAMP["filter_cutoff_delta_pct"]
        timbral["filter_cutoff_delta_pct"] = _clamp(timbral["filter_cutoff_delta_pct"], lo, hi)
    if "brightness_db" in timbral:
        lo, hi = _CLAMP["brightness_db"]
        timbral["brightness_db"] = _clamp(timbral["brightness_db"], lo, hi)
    if "reverb_wet_delta" in timbral:
        lo, hi = _CLAMP["reverb_wet_delta"]
        timbral["reverb_wet_delta"] = _clamp(timbral["reverb_wet_delta"], lo, hi)
    if "velocity_shift" in dynamic:
        lo, hi = _CLAMP["velocity_shift"]
        dynamic["velocity_shift"] = _clamp(dynamic["velocity_shift"], lo, hi)
    if "compression_ratio_delta" in dynamic:
        lo, hi = _CLAMP["compression_ratio_delta"]
        dynamic["compression_ratio_delta"] = _clamp(dynamic["compression_ratio_delta"], lo, hi)

    result: dict = {}
    if harmonic:
        result["harmonic"] = harmonic
    if timbral:
        result["timbral"] = timbral
    if dynamic:
        result["dynamic"] = dynamic

    return result


# ---------------------------------------------------------------------------
# Step 3: Scale substitutions from mode bias (D-05)
# ---------------------------------------------------------------------------


def _scale_substitutions_from_mode_bias(mode_bias: Optional[str]) -> list:
    """Return parallel-mode pitch-class substitution list.

    - "minor": lower major 3rd (pc 4→3) and major 6th (pc 9→8)
    - "major": raise minor 3rd (pc 3→4) and minor 6th (pc 8→9)
    - None: empty list
    """
    if mode_bias == "minor":
        return [
            {"from_pitch_class": 4, "to_pitch_class": 3},
            {"from_pitch_class": 9, "to_pitch_class": 8},
        ]
    if mode_bias == "major":
        return [
            {"from_pitch_class": 3, "to_pitch_class": 4},
            {"from_pitch_class": 8, "to_pitch_class": 9},
        ]
    return []


# ---------------------------------------------------------------------------
# Step 4: Compute device changes from timbral/dynamic vectors (D-06)
# ---------------------------------------------------------------------------

# Maps (class_name, vector_field) → param_name for device target computation
_DEVICE_PARAM_MAP = {
    ("AutoFilter", "filter_cutoff_delta_pct"): "Frequency",
    ("Eq8", "brightness_db"): "Gain 4",
    ("Reverb", "reverb_wet_delta"): "Wet/Dry Mix",
    ("Compressor2", "compression_ratio_delta"): "Ratio",
}


def _compute_device_changes(
    track_devices: list,
    timbral: Optional[dict],
    dynamic: Optional[dict],
) -> list:
    """Build DeviceChange list from timbral and dynamic vector fields.

    For each relevant device class found in track_devices, compute target_normalized
    using the delta. Clamps target to [0.0, 1.0]. Skips if device not present.
    """
    changes: list[DeviceChange] = []

    # Build class_name → device lookup
    device_map = {}
    for dev in track_devices:
        cn = dev.get("class_name", "")
        if cn not in device_map:
            device_map[cn] = dev

    def _current_normalized(dev: dict, param_name: str) -> Optional[float]:
        """Find param value (normalized 0–1) from device dict."""
        # Devices from mix_state may have a "prominent_params" sub-dict or "parameters" list
        prominent = dev.get("prominent_params", {})
        if param_name in prominent:
            return float(prominent[param_name])
        for p in dev.get("parameters", []):
            if p.get("name") == param_name:
                return float(p.get("value", 0.5))
        return 0.5  # fallback: midpoint when param not visible

    # Timbral fields
    if timbral:
        for class_name, field in [
            ("AutoFilter", "filter_cutoff_delta_pct"),
            ("Eq8", "brightness_db"),
            ("Reverb", "reverb_wet_delta"),
        ]:
            delta = timbral.get(field)
            if delta is None or class_name not in device_map:
                continue
            dev = device_map[class_name]
            param_name = _DEVICE_PARAM_MAP[(class_name, field)]
            current = _current_normalized(dev, param_name)

            if field == "filter_cutoff_delta_pct":
                # Proportional: current * (1 + delta/100)
                target = current * (1 + delta / 100.0)
            else:
                # Additive normalized delta
                target = current + delta

            target = float(_clamp(target, 0.0, 1.0))
            changes.append({
                "device_name": dev.get("device_name", class_name),
                "class_name": class_name,
                "param_name": param_name,
                "current_normalized": round(current, 4),
                "target_normalized": round(target, 4),
                "reason": f"{field}={delta:+.2f} → {class_name}.{param_name}: {current:.3f}→{target:.3f}",
            })

    # Dynamic fields
    if dynamic:
        for class_name, field in [("Compressor2", "compression_ratio_delta")]:
            delta = dynamic.get(field)
            if delta is None or class_name not in device_map:
                continue
            dev = device_map[class_name]
            param_name = _DEVICE_PARAM_MAP[(class_name, field)]
            current = _current_normalized(dev, param_name)
            target = float(_clamp(current + delta, 0.0, 1.0))
            changes.append({
                "device_name": dev.get("device_name", class_name),
                "class_name": class_name,
                "param_name": param_name,
                "current_normalized": round(current, 4),
                "target_normalized": round(target, 4),
                "reason": f"{field}={delta:+.4f} → {class_name}.{param_name}: {current:.3f}→{target:.3f}",
            })

    return changes


# ---------------------------------------------------------------------------
# Main function: build_section_refinement_plan
# ---------------------------------------------------------------------------


def build_section_refinement_plan(
    section_name: str,
    instruction: str,
    conn,
) -> SectionRefinementPlan:
    """Build a read-only SectionRefinementPlan for a named section.

    Reads RS state directly (D-03: avoids double JSON serialization).
    Returns a plan with per-track NoteOperation + DeviceChange list.
    Does NOT apply any changes.

    Args:
        section_name: Named arrangement section (case-insensitive locator match)
        instruction: Aesthetic refinement instruction text
        conn: Ableton RS connection object (send_command interface)
    """
    # 1. Get arrangement state
    arrangement_state = conn.send_command("get_arrangement_state", {})
    cue_points = arrangement_state.get("cue_points", [])
    sig_num = arrangement_state.get("signature_numerator", 4)
    sig_den = arrangement_state.get("signature_denominator", 4)
    song_length = arrangement_state.get("song_length", 0.0)
    arrangement_tracks = arrangement_state.get("tracks", [])

    beats_per_bar = sig_num * (4.0 / sig_den)

    # 2. Resolve section bar range
    section_name_lower = section_name.lower()
    locator_index = None
    for i, cp in enumerate(cue_points):
        if cp.get("name", "").lower() == section_name_lower:
            locator_index = i
            break

    if locator_index is None:
        return {
            "section": section_name,
            "instruction": instruction,
            "vector": {},
            "tracks": [],
            "reasoning": [f"Section '{section_name}' not found in arrangement"],
        }

    section_start_beat = cue_points[locator_index]["time"]
    if locator_index + 1 < len(cue_points):
        section_end_beat = cue_points[locator_index + 1]["time"]
    else:
        section_end_beat = song_length

    # 3. Get mix state
    mix_state = conn.send_command("get_mix_state", {})

    # 4. Normalize instruction → matched lexicon keys
    matched_keys = _normalize_instruction(instruction)

    # 5. No signals → return empty plan
    if not matched_keys:
        return {
            "section": section_name,
            "instruction": instruction,
            "vector": {},
            "tracks": [],
            "reasoning": [f"No refinement signals found in: '{instruction}'"],
        }

    # 6. Merge vectors
    merged_vector = _merge_vectors(matched_keys)

    harmonic = merged_vector.get("harmonic", {})
    timbral = merged_vector.get("timbral") if merged_vector.get("timbral") else None
    dynamic = merged_vector.get("dynamic") if merged_vector.get("dynamic") else None

    semitone_shift = harmonic.get("register_shift_semitones", 0)
    density_delta = harmonic.get("density_delta", 0)
    mode_bias = harmonic.get("mode_bias", None)
    velocity_shift = dynamic.get("velocity_shift", 0) if dynamic else 0
    scale_subs = _scale_substitutions_from_mode_bias(mode_bias)

    # Build mix_state lookup by track name
    mix_tracks = {}
    for mt in mix_state.get("tracks", []):
        mix_tracks[mt.get("name", "")] = mt

    # 7. Process each track — collect those with clips in section range
    track_entries: list[TrackRefinementEntry] = []
    reasoning: list[str] = []

    for track_info in arrangement_tracks:
        track_index = track_info["index"]
        track_name = track_info["name"]

        clips_result = conn.send_command("get_arrangement_clips", {"track_index": track_index})
        all_clips = clips_result.get("clips", [])

        section_clips = [
            c for c in all_clips
            if section_start_beat <= c["start_time"] < section_end_beat
        ]

        if not section_clips:
            continue

        # 8. Build NoteOperation from harmonic vector
        note_op: NoteOperation = {
            "semitone_shift": semitone_shift,
            "density_delta": density_delta,
            "scale_substitutions": scale_subs,
            "velocity_shift": velocity_shift,
        }

        # Get track devices from mix state
        mix_track = mix_tracks.get(track_name, {})
        track_devices = mix_track.get("devices", [])

        # Compute DeviceChange list from timbral + dynamic
        device_changes = _compute_device_changes(track_devices, timbral, dynamic)

        entry: TrackRefinementEntry = {
            "track_name": track_name,
            "track_index": track_index,
            "note_operation": note_op,
            "device_changes": device_changes,
        }
        track_entries.append(entry)

        # 9. Append per-track reasoning
        filter_pct = timbral.get("filter_cutoff_delta_pct") if timbral else None
        filter_str = f", filter {filter_pct:+.0f}%" if filter_pct is not None else ""
        mode_str = f", mode→{mode_bias}" if mode_bias else ""
        reasoning.append(
            f"{track_name}: shift {semitone_shift:+d} semitones{mode_str}{filter_str}"
        )

    # 10. Return plan
    return {
        "section": section_name,
        "instruction": instruction,
        "vector": merged_vector,
        "tracks": track_entries,
        "reasoning": reasoning,
    }
