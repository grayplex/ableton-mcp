"""Rhythm pattern library: pattern catalog and chord-tone-to-MIDI applicator."""

# ---------------------------------------------------------------------------
# RHYTHM_CATALOG: ~18 patterns across 4 categories (per D-05, D-06, D-07)
# Each step uses chord tone references (root, 3rd, 5th, 7th, octave) + beat
# position + duration + velocity. All patterns assume 4/4 time.
# ---------------------------------------------------------------------------

RHYTHM_CATALOG = [
    # ===== ARPEGGIOS (5) =====
    {
        "name": "arpeggio_up",
        "category": "arpeggio",
        "style": "basic",
        "description": "Ascending arpeggio through chord tones in 8th notes",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 100},
            {"tone": "3rd", "beat": 0.5, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 1.0, "duration": 0.5, "velocity": 85},
            {"tone": "octave", "beat": 1.5, "duration": 0.5, "velocity": 80},
            {"tone": "root", "beat": 2.0, "duration": 0.5, "velocity": 100},
            {"tone": "3rd", "beat": 2.5, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 3.0, "duration": 0.5, "velocity": 85},
            {"tone": "octave", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "arpeggio_down",
        "category": "arpeggio",
        "style": "basic",
        "description": "Descending arpeggio through chord tones in 8th notes",
        "time_signature": "4/4",
        "steps": [
            {"tone": "octave", "beat": 0.0, "duration": 0.5, "velocity": 100},
            {"tone": "5th", "beat": 0.5, "duration": 0.5, "velocity": 90},
            {"tone": "3rd", "beat": 1.0, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 1.5, "duration": 0.5, "velocity": 80},
            {"tone": "octave", "beat": 2.0, "duration": 0.5, "velocity": 100},
            {"tone": "5th", "beat": 2.5, "duration": 0.5, "velocity": 90},
            {"tone": "3rd", "beat": 3.0, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "arpeggio_alternating",
        "category": "arpeggio",
        "style": "basic",
        "description": "Ascending then descending arpeggio pattern",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 100},
            {"tone": "3rd", "beat": 0.5, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 1.0, "duration": 0.5, "velocity": 85},
            {"tone": "octave", "beat": 1.5, "duration": 0.5, "velocity": 95},
            {"tone": "5th", "beat": 2.0, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 2.5, "duration": 0.5, "velocity": 80},
            {"tone": "root", "beat": 3.0, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "arpeggio_broken",
        "category": "arpeggio",
        "style": "basic",
        "description": "Broken arpeggio: root-5th-3rd-octave pattern",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 100},
            {"tone": "5th", "beat": 0.5, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 1.0, "duration": 0.5, "velocity": 90},
            {"tone": "octave", "beat": 1.5, "duration": 0.5, "velocity": 80},
            {"tone": "root", "beat": 2.0, "duration": 0.5, "velocity": 100},
            {"tone": "5th", "beat": 2.5, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 3.0, "duration": 0.5, "velocity": 90},
            {"tone": "octave", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "arpeggio_jazz",
        "category": "arpeggio",
        "style": "jazz",
        "description": "Jazz arpeggio with 7th extension in swing-friendly rhythm",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.75, "velocity": 95},
            {"tone": "3rd", "beat": 0.75, "duration": 0.25, "velocity": 80},
            {"tone": "5th", "beat": 1.0, "duration": 0.75, "velocity": 90},
            {"tone": "7th", "beat": 1.75, "duration": 0.25, "velocity": 80},
            {"tone": "octave", "beat": 2.0, "duration": 0.75, "velocity": 95},
            {"tone": "7th", "beat": 2.75, "duration": 0.25, "velocity": 80},
            {"tone": "5th", "beat": 3.0, "duration": 0.75, "velocity": 90},
            {"tone": "3rd", "beat": 3.75, "duration": 0.25, "velocity": 80},
        ],
    },
    # ===== BASS LINES (4) =====
    {
        "name": "bass_root_fifth",
        "category": "bass",
        "style": "basic",
        "description": "Root on beat 1, fifth on beat 3 (quarter notes)",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 2.0, "velocity": 100},
            {"tone": "5th", "beat": 2.0, "duration": 2.0, "velocity": 90},
        ],
    },
    {
        "name": "bass_walking",
        "category": "bass",
        "style": "jazz",
        "description": "Walking bass line through chord tones in quarter notes",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 1.0, "velocity": 100},
            {"tone": "3rd", "beat": 1.0, "duration": 1.0, "velocity": 90},
            {"tone": "5th", "beat": 2.0, "duration": 1.0, "velocity": 95},
            {"tone": "octave", "beat": 3.0, "duration": 1.0, "velocity": 85},
        ],
    },
    {
        "name": "bass_octave",
        "category": "bass",
        "style": "rock",
        "description": "Root and octave alternating in 8th notes",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 100},
            {"tone": "octave", "beat": 0.5, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 1.0, "duration": 0.5, "velocity": 100},
            {"tone": "octave", "beat": 1.5, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 2.0, "duration": 0.5, "velocity": 100},
            {"tone": "octave", "beat": 2.5, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 3.0, "duration": 0.5, "velocity": 100},
            {"tone": "octave", "beat": 3.5, "duration": 0.5, "velocity": 85},
        ],
    },
    {
        "name": "bass_pop",
        "category": "bass",
        "style": "pop",
        "description": "Pop bass: root-root-5th-root pattern in 8th notes",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 1.0, "velocity": 100},
            {"tone": "root", "beat": 1.0, "duration": 0.5, "velocity": 85},
            {"tone": "5th", "beat": 1.5, "duration": 0.5, "velocity": 80},
            {"tone": "root", "beat": 2.0, "duration": 1.0, "velocity": 95},
            {"tone": "root", "beat": 3.0, "duration": 0.5, "velocity": 85},
            {"tone": "5th", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    # ===== COMPING (4) =====
    {
        "name": "comping_block",
        "category": "comping",
        "style": "basic",
        "description": "Block chords on beats 1 and 3 (half notes)",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 2.0, "velocity": 90},
            {"tone": "3rd", "beat": 0.0, "duration": 2.0, "velocity": 85},
            {"tone": "5th", "beat": 0.0, "duration": 2.0, "velocity": 85},
            {"tone": "root", "beat": 2.0, "duration": 2.0, "velocity": 85},
            {"tone": "3rd", "beat": 2.0, "duration": 2.0, "velocity": 80},
            {"tone": "5th", "beat": 2.0, "duration": 2.0, "velocity": 80},
        ],
    },
    {
        "name": "comping_syncopated",
        "category": "comping",
        "style": "jazz",
        "description": "Syncopated chord hits on beat 1, and-of-2, and beat 4",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 95},
            {"tone": "3rd", "beat": 0.0, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 0.0, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 1.5, "duration": 0.5, "velocity": 90},
            {"tone": "3rd", "beat": 1.5, "duration": 0.5, "velocity": 85},
            {"tone": "5th", "beat": 1.5, "duration": 0.5, "velocity": 80},
            {"tone": "root", "beat": 3.0, "duration": 1.0, "velocity": 95},
            {"tone": "3rd", "beat": 3.0, "duration": 1.0, "velocity": 90},
            {"tone": "5th", "beat": 3.0, "duration": 1.0, "velocity": 85},
        ],
    },
    {
        "name": "comping_quarter",
        "category": "comping",
        "style": "pop",
        "description": "All chord tones on every beat (quarter notes)",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 1.0, "velocity": 95},
            {"tone": "3rd", "beat": 0.0, "duration": 1.0, "velocity": 90},
            {"tone": "5th", "beat": 0.0, "duration": 1.0, "velocity": 85},
            {"tone": "root", "beat": 1.0, "duration": 1.0, "velocity": 85},
            {"tone": "3rd", "beat": 1.0, "duration": 1.0, "velocity": 80},
            {"tone": "5th", "beat": 1.0, "duration": 1.0, "velocity": 80},
            {"tone": "root", "beat": 2.0, "duration": 1.0, "velocity": 90},
            {"tone": "3rd", "beat": 2.0, "duration": 1.0, "velocity": 85},
            {"tone": "5th", "beat": 2.0, "duration": 1.0, "velocity": 85},
            {"tone": "root", "beat": 3.0, "duration": 1.0, "velocity": 85},
            {"tone": "3rd", "beat": 3.0, "duration": 1.0, "velocity": 80},
            {"tone": "5th", "beat": 3.0, "duration": 1.0, "velocity": 80},
        ],
    },
    {
        "name": "comping_reggae",
        "category": "comping",
        "style": "pop",
        "description": "Reggae-style offbeat chord stabs",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.5, "duration": 0.5, "velocity": 90},
            {"tone": "3rd", "beat": 0.5, "duration": 0.5, "velocity": 85},
            {"tone": "5th", "beat": 0.5, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 1.5, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 1.5, "duration": 0.5, "velocity": 80},
            {"tone": "5th", "beat": 1.5, "duration": 0.5, "velocity": 80},
            {"tone": "root", "beat": 2.5, "duration": 0.5, "velocity": 90},
            {"tone": "3rd", "beat": 2.5, "duration": 0.5, "velocity": 85},
            {"tone": "5th", "beat": 2.5, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 3.5, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 3.5, "duration": 0.5, "velocity": 80},
            {"tone": "5th", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    # ===== STRUMMING (5) =====
    {
        "name": "strumming_down",
        "category": "strumming",
        "style": "basic",
        "description": "Down strums on each beat: all tones as 8th notes",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 100},
            {"tone": "3rd", "beat": 0.0, "duration": 0.5, "velocity": 95},
            {"tone": "5th", "beat": 0.0, "duration": 0.5, "velocity": 90},
            {"tone": "octave", "beat": 0.0, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 1.0, "duration": 0.5, "velocity": 95},
            {"tone": "3rd", "beat": 1.0, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 1.0, "duration": 0.5, "velocity": 85},
            {"tone": "octave", "beat": 1.0, "duration": 0.5, "velocity": 80},
            {"tone": "root", "beat": 2.0, "duration": 0.5, "velocity": 100},
            {"tone": "3rd", "beat": 2.0, "duration": 0.5, "velocity": 95},
            {"tone": "5th", "beat": 2.0, "duration": 0.5, "velocity": 90},
            {"tone": "octave", "beat": 2.0, "duration": 0.5, "velocity": 85},
            {"tone": "root", "beat": 3.0, "duration": 0.5, "velocity": 95},
            {"tone": "3rd", "beat": 3.0, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 3.0, "duration": 0.5, "velocity": 85},
            {"tone": "octave", "beat": 3.0, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "strumming_up_down",
        "category": "strumming",
        "style": "basic",
        "description": "Alternating root-only and full chord strums",
        "time_signature": "4/4",
        "steps": [
            # Down (full chord)
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 100},
            {"tone": "3rd", "beat": 0.0, "duration": 0.5, "velocity": 95},
            {"tone": "5th", "beat": 0.0, "duration": 0.5, "velocity": 90},
            # Up (root only)
            {"tone": "root", "beat": 0.5, "duration": 0.5, "velocity": 80},
            # Down (full chord)
            {"tone": "root", "beat": 1.0, "duration": 0.5, "velocity": 95},
            {"tone": "3rd", "beat": 1.0, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 1.0, "duration": 0.5, "velocity": 85},
            # Up (root only)
            {"tone": "root", "beat": 1.5, "duration": 0.5, "velocity": 80},
            # Down (full chord)
            {"tone": "root", "beat": 2.0, "duration": 0.5, "velocity": 100},
            {"tone": "3rd", "beat": 2.0, "duration": 0.5, "velocity": 95},
            {"tone": "5th", "beat": 2.0, "duration": 0.5, "velocity": 90},
            # Up (root only)
            {"tone": "root", "beat": 2.5, "duration": 0.5, "velocity": 80},
            # Down (full chord)
            {"tone": "root", "beat": 3.0, "duration": 0.5, "velocity": 95},
            {"tone": "3rd", "beat": 3.0, "duration": 0.5, "velocity": 90},
            {"tone": "5th", "beat": 3.0, "duration": 0.5, "velocity": 85},
            # Up (root only)
            {"tone": "root", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "strumming_folk",
        "category": "strumming",
        "style": "basic",
        "description": "Folk pattern: bass on 1-3, full chord on 2-4",
        "time_signature": "4/4",
        "steps": [
            # Beat 1: bass note
            {"tone": "root", "beat": 0.0, "duration": 1.0, "velocity": 100},
            # Beat 2: full chord
            {"tone": "root", "beat": 1.0, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 1.0, "duration": 0.5, "velocity": 85},
            {"tone": "5th", "beat": 1.0, "duration": 0.5, "velocity": 85},
            # Beat 3: bass note (5th)
            {"tone": "5th", "beat": 2.0, "duration": 1.0, "velocity": 95},
            # Beat 4: full chord
            {"tone": "root", "beat": 3.0, "duration": 0.5, "velocity": 80},
            {"tone": "3rd", "beat": 3.0, "duration": 0.5, "velocity": 80},
            {"tone": "5th", "beat": 3.0, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "strumming_rock",
        "category": "strumming",
        "style": "rock",
        "description": "Rock power strum: root+5th emphasis with full chords",
        "time_signature": "4/4",
        "steps": [
            # Beat 1: power (root+5th)
            {"tone": "root", "beat": 0.0, "duration": 0.5, "velocity": 110},
            {"tone": "5th", "beat": 0.0, "duration": 0.5, "velocity": 105},
            # And of 1: full chord
            {"tone": "root", "beat": 0.5, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 0.5, "duration": 0.5, "velocity": 80},
            {"tone": "5th", "beat": 0.5, "duration": 0.5, "velocity": 80},
            # Beat 2: rest (no notes)
            # And of 2: power
            {"tone": "root", "beat": 1.5, "duration": 0.5, "velocity": 100},
            {"tone": "5th", "beat": 1.5, "duration": 0.5, "velocity": 95},
            # Beat 3: power (root+5th)
            {"tone": "root", "beat": 2.0, "duration": 0.5, "velocity": 110},
            {"tone": "5th", "beat": 2.0, "duration": 0.5, "velocity": 105},
            # And of 3: full chord
            {"tone": "root", "beat": 2.5, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 2.5, "duration": 0.5, "velocity": 80},
            {"tone": "5th", "beat": 2.5, "duration": 0.5, "velocity": 80},
            # Beat 4: power
            {"tone": "root", "beat": 3.0, "duration": 0.5, "velocity": 100},
            {"tone": "5th", "beat": 3.0, "duration": 0.5, "velocity": 95},
            # And of 4: full
            {"tone": "root", "beat": 3.5, "duration": 0.5, "velocity": 85},
            {"tone": "3rd", "beat": 3.5, "duration": 0.5, "velocity": 80},
            {"tone": "5th", "beat": 3.5, "duration": 0.5, "velocity": 80},
        ],
    },
    {
        "name": "strumming_16th",
        "category": "strumming",
        "style": "pop",
        "description": "16th note strumming with accented downbeats",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root", "beat": 0.0, "duration": 0.25, "velocity": 100},
            {"tone": "3rd", "beat": 0.0, "duration": 0.25, "velocity": 95},
            {"tone": "5th", "beat": 0.0, "duration": 0.25, "velocity": 90},
            {"tone": "root", "beat": 0.5, "duration": 0.25, "velocity": 80},
            {"tone": "3rd", "beat": 0.5, "duration": 0.25, "velocity": 75},
            {"tone": "5th", "beat": 0.5, "duration": 0.25, "velocity": 75},
            {"tone": "root", "beat": 1.0, "duration": 0.25, "velocity": 95},
            {"tone": "3rd", "beat": 1.0, "duration": 0.25, "velocity": 90},
            {"tone": "5th", "beat": 1.0, "duration": 0.25, "velocity": 85},
            {"tone": "root", "beat": 1.5, "duration": 0.25, "velocity": 80},
            {"tone": "3rd", "beat": 1.5, "duration": 0.25, "velocity": 75},
            {"tone": "5th", "beat": 1.5, "duration": 0.25, "velocity": 75},
            {"tone": "root", "beat": 2.0, "duration": 0.25, "velocity": 100},
            {"tone": "3rd", "beat": 2.0, "duration": 0.25, "velocity": 95},
            {"tone": "5th", "beat": 2.0, "duration": 0.25, "velocity": 90},
            {"tone": "root", "beat": 2.5, "duration": 0.25, "velocity": 80},
            {"tone": "3rd", "beat": 2.5, "duration": 0.25, "velocity": 75},
            {"tone": "5th", "beat": 2.5, "duration": 0.25, "velocity": 75},
            {"tone": "root", "beat": 3.0, "duration": 0.25, "velocity": 95},
            {"tone": "3rd", "beat": 3.0, "duration": 0.25, "velocity": 90},
            {"tone": "5th", "beat": 3.0, "duration": 0.25, "velocity": 85},
            {"tone": "root", "beat": 3.5, "duration": 0.25, "velocity": 80},
            {"tone": "3rd", "beat": 3.5, "duration": 0.25, "velocity": 75},
            {"tone": "5th", "beat": 3.5, "duration": 0.25, "velocity": 75},
        ],
    },
]


def _resolve_chord_tone(tone_ref, chord_midis):
    """Map a chord tone reference to an actual MIDI pitch.

    Args:
        tone_ref: Tone reference string ("root", "3rd", "5th", "7th", "octave").
        chord_midis: Sorted ascending list of MIDI pitches for the chord.

    Returns:
        int: The resolved MIDI pitch value.
    """
    if tone_ref == "root":
        return chord_midis[0]
    elif tone_ref == "3rd":
        return chord_midis[1] if len(chord_midis) > 1 else chord_midis[0]
    elif tone_ref == "5th":
        return chord_midis[2] if len(chord_midis) > 2 else chord_midis[-1]
    elif tone_ref == "7th":
        return chord_midis[3] if len(chord_midis) > 3 else chord_midis[-1]
    elif tone_ref == "octave":
        return chord_midis[0] + 12
    else:
        # Unrecognized tone reference: fall back to root
        return chord_midis[0]


def get_rhythm_patterns(category=None, style=None):
    """Retrieve rhythm pattern metadata, optionally filtered by category and/or style.

    Returns pattern info without the raw steps data -- just metadata and step count.

    Args:
        category: Optional filter. One of "arpeggio", "bass", "comping", "strumming".
        style: Optional filter. E.g., "basic", "jazz", "pop", "rock".

    Returns:
        list[dict]: Pattern metadata entries, each with keys:
                    name, category, style, description, time_signature, step_count.
    """
    results = []
    for pattern in RHYTHM_CATALOG:
        if category is not None and pattern["category"] != category:
            continue
        if style is not None and pattern["style"] != style:
            continue
        results.append({
            "name": pattern["name"],
            "category": pattern["category"],
            "style": pattern["style"],
            "description": pattern["description"],
            "time_signature": pattern["time_signature"],
            "step_count": len(pattern["steps"]),
        })
    return results


def apply_rhythm_pattern(chord_midis, pattern_name, start_beat=0.0, duration=4.0):
    """Apply a rhythm pattern to a chord, producing time-positioned MIDI notes.

    Output format matches add_notes_to_clip exactly:
    [{"pitch": int, "start_time": float, "duration": float, "velocity": int}]

    Args:
        chord_midis: List of MIDI pitches for the chord.
        pattern_name: Name of a pattern from RHYTHM_CATALOG.
        start_beat: Starting beat position in clip timeline (default 0.0).
        duration: Duration in beats; pattern plays once within this (default 4.0).

    Returns:
        list[dict]: Notes in add_notes_to_clip format.

    Raises:
        ValueError: If pattern_name is not found in the catalog.
    """
    # Look up pattern
    pattern = None
    for p in RHYTHM_CATALOG:
        if p["name"] == pattern_name:
            pattern = p
            break

    if pattern is None:
        raise ValueError(
            f"Unknown rhythm pattern: '{pattern_name}'. "
            f"Use get_rhythm_patterns() to see available patterns."
        )

    sorted_midis = sorted(chord_midis)

    notes = []
    for step in pattern["steps"]:
        # Skip steps beyond duration (per Pitfall 3)
        if step["beat"] >= duration:
            continue

        pitch = _resolve_chord_tone(step["tone"], sorted_midis)
        note_dur = min(step["duration"], duration - step["beat"])

        notes.append({
            "pitch": pitch,
            "start_time": start_beat + step["beat"],
            "duration": note_dur,
            "velocity": step["velocity"],
        })

    return notes
