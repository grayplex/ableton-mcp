"""Scale library: catalog of 38 scales, pitch generation, validation, relationships, and detection."""

from MCP_Server.theory.pitch import _force_sharp, _format_note_name, _parse_note_name, _get_pitch_module
from MCP_Server.theory.chords import _make_note_obj, _midi_to_pitch

# ---------------------------------------------------------------------------
# SCALE_CATALOG: 38 scales across 8 categories
# Each entry: intervals (semitone steps), category, music21_class (or None), aliases
# ---------------------------------------------------------------------------

SCALE_CATALOG = {
    # --- Diatonic (3) ---
    "major": {
        "intervals": [2, 2, 1, 2, 2, 2, 1],
        "category": "diatonic",
        "music21_class": "MajorScale",
        "aliases": ["ionian"],
    },
    "natural_minor": {
        "intervals": [2, 1, 2, 2, 1, 2, 2],
        "category": "diatonic",
        "music21_class": "MinorScale",
        "aliases": ["aeolian"],
    },
    "chromatic": {
        "intervals": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "category": "diatonic",
        "music21_class": "ChromaticScale",
        "aliases": [],
    },
    # --- Modal (7) ---
    "ionian": {
        "intervals": [2, 2, 1, 2, 2, 2, 1],
        "category": "modal",
        "music21_class": "MajorScale",
        "aliases": ["major"],
    },
    "dorian": {
        "intervals": [2, 1, 2, 2, 2, 1, 2],
        "category": "modal",
        "music21_class": "DorianScale",
        "aliases": [],
    },
    "phrygian": {
        "intervals": [1, 2, 2, 2, 1, 2, 2],
        "category": "modal",
        "music21_class": "PhrygianScale",
        "aliases": [],
    },
    "lydian": {
        "intervals": [2, 2, 2, 1, 2, 2, 1],
        "category": "modal",
        "music21_class": "LydianScale",
        "aliases": [],
    },
    "mixolydian": {
        "intervals": [2, 2, 1, 2, 2, 1, 2],
        "category": "modal",
        "music21_class": "MixolydianScale",
        "aliases": [],
    },
    "aeolian": {
        "intervals": [2, 1, 2, 2, 1, 2, 2],
        "category": "modal",
        "music21_class": "MinorScale",
        "aliases": ["natural_minor"],
    },
    "locrian": {
        "intervals": [1, 2, 2, 1, 2, 2, 2],
        "category": "modal",
        "music21_class": "LocrianScale",
        "aliases": [],
    },
    # --- Minor Variants (3) ---
    "harmonic_minor": {
        "intervals": [2, 1, 2, 2, 1, 3, 1],
        "category": "minor_variant",
        "music21_class": "HarmonicMinorScale",
        "aliases": [],
    },
    "melodic_minor": {
        "intervals": [2, 1, 2, 2, 2, 2, 1],
        "category": "minor_variant",
        "music21_class": "MelodicMinorScale",
        "aliases": [],
    },
    "dorian_b2": {
        "intervals": [1, 2, 2, 2, 2, 1, 2],
        "category": "minor_variant",
        "music21_class": None,
        "aliases": [],
    },
    # --- Pentatonic (4) ---
    "major_pentatonic": {
        "intervals": [2, 2, 3, 2, 3],
        "category": "pentatonic",
        "music21_class": None,
        "aliases": [],
    },
    "minor_pentatonic": {
        "intervals": [3, 2, 2, 3, 2],
        "category": "pentatonic",
        "music21_class": None,
        "aliases": [],
    },
    "japanese": {
        "intervals": [1, 4, 2, 1, 4],
        "category": "pentatonic",
        "music21_class": None,
        "aliases": [],
    },
    "egyptian": {
        "intervals": [2, 3, 2, 3, 2],
        "category": "pentatonic",
        "music21_class": None,
        "aliases": [],
    },
    # --- Blues (3) ---
    "blues": {
        "intervals": [3, 2, 1, 1, 3, 2],
        "category": "blues",
        "music21_class": None,
        "aliases": [],
    },
    "major_blues": {
        "intervals": [2, 1, 1, 3, 2, 3],
        "category": "blues",
        "music21_class": None,
        "aliases": [],
    },
    "blues_bebop": {
        "intervals": [3, 2, 1, 1, 1, 2, 2],
        "category": "blues",
        "music21_class": None,
        "aliases": [],
    },
    # --- Symmetric (4) ---
    "whole_tone": {
        "intervals": [2, 2, 2, 2, 2, 2],
        "category": "symmetric",
        "music21_class": "WholeToneScale",
        "aliases": [],
    },
    "diminished_whole_half": {
        "intervals": [2, 1, 2, 1, 2, 1, 2, 1],
        "category": "symmetric",
        "music21_class": None,
        "aliases": [],
    },
    "diminished_half_whole": {
        "intervals": [1, 2, 1, 2, 1, 2, 1, 2],
        "category": "symmetric",
        "music21_class": None,
        "aliases": [],
    },
    "augmented": {
        "intervals": [3, 1, 3, 1, 3, 1],
        "category": "symmetric",
        "music21_class": None,
        "aliases": [],
    },
    # --- Bebop (4) ---
    "bebop_dominant": {
        "intervals": [2, 2, 1, 2, 2, 1, 1, 1],
        "category": "bebop",
        "music21_class": None,
        "aliases": [],
    },
    "bebop_major": {
        "intervals": [2, 2, 1, 2, 1, 1, 2, 1],
        "category": "bebop",
        "music21_class": None,
        "aliases": [],
    },
    "bebop_dorian": {
        "intervals": [2, 1, 1, 1, 2, 2, 1, 2],
        "category": "bebop",
        "music21_class": None,
        "aliases": [],
    },
    "bebop_melodic_minor": {
        "intervals": [2, 1, 2, 2, 1, 1, 1, 2],
        "category": "bebop",
        "music21_class": None,
        "aliases": [],
    },
    # --- World/Other (10) ---
    "hungarian_minor": {
        "intervals": [2, 1, 3, 1, 1, 3, 1],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "persian": {
        "intervals": [1, 3, 1, 1, 2, 3, 1],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "arabic": {
        "intervals": [1, 3, 1, 2, 1, 3, 1],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "double_harmonic": {
        "intervals": [1, 3, 1, 2, 1, 3, 1],
        "category": "world",
        "music21_class": None,
        "aliases": ["arabic", "byzantine"],
    },
    "enigmatic": {
        "intervals": [1, 3, 2, 2, 2, 1, 1],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "neapolitan_major": {
        "intervals": [1, 2, 2, 2, 2, 2, 1],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "neapolitan_minor": {
        "intervals": [1, 2, 2, 2, 1, 3, 1],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "phrygian_dominant": {
        "intervals": [1, 3, 1, 2, 1, 2, 2],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "lydian_dominant": {
        "intervals": [2, 2, 2, 1, 2, 1, 2],
        "category": "world",
        "music21_class": None,
        "aliases": [],
    },
    "super_locrian": {
        "intervals": [1, 2, 1, 2, 2, 2, 2],
        "category": "world",
        "music21_class": None,
        "aliases": ["altered"],
    },
}

# Simplicity ranking for detection tiebreak (lower = simpler, preferred)
_SIMPLICITY_RANK = {
    "diatonic": 0,
    "modal": 1,
    "pentatonic": 2,
    "minor_variant": 3,
    "blues": 4,
    "symmetric": 5,
    "bebop": 6,
    "world": 7,
}

# Mode rotation map: maps parent scale to mode names (7-note diatonic modes)
_DIATONIC_MODE_NAMES = ["ionian", "dorian", "phrygian", "lydian", "mixolydian", "aeolian", "locrian"]

# Note names by pitch class (0=C, using sharps)
_PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _pc_name(pc):
    """Get note name for a pitch class integer (0-11), using sharp spelling."""
    return _PC_NAMES[pc % 12]


def _scale_pitch_classes(root_pc, intervals):
    """Generate the set of pitch classes for a scale given root pitch class and interval list."""
    pcs = set()
    current = root_pc
    pcs.add(current % 12)
    for step in intervals[:-1]:  # Don't add after last interval (wraps to root)
        current += step
        pcs.add(current % 12)
    return pcs


def list_scales():
    """Return the full catalog of available scales.

    Returns:
        list[dict]: Each entry has keys: name, intervals, category, note_count
    """
    result = []
    for name, info in SCALE_CATALOG.items():
        result.append({
            "name": name,
            "intervals": list(info["intervals"]),
            "category": info["category"],
            "note_count": len(info["intervals"]),
        })
    return result


def get_scale_pitches(root, scale_name, octave_start=4, octave_end=5):
    """Generate MIDI pitch note objects for a scale across an octave range.

    Args:
        root: Root note name (e.g., "C", "F#", "Bb")
        scale_name: Scale name from SCALE_CATALOG
        octave_start: Starting octave (default 4)
        octave_end: Ending octave (default 5). One octave of pitches generated
                    from octave_start, ending at octave_start+1.

    Returns:
        dict: {"root": str, "scale": str, "pitches": [{"midi": int, "name": str}, ...]}

    Raises:
        ValueError: If scale_name not in catalog
    """
    if scale_name not in SCALE_CATALOG:
        raise ValueError(f"Unknown scale: '{scale_name}'. Use list_scales() to see available scales.")

    intervals = SCALE_CATALOG[scale_name]["intervals"]
    pitch_mod = _get_pitch_module()

    # Parse root at octave_start
    root_pitch = _parse_note_name(root + str(octave_start))
    root_midi = root_pitch.midi

    # Build pitches by accumulating intervals for one octave (including top note)
    pitches = []
    current_midi = root_midi
    pitches.append(_make_note_obj(_force_sharp(pitch_mod.Pitch(midi=current_midi))))

    for step in intervals:
        current_midi += step
        pitches.append(_make_note_obj(_force_sharp(pitch_mod.Pitch(midi=current_midi))))

    return {
        "root": root,
        "scale": scale_name,
        "pitches": pitches,
    }


def check_notes_in_scale(midi_pitches, root, scale_name):
    """Check which MIDI pitches belong to a given scale.

    Args:
        midi_pitches: List of MIDI pitch numbers
        root: Root note name (e.g., "C")
        scale_name: Scale name from SCALE_CATALOG

    Returns:
        dict: {"scale": str, "root": str, "in_scale": [note_obj], "out_of_scale": [note_obj], "all_in_scale": bool}
    """
    if scale_name not in SCALE_CATALOG:
        raise ValueError(f"Unknown scale: '{scale_name}'.")

    intervals = SCALE_CATALOG[scale_name]["intervals"]

    # Get root pitch class
    root_pitch = _parse_note_name(root + "4")
    root_pc = root_pitch.midi % 12

    # Build scale pitch class set
    scale_pcs = _scale_pitch_classes(root_pc, intervals)

    in_scale = []
    out_of_scale = []

    for midi in midi_pitches:
        note_obj = _make_note_obj(_midi_to_pitch(midi))
        if midi % 12 in scale_pcs:
            in_scale.append(note_obj)
        else:
            out_of_scale.append(note_obj)

    return {
        "scale": scale_name,
        "root": root,
        "in_scale": in_scale,
        "out_of_scale": out_of_scale,
        "all_in_scale": len(out_of_scale) == 0,
    }


def get_related_scales(root, scale_name):
    """Find related scales: parallel (same root), relative (same key sig), and modes.

    Args:
        root: Root note name (e.g., "C")
        scale_name: Scale name from SCALE_CATALOG

    Returns:
        dict: {"parallel": [...], "relative": [...], "modes": [...]}
    """
    if scale_name not in SCALE_CATALOG:
        raise ValueError(f"Unknown scale: '{scale_name}'.")

    root_pitch = _parse_note_name(root + "4")
    root_pc = root_pitch.midi % 12

    # --- Parallel scales: same root, different scale types ---
    parallel_candidates = [
        "major", "natural_minor", "harmonic_minor", "melodic_minor",
        "dorian", "mixolydian", "lydian", "phrygian", "locrian",
    ]
    parallel = []
    for candidate in parallel_candidates:
        if candidate != scale_name and candidate in SCALE_CATALOG:
            parallel.append({"root": root, "scale": candidate})

    # --- Relative scales ---
    relative = []
    # Resolve the canonical name for comparison
    canonical = scale_name
    if scale_name in ("major", "ionian"):
        # Relative minor: root - 3 semitones
        rel_pc = (root_pc - 3) % 12
        rel_name = _pc_name(rel_pc)
        relative.append({"root": rel_name, "scale": "natural_minor"})
    elif scale_name in ("natural_minor", "aeolian"):
        # Relative major: root + 3 semitones
        rel_pc = (root_pc + 3) % 12
        rel_name = _pc_name(rel_pc)
        relative.append({"root": rel_name, "scale": "major"})

    # --- Modes: rotate interval pattern for 7-note diatonic scales ---
    modes = []
    intervals = SCALE_CATALOG[scale_name]["intervals"]

    # Only compute modes for 7-note diatonic-family scales
    if len(intervals) == 7 and scale_name in ("major", "ionian", "natural_minor", "aeolian",
                                                "dorian", "phrygian", "lydian", "mixolydian", "locrian"):
        # Determine which mode position the input scale occupies
        major_intervals = SCALE_CATALOG["major"]["intervals"]

        # Find the mode index of the current scale
        mode_idx = None
        for i in range(7):
            rotated = major_intervals[i:] + major_intervals[:i]
            if rotated == intervals:
                mode_idx = i
                break

        if mode_idx is not None:
            # Generate all 7 modes from the parent major scale
            # The parent major root is: current_root - sum(intervals[:mode_idx]) semitones
            parent_root_pc = root_pc
            for step in intervals[:mode_idx]:
                parent_root_pc -= step
            parent_root_pc = parent_root_pc % 12

            # Now generate each mode
            current_pc = parent_root_pc
            for i in range(7):
                mode_root = _pc_name(current_pc)
                mode_name = _DIATONIC_MODE_NAMES[i]
                modes.append({"root": mode_root, "scale": mode_name})
                current_pc = (current_pc + major_intervals[i]) % 12

    return {
        "parallel": parallel,
        "relative": relative,
        "modes": modes,
    }


def detect_scales_from_notes(midi_pitches):
    """Detect which scales best match a set of MIDI pitches.

    Args:
        midi_pitches: List of MIDI pitch numbers

    Returns:
        list[dict]: Top 5 candidates, each with root, scale, coverage, matched_notes, total_notes

    Raises:
        ValueError: If midi_pitches is empty
    """
    if not midi_pitches:
        raise ValueError("midi_pitches must not be empty.")

    input_pcs = set(m % 12 for m in midi_pitches)
    total = len(input_pcs)

    candidates = []

    for scale_name, info in SCALE_CATALOG.items():
        intervals = info["intervals"]
        category = info["category"]
        simplicity = _SIMPLICITY_RANK.get(category, 99)

        for root_pc in range(12):
            scale_pcs = _scale_pitch_classes(root_pc, intervals)
            matched = input_pcs & scale_pcs
            coverage = len(matched) / total

            if coverage > 0:
                candidates.append({
                    "root": _pc_name(root_pc),
                    "scale": scale_name,
                    "coverage": round(coverage, 4),
                    "matched_notes": len(matched),
                    "total_notes": total,
                    "_simplicity": simplicity,
                })

    # Sort by coverage descending, then simplicity ascending
    candidates.sort(key=lambda x: (-x["coverage"], x["_simplicity"]))

    # Remove internal sort key and return top 5
    result = []
    for c in candidates[:5]:
        result.append({
            "root": c["root"],
            "scale": c["scale"],
            "coverage": c["coverage"],
            "matched_notes": c["matched_notes"],
            "total_notes": c["total_notes"],
        })

    return result
