"""Chord engine library: build, invert, voice, identify, and enumerate diatonic chords via music21."""

from MCP_Server.theory.pitch import _force_sharp, _format_note_name, _parse_note_name

# Lazy-loaded music21 modules (per D-20)
_harmony_module = None
_chord_module = None
_key_module = None
_roman_module = None
_pitch_module = None


def _get_harmony_module():
    """Lazy-import music21.harmony on first use."""
    global _harmony_module
    if _harmony_module is None:
        from music21 import harmony

        _harmony_module = harmony
    return _harmony_module


def _get_chord_module():
    """Lazy-import music21.chord on first use."""
    global _chord_module
    if _chord_module is None:
        from music21 import chord

        _chord_module = chord
    return _chord_module


def _get_key_module():
    """Lazy-import music21.key on first use."""
    global _key_module
    if _key_module is None:
        from music21 import key

        _key_module = key
    return _key_module


def _get_roman_module():
    """Lazy-import music21.roman on first use."""
    global _roman_module
    if _roman_module is None:
        from music21 import roman

        _roman_module = roman
    return _roman_module


def _get_pitch_module():
    """Lazy-import music21.pitch on first use."""
    global _pitch_module
    if _pitch_module is None:
        from music21 import pitch

        _pitch_module = pitch
    return _pitch_module


# Quality mapping: user-facing short symbols -> ChordSymbol notation (per D-02, research 1.1)
_QUALITY_MAP = {
    "maj": "",
    "min": "m",
    "dim": "dim",
    "aug": "aug",
    "maj7": "maj7",
    "min7": "m7",
    "dom7": "7",
    "7": "7",
    "dim7": "dim7",
    "hdim7": "m7b5",
    "min7b5": "m7b5",
    "sus2": "sus2",
    "sus4": "sus4",
    "add9": "add9",
    "9": "9",
    "min9": "m9",
    "maj9": "maj9",
    "11": "11",
    "min11": "m11",
    "13": "13",
    "min13": "m13",
    "7b5": "7b5",
    "7#5": "7#5",
    "7b9": "7b9",
    "7#9": "7#9",
    "7#11": "7#11",
}


def _make_note_obj(p):
    """Convert a music21 Pitch to a rich note object {"midi": int, "name": str}.

    Applies _force_sharp for consistent sharp-default spelling, then _format_note_name
    for unambiguous octave notation.
    """
    p = _force_sharp(p)
    return {"midi": p.midi, "name": _format_note_name(p)}


def _midi_to_pitch(midi_val):
    """Create a music21 Pitch from a MIDI number."""
    pitch_mod = _get_pitch_module()
    p = pitch_mod.Pitch(midi=midi_val)
    return _force_sharp(p)


def build_chord(root, quality, octave=4):
    """Build a chord from root note, quality symbol, and octave.

    Args:
        root: Root note name (e.g., "C", "F#", "Bb")
        quality: Chord quality short symbol (e.g., "maj", "min7", "dom7", "aug")
        octave: Target octave for the root (default 4, where C4 = MIDI 60)

    Returns:
        dict: {"root": str, "quality": str, "notes": [{"midi": int, "name": str}, ...]}

    Raises:
        ValueError: If root or quality is invalid
    """
    harmony = _get_harmony_module()

    # Map quality to ChordSymbol notation
    if quality in _QUALITY_MAP:
        cs_quality = _QUALITY_MAP[quality]
    else:
        cs_quality = quality  # Fallback: try raw quality

    # Build chord symbol
    symbol = root + cs_quality
    try:
        cs = harmony.ChordSymbol(symbol)
    except Exception:
        raise ValueError(f"Invalid chord: root='{root}', quality='{quality}' (symbol='{symbol}')")

    # Validate: ChordSymbol silently returns empty for truly invalid input
    pitches = list(cs.pitches)
    if not pitches:
        raise ValueError(f"Invalid chord: root='{root}', quality='{quality}' (no pitches produced)")

    # Check that root is valid by verifying the chord root matches expected
    try:
        chord_root = cs.root()
    except Exception:
        raise ValueError(f"Invalid root note: '{root}'")

    # Validate root letter matches what was requested
    requested_root = root.replace("#", "").replace("b", "").upper()
    actual_root = chord_root.name.replace("#", "").replace("-", "").replace("b", "").upper()
    if requested_root[0] != actual_root[0]:
        raise ValueError(f"Invalid chord: root='{root}', quality='{quality}'")

    # Transpose to target octave: place root at the requested octave.
    # ChordSymbol places roots at varying octaves; we shift so root lands at
    # the user's requested octave (e.g., octave=4 means root at C4/G4/A4).
    root_octave = chord_root.octave if chord_root.octave is not None else 3
    semitone_shift = (octave - root_octave) * 12

    notes = []
    for p in pitches:
        new_p = p.transpose(semitone_shift)
        notes.append(_make_note_obj(new_p))

    # Use music21's chord quality attribute for display
    quality_display = cs.quality if hasattr(cs, "quality") and cs.quality else quality

    # Root note: use the actual first note's root position from the transposed pitches
    root_transposed = chord_root.transpose(semitone_shift)
    root_note = _make_note_obj(root_transposed)

    return {
        "root": root_note["name"],
        "quality": quality_display,
        "notes": notes,
    }


def get_chord_inversions(root, quality, octave=4):
    """Get all inversions of a chord.

    Args:
        root: Root note name (e.g., "C", "F#")
        quality: Chord quality short symbol (e.g., "maj", "min7")
        octave: Target octave (default 4)

    Returns:
        list: [{"inversion": int, "bass_note": str, "notes": [note_obj, ...]}, ...]
    """
    base = build_chord(root, quality, octave)
    base_midis = [n["midi"] for n in base["notes"]]
    num_notes = len(base_midis)

    inversions = []
    current_midis = list(base_midis)

    for inv_num in range(num_notes):
        # Build note objects from current MIDI values
        notes = [_make_note_obj(_midi_to_pitch(m)) for m in current_midis]
        bass_note = notes[0]["name"]

        inversions.append({
            "inversion": inv_num,
            "bass_note": bass_note,
            "notes": notes,
        })

        # Prepare next inversion: move bottom note up an octave
        if inv_num < num_notes - 1:
            bottom = current_midis.pop(0)
            current_midis.append(bottom + 12)

    return inversions


def get_chord_voicings(root, quality, octave=4):
    """Get various voicings of a chord (close, open, drop-2, drop-3).

    Args:
        root: Root note name (e.g., "C", "F#")
        quality: Chord quality short symbol (e.g., "maj7", "min")
        octave: Target octave (default 4)

    Returns:
        dict: {"close": [...], "open": [...], "drop2": [...], "drop3": [...] | None}
    """
    base = build_chord(root, quality, octave)
    close_midis = [n["midi"] for n in base["notes"]]

    def midis_to_notes(midis):
        return [_make_note_obj(_midi_to_pitch(m)) for m in sorted(midis)]

    # Close voicing: default
    close_notes = midis_to_notes(close_midis)

    # Open voicing: drop every other note (index 1, 3, ...) by one octave
    open_midis = list(close_midis)
    for i in range(1, len(open_midis), 2):
        open_midis[i] -= 12
    open_notes = midis_to_notes(open_midis)

    # Drop-2: take 2nd from top, drop one octave (requires 3+ notes)
    if len(close_midis) >= 3:
        drop2_midis = list(close_midis)
        drop2_midis[-2] -= 12
        drop2_notes = midis_to_notes(drop2_midis)
    else:
        drop2_notes = close_notes  # Fallback for dyads

    # Drop-3: take 3rd from top, drop one octave (requires 4+ notes)
    if len(close_midis) >= 4:
        drop3_midis = list(close_midis)
        drop3_midis[-3] -= 12
        drop3_notes = midis_to_notes(drop3_midis)
    else:
        drop3_notes = None

    return {
        "close": close_notes,
        "open": open_notes,
        "drop2": drop2_notes,
        "drop3": drop3_notes,
    }


def identify_chord(midi_pitches):
    """Identify chord(s) from a set of MIDI pitch numbers.

    Returns up to 3 ranked candidates with root, quality, inversion, and confidence.

    Args:
        midi_pitches: List of MIDI pitch numbers (e.g., [60, 64, 67])

    Returns:
        list: [{"root": str, "quality": str, "name": str, "inversion": int,
                "bass_note": str, "confidence": float, "notes": [note_obj, ...]}, ...]
    """
    chord_mod = _get_chord_module()
    harmony = _get_harmony_module()

    sorted_pitches = sorted(midi_pitches)
    notes = [_make_note_obj(_midi_to_pitch(m)) for m in sorted_pitches]

    candidates = []
    seen = set()

    # Primary identification
    try:
        c = chord_mod.Chord(sorted_pitches)
        root_pitch = c.root()
        root_name = _format_note_name(_force_sharp(root_pitch))
        quality_str = c.quality if hasattr(c, "quality") else ""
        common_name = c.pitchedCommonName or ""
        inv = c.inversion() if c.inversion() is not None else 0
        bass_pitch = c.bass()
        bass_name = _format_note_name(_force_sharp(bass_pitch))

        # Confidence: root position highest, inversions slightly lower
        confidence = 1.0 - (inv * 0.05)

        candidate_key = (root_name, quality_str, inv)
        if candidate_key not in seen:
            seen.add(candidate_key)
            candidates.append({
                "root": _force_sharp(root_pitch).name,
                "quality": quality_str,
                "name": common_name,
                "inversion": inv,
                "bass_note": bass_name,
                "confidence": confidence,
                "notes": notes,
            })
    except Exception:
        pass

    # Alternative candidates: try each pitch as potential root
    pitch_mod = _get_pitch_module()
    for midi_val in sorted_pitches:
        try:
            potential_root = _force_sharp(pitch_mod.Pitch(midi=midi_val))

            # Build a chord with these pitches but suggest this root
            c2 = chord_mod.Chord(sorted_pitches)

            # Try to find enharmonic reinterpretation
            # Compute intervals from this potential root
            root_pc = midi_val % 12
            intervals = sorted(set((m % 12 - root_pc) % 12 for m in sorted_pitches))

            # Check if this forms a known chord pattern
            # Try building a ChordSymbol and compare pitch classes
            reinterpreted = False
            for qual_name, cs_suffix in _QUALITY_MAP.items():
                try:
                    test_sym = harmony.ChordSymbol(potential_root.name + cs_suffix)
                    test_pcs = sorted(set(p.midi % 12 for p in test_sym.pitches))
                    input_pcs = sorted(set(m % 12 for m in sorted_pitches))
                    if test_pcs == input_pcs:
                        # Found a match - determine inversion
                        bass_pc = sorted_pitches[0] % 12
                        root_pc_val = potential_root.midi % 12
                        # Determine inversion by bass note position in chord
                        chord_pcs = [p.midi % 12 for p in test_sym.pitches]
                        if bass_pc == root_pc_val:
                            inv_num = 0
                        elif bass_pc in chord_pcs:
                            inv_num = chord_pcs.index(bass_pc)
                        else:
                            inv_num = 0

                        confidence = 0.8 - (inv_num * 0.05)
                        if potential_root.name != (candidates[0]["root"] if candidates else ""):
                            confidence = min(confidence, 0.75)  # Reinterpretation penalty

                        cand_key = (potential_root.name, qual_name, inv_num)
                        if cand_key not in seen:
                            seen.add(cand_key)
                            bass_note = _make_note_obj(_midi_to_pitch(sorted_pitches[0]))

                            # Build quality display from common name
                            display_name = f"{potential_root.name}-{qual_name}"

                            candidates.append({
                                "root": potential_root.name,
                                "quality": qual_name,
                                "name": display_name,
                                "inversion": inv_num,
                                "bass_note": bass_note["name"],
                                "confidence": confidence,
                                "notes": notes,
                            })
                            reinterpreted = True
                except Exception:
                    continue
        except Exception:
            continue

    # Sort by confidence descending, return top 3
    candidates.sort(key=lambda x: x["confidence"], reverse=True)
    return candidates[:3]


def get_diatonic_chords(key_name, scale_type="major", octave=4):
    """Get all diatonic chords (triads and 7ths) for a key.

    Args:
        key_name: Key root (e.g., "C", "A", "F#")
        scale_type: "major", "minor", "harmonic_minor", or "melodic_minor"
        octave: Target octave (default 4)

    Returns:
        dict: {"key": str, "scale": str,
               "triads": [{"degree": int, "roman": str, "quality": str, "root": str,
                           "notes": [note_obj, ...]}, ...],
               "sevenths": [...]}

    Raises:
        ValueError: If scale_type is not one of the supported types
    """
    valid_types = ("major", "minor", "harmonic_minor", "melodic_minor")
    if scale_type not in valid_types:
        raise ValueError(f"Unsupported scale type: '{scale_type}'. Use one of: {', '.join(valid_types)}.")

    key_mod = _get_key_module()
    roman_mod = _get_roman_module()

    # For harmonic/melodic minor, use minor key as base for Roman numeral context
    if scale_type in ("harmonic_minor", "melodic_minor"):
        k = key_mod.Key(key_name, "minor")
    else:
        k = key_mod.Key(key_name, scale_type)

    # Determine the scale object for pitch generation (used in _build_diatonic_chord)
    scale_obj = None
    if scale_type == "harmonic_minor":
        from music21 import scale as scale_mod
        scale_obj = scale_mod.HarmonicMinorScale(key_name)
    elif scale_type == "melodic_minor":
        from music21 import scale as scale_mod
        scale_obj = scale_mod.MelodicMinorScale(key_name)

    # Roman numeral templates
    if scale_type == "major":
        triad_numerals = ["I", "ii", "iii", "IV", "V", "vi", "viio"]
        seventh_numerals = ["I7", "ii7", "iii7", "IV7", "V7", "vi7", "viio7"]
    elif scale_type == "minor":
        triad_numerals = ["i", "iio", "III", "iv", "v", "VI", "VII"]
        seventh_numerals = ["i7", "iio7", "III7", "iv7", "v7", "VI7", "VII7"]
    elif scale_type == "harmonic_minor":
        triad_numerals = ["i", "iio", "III+", "iv", "V", "VI", "viio"]
        seventh_numerals = ["i7", "iio7", "III+7", "iv7", "V7", "VI7", "viio7"]
    elif scale_type == "melodic_minor":
        triad_numerals = ["i", "ii", "III+", "IV", "V", "vio", "viio"]
        seventh_numerals = ["i7", "ii7", "III+7", "IV7", "V7", "vio7", "viio7"]

    def _build_diatonic_chord(numeral, degree_num):
        rn = roman_mod.RomanNumeral(numeral, k)
        pitches = list(rn.pitches)

        if not pitches:
            return None

        # Transpose to target octave
        root_pitch = rn.root()
        root_octave = root_pitch.octave if root_pitch.octave is not None else 4
        semitone_shift = (octave - root_octave) * 12

        # Adjust: keep chord degrees ascending within target octave range
        # For diatonic chords, the root of degree I should be at target octave
        # Other degrees should be relative to that
        # Calculate shift so degree 1 root lands at the target octave
        if degree_num == 1:
            shift = semitone_shift
        else:
            # Get the expected MIDI for this degree's root at the target octave
            scale_pitches = list(scale_obj.pitches) if scale_obj else list(k.getScale().pitches)
            # degree_num is 1-based, scale_pitches[0] is degree 1
            if degree_num - 1 < len(scale_pitches):
                scale_root = scale_pitches[degree_num - 1]
                scale_root_octave = scale_root.octave if scale_root.octave is not None else 4
                shift = (octave - scale_root_octave) * 12
            else:
                shift = semitone_shift

        note_objs = []
        for p in pitches:
            new_p = p.transpose(shift)
            note_objs.append(_make_note_obj(new_p))

        root_name = _force_sharp(root_pitch).name
        quality_str = rn.quality if hasattr(rn, "quality") else ""

        return {
            "degree": degree_num,
            "roman": numeral,
            "quality": quality_str,
            "root": root_name,
            "notes": note_objs,
        }

    triads = []
    for i, numeral in enumerate(triad_numerals):
        chord_dict = _build_diatonic_chord(numeral, i + 1)
        if chord_dict:
            triads.append(chord_dict)

    sevenths = []
    for i, numeral in enumerate(seventh_numerals):
        chord_dict = _build_diatonic_chord(numeral, i + 1)
        if chord_dict:
            sevenths.append(chord_dict)

    return {
        "key": key_name,
        "scale": scale_type,
        "triads": triads,
        "sevenths": sevenths,
    }
