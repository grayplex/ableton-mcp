"""Progression engine library: catalog, generation, analysis, and suggestion of chord progressions."""

import re

from MCP_Server.theory.pitch import _force_sharp, _format_note_name, _parse_note_name
from MCP_Server.theory.chords import (
    _make_note_obj,
    _midi_to_pitch,
    build_chord,
    _get_harmony_module,
    _get_key_module,
    _get_roman_module,
    _get_pitch_module,
)
from MCP_Server.theory.scales import SCALE_CATALOG

# ---------------------------------------------------------------------------
# PROGRESSION_CATALOG: 25 progressions across 7 genres (per D-01, D-02, D-03)
# Each entry stores Roman numeral sequences only -- resolved to MIDI at call time.
# ---------------------------------------------------------------------------

PROGRESSION_CATALOG = [
    # --- Pop (4) ---
    {"name": "Axis of Awesome", "genre": "pop", "numerals": ["I", "V", "vi", "IV"]},
    {"name": "Sensitive Female", "genre": "pop", "numerals": ["vi", "IV", "I", "V"]},
    {"name": "50s Progression", "genre": "pop", "numerals": ["I", "vi", "IV", "V"]},
    {"name": "Pop-Punk", "genre": "pop", "numerals": ["I", "V", "vi", "iii", "IV", "I", "IV", "V"]},
    # --- Rock (4) ---
    {"name": "Classic Rock", "genre": "rock", "numerals": ["I", "IV", "V"]},
    {"name": "Rock Anthem", "genre": "rock", "numerals": ["I", "bVII", "IV", "I"]},
    {"name": "Grunge", "genre": "rock", "numerals": ["i", "bVI", "bVII", "i"]},
    {"name": "Power Ballad", "genre": "rock", "numerals": ["I", "V", "vi", "IV"]},
    # --- Jazz (5) ---
    {"name": "ii-V-I Major", "genre": "jazz", "numerals": ["ii7", "V7", "I7"]},
    {"name": "ii-V-I Minor", "genre": "jazz", "numerals": ["ii7b5", "V7", "i7"]},
    {"name": "Jazz Turnaround", "genre": "jazz", "numerals": ["I7", "vi7", "ii7", "V7"]},
    {"name": "Rhythm Changes A", "genre": "jazz", "numerals": ["I", "vi", "ii", "V"]},
    {"name": "Coltrane Changes", "genre": "jazz", "numerals": ["I7", "bIII7", "V7", "bVII7"]},
    # --- Blues (3) ---
    {"name": "12-Bar Blues", "genre": "blues", "numerals": ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"]},
    {"name": "Minor Blues", "genre": "blues", "numerals": ["i", "i", "i", "i", "iv", "iv", "i", "i", "bVI", "V", "i", "i"]},
    {"name": "Jazz Blues", "genre": "blues", "numerals": ["I7", "IV7", "I7", "I7", "IV7", "IV7", "I7", "vi7", "ii7", "V7", "I7", "V7"]},
    # --- R&B / Soul (3) ---
    {"name": "Neo-Soul", "genre": "rnb", "numerals": ["ii7", "V7", "I7", "IV7"]},
    {"name": "Motown", "genre": "rnb", "numerals": ["I", "IV", "vi", "V"]},
    {"name": "R&B Ballad", "genre": "rnb", "numerals": ["I", "iii", "IV", "V"]},
    # --- Classical (3) ---
    {"name": "Authentic Cadence", "genre": "classical", "numerals": ["IV", "V", "I"]},
    {"name": "Pachelbel Canon", "genre": "classical", "numerals": ["I", "V", "vi", "iii", "IV", "I", "IV", "V"]},
    {"name": "Romanesca", "genre": "classical", "numerals": ["I", "V", "vi", "III", "IV", "I", "IV", "V"]},
    # --- EDM (3) ---
    {"name": "EDM Anthem", "genre": "edm", "numerals": ["vi", "IV", "I", "V"]},
    {"name": "Trance", "genre": "edm", "numerals": ["i", "bVII", "bVI", "bVII"]},
    {"name": "Future Bass", "genre": "edm", "numerals": ["I", "iii", "vi", "IV"]},
]

# ---------------------------------------------------------------------------
# Functional harmony mappings (per D-08)
# ---------------------------------------------------------------------------

_CHORD_FUNCTIONS = {
    "I": "tonic", "i": "tonic",
    "ii": "predominant", "II": "predominant",
    "iii": "mediant", "III": "mediant",
    "IV": "predominant", "iv": "predominant",
    "V": "dominant", "v": "dominant",
    "vi": "submediant", "VI": "submediant",
    "vii": "leading_tone", "VII": "subtonic",
    "bVII": "subtonic", "bvii": "subtonic",
    "bVI": "submediant", "bvi": "submediant",
    "bIII": "mediant", "biii": "mediant",
}

# Strip quality suffixes to get base numeral for function lookup
_QUALITY_SUFFIX_RE = re.compile(r"^(#?b?[ivIV]+)")

# ---------------------------------------------------------------------------
# Theory rules: functional harmony -> likely next chords (per RESEARCH section 4)
# Each tuple: (numeral, score, reason)
# ---------------------------------------------------------------------------

_THEORY_RULES = {
    "tonic": [
        ("IV", 3, "predominant motion"),
        ("V", 3, "direct to dominant"),
        ("vi", 2, "tonic prolongation"),
        ("ii", 2, "predominant motion"),
    ],
    "predominant": [
        ("V", 5, "predominant to dominant"),
        ("V7", 5, "predominant to dominant"),
        ("viio", 2, "leading tone resolution"),
    ],
    "dominant": [
        ("I", 6, "authentic resolution"),
        ("i", 5, "authentic resolution"),
        ("vi", 3, "deceptive cadence"),
        ("VI", 2, "deceptive cadence"),
    ],
    "submediant": [
        ("ii", 3, "predominant motion"),
        ("IV", 3, "predominant motion"),
        ("V", 2, "direct to dominant"),
    ],
    "mediant": [
        ("IV", 3, "predominant motion"),
        ("vi", 2, "submediant motion"),
    ],
    "leading_tone": [
        ("I", 5, "resolution"),
        ("i", 4, "resolution"),
    ],
    "subtonic": [
        ("I", 3, "rock cadence"),
        ("i", 2, "minor resolution"),
    ],
}

# Weights for hybrid suggestion algorithm
_THEORY_WEIGHT = 1.0
_CATALOG_WEIGHT = 0.5

# Regex to normalize chord names: convert "b" flat notation to "-" for music21
# Matches note letter + "b" (flat) but not quality suffixes like "dim", "m", etc.
_CHORD_NAME_RE = re.compile(r"^([A-Ga-g])(b)(.*)")


def _normalize_chord_name(name):
    """Normalize a chord name for music21's ChordSymbol parser.

    Converts user-friendly flat notation (e.g., "Bb", "Ebm7") to music21's
    internal format (e.g., "B-", "E-m7").
    """
    m = _CHORD_NAME_RE.match(name)
    if m:
        letter = m.group(1)
        suffix = m.group(3)
        return letter + "-" + suffix
    return name


def _get_base_numeral(numeral):
    """Extract base Roman numeral from a numeral with quality suffixes.

    Examples: 'V7' -> 'V', 'ii7b5' -> 'ii', 'bVII7' -> 'bVII', 'viio' -> 'vii'
    """
    m = _QUALITY_SUFFIX_RE.match(numeral)
    if m:
        return m.group(1)
    return numeral


def _get_function(numeral):
    """Get the harmonic function label for a Roman numeral."""
    base = _get_base_numeral(numeral)
    return _CHORD_FUNCTIONS.get(base, "tonic")


def _resolve_numeral_to_chord(numeral, key_name, scale_type="major", octave=4):
    """Resolve a Roman numeral to a unified chord object in a given key.

    Uses music21's RomanNumeral class for standard major/minor keys.
    For modal scale types, uses the parent major key mapping.

    Args:
        numeral: Roman numeral string (e.g., "V7", "ii", "bVII")
        key_name: Key root (e.g., "C", "G", "F#")
        scale_type: Scale type (default "major")
        octave: Target octave for chord voicing

    Returns:
        dict: Unified chord object {"numeral": str, "root": str, "quality": str,
              "notes": [{"midi": int, "name": str}, ...]}

    Raises:
        ValueError: If numeral cannot be resolved
    """
    key_mod = _get_key_module()
    roman_mod = _get_roman_module()

    # Determine the key object based on scale type
    if scale_type in ("minor", "natural_minor", "aeolian"):
        k = key_mod.Key(key_name, "minor")
    elif scale_type in ("major", "ionian"):
        k = key_mod.Key(key_name)
    elif scale_type in SCALE_CATALOG:
        # Modal scales: use the parent major key approach
        # For dorian on D, the parent major is C, etc.
        # Build scale from intervals to find the parent major root
        intervals = SCALE_CATALOG[scale_type]["intervals"]
        major_intervals = SCALE_CATALOG.get("major", {}).get("intervals", [2, 2, 1, 2, 2, 2, 1])

        # Find the mode index by checking interval rotation
        mode_idx = None
        if len(intervals) == 7:
            for i in range(7):
                rotated = major_intervals[i:] + major_intervals[:i]
                if rotated == intervals:
                    mode_idx = i
                    break

        if mode_idx is not None:
            # Calculate parent major root
            root_pitch = _parse_note_name(key_name + "4")
            root_midi = root_pitch.midi
            # Go back by the sum of intervals before this mode position
            parent_midi = root_midi
            for step in intervals[:mode_idx]:
                parent_midi -= step
            parent_pitch = _midi_to_pitch(parent_midi % 12 + 60)
            parent_name = _format_note_name(parent_pitch).replace(str(parent_pitch.octave), "")
            k = key_mod.Key(parent_name)
        else:
            # Non-modal scale: fall back to major key
            k = key_mod.Key(key_name)
    else:
        k = key_mod.Key(key_name)

    try:
        rn = roman_mod.RomanNumeral(numeral, k)
    except Exception as exc:
        raise ValueError(f"Invalid Roman numeral: '{numeral}' in key {key_name} {scale_type}") from exc

    pitches = list(rn.pitches)
    if not pitches:
        raise ValueError(f"Roman numeral '{numeral}' produced no pitches in key {key_name}")

    # Transpose to target octave
    root_pitch = rn.root()
    root_octave = root_pitch.octave if root_pitch.octave is not None else 4
    semitone_shift = (octave - root_octave) * 12

    note_objs = []
    for p in pitches:
        new_p = p.transpose(semitone_shift)
        note_objs.append(_make_note_obj(new_p))

    root_transposed = root_pitch.transpose(semitone_shift)
    root_name = _make_note_obj(root_transposed)["name"]
    quality_str = rn.quality if hasattr(rn, "quality") and rn.quality else ""

    return {
        "numeral": numeral,
        "root": root_name,
        "quality": quality_str,
        "notes": note_objs,
    }


def _voice_lead_pair(prev_midis, next_pitch_classes):
    """Voice-lead next chord to minimize total movement from previous chord.

    For each pitch class in the next chord, find the nearest octave placement
    relative to the center of the previous chord, then optimize assignment to
    minimize total voice movement.

    Args:
        prev_midis: List of MIDI pitch values for the previous chord
        next_pitch_classes: List of pitch classes (0-11) for the next chord

    Returns:
        list[int]: Voice-led MIDI pitches, sorted ascending
    """
    center = sum(prev_midis) / len(prev_midis)
    prev_sorted = sorted(prev_midis)

    # For each pitch class, generate nearest candidate to the chord center
    candidates = []
    for pc in next_pitch_classes:
        # Find nearest octave placement to chord center
        base = int(center) - (int(center) % 12) + pc
        # Try base and base-12 to find closest to center
        options = [base - 12, base, base + 12]
        best = min(options, key=lambda x: abs(x - center))
        candidates.append(best)

    # Greedy assignment: for each prev voice (sorted), assign the nearest
    # available candidate to minimize total movement
    if len(candidates) == len(prev_sorted):
        # Try all permutations for small chords (3-4 notes), or greedy for larger
        from itertools import permutations

        if len(candidates) <= 5:
            best_perm = None
            best_cost = float("inf")
            for perm in permutations(candidates):
                cost = sum(abs(p - c) for p, c in zip(prev_sorted, sorted(perm)))
                if cost < best_cost:
                    best_cost = cost
                    best_perm = perm
            return sorted(best_perm)

    # Different sizes or too large: use center-based placement
    return sorted(candidates)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_common_progressions(key, genre=None, octave=4):
    """Retrieve common chord progressions, optionally filtered by genre.

    Each progression is resolved to concrete MIDI pitches in the given key.

    Args:
        key: Key root note (e.g., "C", "G", "F#")
        genre: Optional genre filter (case-insensitive). One of:
               pop, rock, jazz, blues, rnb, classical, edm
        octave: Target octave for chord voicings (default 4)

    Returns:
        list[dict]: Each entry has keys: name, genre, numerals, chords
                    where chords is a list of unified chord objects
    """
    # Filter catalog by genre if provided
    if genre is not None:
        genre_lower = genre.lower()
        entries = [p for p in PROGRESSION_CATALOG if p["genre"].lower() == genre_lower]
    else:
        entries = list(PROGRESSION_CATALOG)

    results = []
    for entry in entries:
        chords = []
        for numeral in entry["numerals"]:
            chord_obj = _resolve_numeral_to_chord(numeral, key, "major", octave)
            chords.append(chord_obj)
        results.append({
            "name": entry["name"],
            "genre": entry["genre"],
            "numerals": list(entry["numerals"]),
            "chords": chords,
        })

    return results


def generate_progression(key, numerals, scale_type="major", octave=4):
    """Generate a chord progression with voice leading from Roman numerals.

    Resolves each numeral to a chord in the given key and scale, then applies
    nearest-voice voice leading between consecutive chords.

    Args:
        key: Key root note (e.g., "C", "D", "Ab")
        numerals: List of Roman numeral strings (e.g., ["I", "IV", "V", "I"])
        scale_type: Scale/mode for chord resolution (default "major")
        octave: Target octave for chord voicings (default 4)

    Returns:
        dict: {"key": str, "scale_type": str, "chords": [unified_chord_obj, ...]}

    Raises:
        ValueError: If numerals is empty, or scale_type is invalid
    """
    if not numerals:
        raise ValueError("numerals must be a non-empty list of Roman numeral strings")

    # Validate scale_type
    valid_scale_types = {"major", "minor", "natural_minor"}
    if scale_type not in valid_scale_types and scale_type not in SCALE_CATALOG:
        raise ValueError(
            f"Unknown scale type: '{scale_type}'. "
            f"Use 'major', 'minor', or a scale from the catalog."
        )

    chords = []

    # First chord: close position (default voicing)
    first_chord = _resolve_numeral_to_chord(numerals[0], key, scale_type, octave)
    chords.append(first_chord)

    # Subsequent chords: voice-lead from previous
    for i in range(1, len(numerals)):
        # Resolve to get the pitch classes of the next chord
        next_chord_raw = _resolve_numeral_to_chord(numerals[i], key, scale_type, octave)
        next_pcs = [n["midi"] % 12 for n in next_chord_raw["notes"]]

        # Voice-lead from previous chord
        prev_midis = [n["midi"] for n in chords[-1]["notes"]]
        voiced_midis = _voice_lead_pair(prev_midis, next_pcs)

        # Build note objects from voice-led MIDI values
        voiced_notes = [_make_note_obj(_midi_to_pitch(m)) for m in voiced_midis]

        chords.append({
            "numeral": numerals[i],
            "root": next_chord_raw["root"],
            "quality": next_chord_raw["quality"],
            "notes": voiced_notes,
        })

    return {
        "key": key,
        "scale_type": scale_type,
        "chords": chords,
    }


def analyze_progression(chord_names, key):
    """Analyze a chord progression, identifying Roman numerals for each chord.

    Handles diatonic and non-diatonic chords (borrowed chords, secondary dominants).

    Args:
        chord_names: List of chord name strings (e.g., ["C", "F", "G", "C"])
        key: Key for analysis (e.g., "C", "G", "Ab")

    Returns:
        list[dict]: Each entry is a unified chord object with numeral, root, quality,
                    notes, and optional function field

    Raises:
        ValueError: If chord_names is empty or contains invalid chord names
    """
    if not chord_names:
        raise ValueError("chord_names must be a non-empty list")

    harmony = _get_harmony_module()
    key_mod = _get_key_module()
    roman_mod = _get_roman_module()

    k = key_mod.Key(key)

    results = []
    for name in chord_names:
        try:
            normalized = _normalize_chord_name(name)
            cs = harmony.ChordSymbol(normalized)
        except Exception as exc:
            raise ValueError(f"Invalid chord name: '{name}'") from exc

        pitches = list(cs.pitches)
        if not pitches:
            raise ValueError(f"Chord name '{name}' produced no pitches")

        # Get Roman numeral analysis
        try:
            rn = roman_mod.romanNumeralFromChord(cs, k)
        except Exception:
            # Fallback: still return the chord data without numeral analysis
            note_objs = [_make_note_obj(p) for p in pitches]
            results.append({
                "numeral": "?",
                "root": _make_note_obj(cs.root())["name"] if cs.root() else name,
                "quality": cs.quality if hasattr(cs, "quality") else "",
                "notes": note_objs,
            })
            continue

        # Extract numeral figure, root, quality
        figure = rn.figure if hasattr(rn, "figure") else "?"
        quality_str = rn.quality if hasattr(rn, "quality") and rn.quality else ""

        # Build note objects from the ChordSymbol pitches
        note_objs = [_make_note_obj(p) for p in pitches]

        # Root note
        try:
            root_name = _make_note_obj(cs.root())["name"]
        except Exception:
            root_name = name

        # Get harmonic function
        func = _get_function(figure)

        results.append({
            "numeral": figure,
            "root": root_name,
            "quality": quality_str,
            "notes": note_objs,
            "function": func,
        })

    return results


def suggest_next_chord(key, preceding, genre=None):
    """Suggest next chords given preceding context using hybrid theory + catalog approach.

    Combines functional harmony rules with catalog frequency analysis to produce
    ranked chord suggestions.

    Args:
        key: Key root note (e.g., "C", "G")
        preceding: List of Roman numeral strings for preceding chords (1-4 chords)
        genre: Optional genre filter for catalog matching

    Returns:
        list[dict]: Top 3-5 suggestions, each with numeral, root, quality, notes,
                    reason, and score fields. Sorted by score descending.

    Raises:
        ValueError: If preceding is empty
    """
    if not preceding:
        raise ValueError("preceding must be a non-empty list of Roman numeral strings")

    # Use up to last 4 chords for context (per D-11)
    context = preceding[-4:]

    # Step 1: Get harmonic function of the last chord
    last_numeral = context[-1]
    last_function = _get_function(last_numeral)

    # Step 2: Theory rule suggestions
    candidates = {}  # numeral -> {"score": float, "reasons": [str]}
    theory_suggestions = _THEORY_RULES.get(last_function, [])
    for numeral, score, reason in theory_suggestions:
        if numeral not in candidates:
            candidates[numeral] = {"score": 0.0, "reasons": []}
        candidates[numeral]["score"] += score * _THEORY_WEIGHT
        candidates[numeral]["reasons"].append(reason)

    # Step 3: Catalog matching
    catalog_entries = PROGRESSION_CATALOG
    if genre is not None:
        genre_lower = genre.lower()
        catalog_entries = [p for p in catalog_entries if p["genre"].lower() == genre_lower]

    for prog in catalog_entries:
        numerals = prog["numerals"]
        # Normalize for matching: strip quality suffixes to get base numerals
        prog_bases = [_get_base_numeral(n) for n in numerals]
        context_bases = [_get_base_numeral(n) for n in context]

        # Search for the context as a subsequence in the progression
        for start in range(len(prog_bases)):
            # Check if context matches starting at this position
            match = True
            for j, ctx_base in enumerate(context_bases):
                idx = start + j
                if idx >= len(prog_bases) or prog_bases[idx] != ctx_base:
                    match = False
                    break
            if match:
                # What follows the context in this progression?
                next_idx = start + len(context_bases)
                if next_idx < len(numerals):
                    next_numeral = numerals[next_idx]
                    if next_numeral not in candidates:
                        candidates[next_numeral] = {"score": 0.0, "reasons": []}
                    candidates[next_numeral]["score"] += _CATALOG_WEIGHT
                    reason = f"common {prog['genre']} pattern ({prog['name']})"
                    if reason not in candidates[next_numeral]["reasons"]:
                        candidates[next_numeral]["reasons"].append(reason)

    # Step 4: Rank and resolve top 5
    ranked = sorted(candidates.items(), key=lambda x: x[1]["score"], reverse=True)[:5]

    # Ensure we return at least 3 suggestions by adding fallback diatonic chords
    if len(ranked) < 3:
        fallback_numerals = ["I", "IV", "V", "vi", "ii"]
        for fb in fallback_numerals:
            if fb not in candidates and len(ranked) < 3:
                ranked.append((fb, {"score": 0.5, "reasons": ["diatonic option"]}))

    results = []
    for numeral, info in ranked:
        try:
            chord_obj = _resolve_numeral_to_chord(numeral, key, "major", 4)
        except (ValueError, Exception):
            continue
        chord_obj["reason"] = info["reasons"][0] if info["reasons"] else "harmonic option"
        chord_obj["score"] = round(info["score"], 2)
        results.append(chord_obj)

    return results
