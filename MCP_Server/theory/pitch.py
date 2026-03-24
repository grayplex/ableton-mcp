"""Pitch mapping utilities: bidirectional MIDI number <-> note name conversion via music21."""

import re

_pitch_module = None


def _get_pitch_module():
    """Lazy-import music21.pitch on first use (per D-14 -- keeps server startup fast)."""
    global _pitch_module
    if _pitch_module is None:
        from music21 import pitch

        _pitch_module = pitch
    return _pitch_module


def _force_sharp(p):
    """If pitch has a flat accidental, return the sharp enharmonic equivalent.

    Ensures sharps-default behavior (per D-12) since music21 prefers Eb/Bb over D#/A#.
    """
    if p.accidental is not None and p.accidental.alter < 0:
        return p.getEnharmonic()
    return p


def _format_note_name(p) -> str:
    """Format pitch as unambiguous note name string.

    Handles negative octaves where music21's nameWithOctave is ambiguous
    (e.g., 'C-1' could be parsed as C-flat in octave 1). Uses parenthesized
    negative octaves: 'C(-1)' for clarity.
    """
    if p.octave is not None and p.octave < 0:
        return f"{p.name}({p.octave})"
    return p.nameWithOctave


# Regex for parsing note names with optional parenthesized negative octaves
_NOTE_RE = re.compile(
    r"^([A-Ga-g])"           # pitch letter
    r"([#\-b]*)"             # accidentals (sharp, flat)
    r"\(?(-?\d+)\)?$"        # octave (possibly negative, possibly in parens)
)


def _parse_note_name(note_name: str):
    """Parse a note name string into a music21 Pitch, handling negative octaves.

    Accepts formats: 'C4', 'C#4', 'Eb3', 'C(-1)', 'C#(-1)', 'C-1' (ambiguous
    but handled: hyphen before digit at end is treated as negative octave sign
    only when it follows the pitch letter directly with no other accidentals).
    """
    pitch_mod = _get_pitch_module()

    m = _NOTE_RE.match(note_name.strip())
    if m:
        letter = m.group(1).upper()
        acc_str = m.group(2)
        octave = int(m.group(3))

        # Build pitch from components to avoid music21 parsing ambiguity
        p = pitch_mod.Pitch()
        p.step = letter
        if acc_str:
            # Convert accidental string: # -> sharp, - or b -> flat
            acc_cleaned = acc_str.replace("b", "-")
            p.accidental = pitch_mod.Accidental(acc_cleaned)
        p.octave = octave
        return p

    # Fallback: let music21 parse directly (handles unusual formats)
    return pitch_mod.Pitch(note_name)


def midi_to_note(midi_number: int, key_context: str | None = None) -> dict:
    """Convert MIDI number to note info dict.

    Args:
        midi_number: MIDI pitch number (any integer accepted at library level per D-16)
        key_context: Optional key for enharmonic spelling (e.g., "Ab major").
                     Without key context, defaults to sharps (per D-12).

    Returns:
        dict with keys: midi (int), name (str), octave (int), pitch_class (str)
    """
    pitch_mod = _get_pitch_module()
    p = pitch_mod.Pitch(midi=midi_number)

    if key_context is not None:
        from music21 import key as key_module

        # Accept formats like "Ab major", "C# minor", or just "Ab", "c"
        parts = key_context.strip().split()
        if len(parts) == 2:
            k = key_module.Key(parts[0], parts[1])
        else:
            k = key_module.Key(parts[0])

        # Build a pitch-class-to-name lookup from the key's scale
        scale_spelling = {}
        for sp in k.getScale().pitches:
            scale_spelling[sp.midi % 12] = sp.name

        pc = midi_number % 12
        if pc in scale_spelling:
            # Use the scale's spelling for this pitch class
            p = pitch_mod.Pitch(scale_spelling[pc])
            p.octave = (midi_number - pc) // 12 - 1  # MIDI octave formula
        else:
            # Pitch not in key scale — use simplifyEnharmonic default
            p = p.simplifyEnharmonic()
    else:
        # Default: sharps for black keys (per D-12)
        # music21 prefers Eb/Bb by convention; force sharps instead
        p = _force_sharp(p)

    return {
        "midi": midi_number,
        "name": _format_note_name(p),
        "octave": p.octave,
        "pitch_class": p.name,
    }


def note_to_midi(note_name: str) -> dict:
    """Convert note name to MIDI info dict.

    Args:
        note_name: Note name with octave (e.g., "C4", "Eb3", "F#5")

    Returns:
        dict with keys: name (str), midi (int)
    """
    p = _parse_note_name(note_name)

    return {
        "name": _format_note_name(p),
        "midi": p.midi,
    }
