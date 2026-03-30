# Phase 17: Progression Engine - Research

**Date:** 2026-03-24
**Phase:** 17-progression-engine

---

## 1. Progression Catalog (~25 progressions across 7 genres)

### Pop (4)
| Name | Numerals |
|------|----------|
| Axis of Awesome | I, V, vi, IV |
| Sensitive Female | vi, IV, I, V |
| 50s Progression | I, vi, IV, V |
| Pop-Punk | I, V, vi, iii, IV, I, IV, V |

### Rock (4)
| Name | Numerals |
|------|----------|
| Classic Rock | I, IV, V |
| Rock Anthem | I, bVII, IV, I |
| Grunge | i, bVI, bVII, i |
| Power Ballad | I, V, vi, IV |

### Jazz (5)
| Name | Numerals |
|------|----------|
| ii-V-I Major | ii7, V7, I7 |
| ii-V-I Minor | ii7b5, V7, i7 |
| Jazz Turnaround | I7, vi7, ii7, V7 |
| Rhythm Changes A | I, vi, ii, V |
| Coltrane Changes | I7, bIII7, V7, bVII7 |

### Blues (3)
| Name | Numerals |
|------|----------|
| 12-Bar Blues | I, I, I, I, IV, IV, I, I, V, IV, I, V |
| Minor Blues | i, i, i, i, iv, iv, i, i, bVI, V, i, i |
| Jazz Blues | I7, IV7, I7, I7, IV7, IV7, I7, vi7, ii7, V7, I7, V7 |

### R&B / Soul (3)
| Name | Numerals |
|------|----------|
| Neo-Soul | ii7, V7, I7, IV7 |
| Motown | I, IV, vi, V |
| R&B Ballad | I, iii, IV, V |

### Classical (3)
| Name | Numerals |
|------|----------|
| Authentic Cadence | IV, V, I |
| Pachelbel Canon | I, V, vi, iii, IV, I, IV, V |
| Romanesca | I, V, vi, III, IV, I, IV, V |

### EDM (3)
| Name | Numerals |
|------|----------|
| EDM Anthem | vi, IV, I, V |
| Trance | i, bVII, bVI, bVII |
| Future Bass | I, iii, vi, IV |

**Total: 25 progressions**

---

## 2. music21 Roman Numeral API

### Core class: `music21.roman.RomanNumeral`

```python
from music21 import roman, key

# Create Roman numeral in a key
k = key.Key("C")
rn = roman.RomanNumeral("V7", k)

# Get pitches
rn.pitches  # (G4, B4, D5, F5)
rn.root()   # Pitch G4
rn.quality  # 'dominant'

# Resolve to MIDI
[p.midi for p in rn.pitches]  # [67, 71, 74, 77]
```

### Analyzing chords as Roman numerals

```python
from music21 import harmony, roman, key

# Parse chord name to ChordSymbol
cs = harmony.ChordSymbol("Dm7")
# cs.pitches gives (D3, F3, A3, C4)

# Determine Roman numeral in a key
k = key.Key("C")
rn = roman.romanNumeralFromChord(cs, k)
rn.figure  # "ii7"
rn.quality  # 'minor'
```

Key method: `roman.romanNumeralFromChord(chord_obj, key_obj)` — this is the primary API for analyzing chords as Roman numerals. It handles:
- Diatonic chords → standard numerals (I, ii, iii, etc.)
- Non-diatonic chords → chromatic alterations (#IV, bVII, etc.)
- Secondary dominants when detectable

### Non-diatonic chord detection

music21's `romanNumeralFromChord` will produce chromatic Roman numerals for non-diatonic chords:
- Borrowed chords: bVII, bIII, bVI (from parallel minor)
- Secondary dominants: Need explicit detection — check if a chord is V/x pattern
- Neapolitan: bII chord

For secondary dominant detection:
```python
# Check if chord could be V of the next chord
# If chord is major/dominant and its root is a P5 above the next chord's root
# then label it as V/x
```

### Key + scale type for modal progressions

```python
# For modal progressions (e.g., Dorian)
# Use key.Key with mode
k = key.Key("D", "dorian")  # Does NOT work — Key only takes major/minor
# Instead: use key.Key("C") (parent major key) and interpret numerals relative to D
# OR: Use RomanNumeral with explicit scale
from music21 import scale
s = scale.DorianScale("D")
```

**Recommended approach:** For standard major/minor, use `key.Key()`. For modal progressions, build the scale from SCALE_CATALOG intervals and resolve numerals manually using `build_chord` with scale degree roots. This is simpler and more consistent than fighting music21's modal key support.

---

## 3. Voice Leading Algorithm (Basic Nearest-Voice)

### Algorithm: Minimize total pitch movement

Given previous chord voicing (MIDI pitches) and next chord (pitch classes to voice):

1. Start with previous chord's MIDI pitches as reference
2. For next chord's pitch classes, find the voicing that minimizes total semitone movement
3. For each voice, find the nearest octave placement of the target pitch class

```python
def _voice_lead_pair(prev_midis, next_pitch_classes):
    """Voice-lead next chord to minimize movement from prev chord."""
    result = []
    used_pcs = list(next_pitch_classes)

    # For each voice in prev chord, find nearest target pitch class
    for prev_midi in prev_midis:
        best_midi = None
        best_dist = float('inf')
        for pc in used_pcs:
            # Try nearest octave placements
            candidate = prev_midi + ((pc - prev_midi % 12) % 12)
            if candidate - prev_midi > 6:
                candidate -= 12
            dist = abs(candidate - prev_midi)
            if dist < best_dist:
                best_dist = dist
                best_midi = candidate
        result.append(best_midi)

    return sorted(result)
```

### Handling different chord sizes

When consecutive chords have different numbers of notes (e.g., triad → 7th chord):
- Extra notes: add them in the nearest available position
- Fewer notes: drop the voice with the largest movement

### First chord voicing

The first chord in a progression needs a default voicing. Use close position in the target octave (from `build_chord`).

---

## 4. Next-Chord Suggestion (Hybrid Algorithm)

### Theory Rules (functional harmony)

| Current function | Likely next | Weight |
|-----------------|-------------|--------|
| Tonic (I, i) | Any | - |
| Predominant (ii, IV, ii7) | Dominant (V, V7, viio) | High |
| Dominant (V, V7, viio) | Tonic (I, i) | Very high |
| Submediant (vi) | Predominant (ii, IV) or Dominant (V) | Medium |
| Mediant (iii) | Predominant (IV, vi) | Medium |

### Common substitution patterns

| Pattern | Description |
|---------|-------------|
| V → I (or i) | Authentic resolution |
| V → vi | Deceptive cadence |
| IV → I | Plagal cadence |
| ii → V | Predominant to dominant |
| I → vi → IV → V | Pop pattern continuation |
| bVII → I | Rock cadence |

### Catalog frequency weighting

Count how often each numeral follows the current context in the progression catalog. Weight these alongside theory rules.

### Algorithm

```python
def suggest_next(key, preceding_chords, genre=None):
    candidates = {}

    # 1. Theory rules: score based on functional harmony
    last_chord = preceding_chords[-1]
    for next_chord, score in theory_rules[function_of(last_chord)]:
        candidates[next_chord] = score * THEORY_WEIGHT

    # 2. Catalog matching: find progressions containing the preceding sequence
    # Score next chords by frequency
    for prog in catalog (filtered by genre if given):
        for i, match subsequence in prog:
            next_in_prog = prog[i + len(preceding)]
            candidates[next_in_prog] += CATALOG_WEIGHT

    # 3. Rank and return top 5
    return sorted(candidates, key=score, reverse=True)[:5]
```

### Reason strings

Map each suggestion to a brief reason:
- "dominant resolution (V → I)"
- "deceptive cadence (V → vi)"
- "common pop pattern"
- "predominant motion (ii → V)"
- "catalog pattern (jazz turnaround)"

---

## 5. Chord Name Parsing for analyze_progression

### Using music21.harmony.ChordSymbol

```python
from music21 import harmony

# Parses standard chord notation
cs = harmony.ChordSymbol("Cmaj7")  # C major 7th
cs = harmony.ChordSymbol("Dm")     # D minor
cs = harmony.ChordSymbol("G7")     # G dominant 7th
cs = harmony.ChordSymbol("F#m7b5") # F# half-diminished 7th
cs = harmony.ChordSymbol("Bb")     # Bb major
cs = harmony.ChordSymbol("Edim7")  # E diminished 7th
```

ChordSymbol handles a wide range of notation styles. It returns a chord object with `.pitches`, `.root()`, `.quality`, and other attributes.

### Flow for analyze_progression

1. Parse each chord name string via `harmony.ChordSymbol(name)`
2. Create a `key.Key(key_name)` for the analysis key
3. Use `roman.romanNumeralFromChord(cs, k)` to get the Roman numeral
4. Extract: `.figure` (numeral string), `.quality`, `.root()`, `.pitches`
5. Build rich output object per D-14/D-15

### Edge cases

- Invalid chord names: ChordSymbol may silently produce wrong results or raise — catch and report
- Slash chords (e.g., "C/E"): ChordSymbol supports these
- Enharmonic: "Db" vs "C#" — music21 handles this
- Chord names with "b" ambiguity (e.g., "Bb" vs "B flat"): ChordSymbol handles standard notation

---

## 6. Existing Code Reuse Strategy

### From chords.py

| Function | Used by | Purpose |
|----------|---------|---------|
| `build_chord()` | `get_common_progressions`, `generate_progression` | Resolve root + quality to MIDI pitches |
| `get_diatonic_chords()` | `analyze_progression`, `suggest_next_chord` | Get diatonic chord set for Roman numeral context |
| `identify_chord()` | Potentially `analyze_progression` | Fallback chord identification |
| `_make_note_obj()` | All functions | Convert music21 Pitch to `{"midi": int, "name": str}` |
| `_midi_to_pitch()` | Voice leading | Convert MIDI int to music21 Pitch |
| `_get_key_module()` | `analyze_progression` | Lazy music21.key import |
| `_get_roman_module()` | `analyze_progression`, `generate_progression` | Lazy music21.roman import |
| `_get_harmony_module()` | `analyze_progression` | Lazy music21.harmony import for ChordSymbol |

### From scales.py

| Function | Used by | Purpose |
|----------|---------|---------|
| `SCALE_CATALOG` | `generate_progression` | Get interval pattern for modal progressions |
| `get_scale_pitches()` | `generate_progression` | Generate scale degrees for modal chord building |

### From pitch.py

| Function | Used by | Purpose |
|----------|---------|---------|
| `_force_sharp()` | All functions via `_make_note_obj` | Consistent sharp spelling |
| `_format_note_name()` | All functions via `_make_note_obj` | Note name formatting |

---

## 7. File Structure

### New file: `MCP_Server/theory/progressions.py`

```
progressions.py
├── Lazy imports (_get_harmony_module, _get_key_module, _get_roman_module reused from chords)
├── PROGRESSION_CATALOG (list of dicts: name, genre, numerals)
├── _CHORD_FUNCTIONS (dict mapping numeral patterns to functional labels)
├── _THEORY_RULES (dict mapping functions to likely next chords with weights)
├── get_common_progressions(key, genre=None, octave=4) → dict
├── generate_progression(key, numerals, scale_type="major", octave=4) → dict
├── analyze_progression(chord_names, key) → dict
├── suggest_next_chord(key, preceding, genre=None) → dict
└── _voice_lead_pair(prev_midis, next_pitch_classes) → list[int]  (internal helper)
```

### Modifications to existing files

1. `MCP_Server/theory/__init__.py` — Add 4 exports from progressions
2. `MCP_Server/tools/theory.py` — Add 4 @mcp.tool() functions with aliased imports
3. `tests/test_theory.py` — Add TestProgressionLibrary and TestProgressionTools classes

---

## 8. Unified Chord Object Format (D-15)

All 4 tools return chords in this shape:

```json
{
  "numeral": "V7",
  "root": "G4",
  "quality": "dominant",
  "notes": [
    {"midi": 67, "name": "G4"},
    {"midi": 71, "name": "B4"},
    {"midi": 74, "name": "D5"},
    {"midi": 77, "name": "F5"}
  ]
}
```

Optional fields per context:
- `"reason"` — only in suggest_next_chord output
- `"score"` — only in suggest_next_chord output
- `"function"` — chord function label (tonic/predominant/dominant) in analyze_progression

---

## 9. Plan Split Recommendation

**Plan 17-01: Progression library** (Wave 1)
- Create `MCP_Server/theory/progressions.py` with PROGRESSION_CATALOG and all 4 library functions
- Update `MCP_Server/theory/__init__.py` with 4 new exports
- Add unit tests in `tests/test_theory.py`

**Plan 17-02: Wire MCP tools** (Wave 2, depends on 17-01)
- Add 4 @mcp.tool() functions in `MCP_Server/tools/theory.py`
- Add integration tests
- Verify total tool count reaches 190 (186 existing + 4 new)

This matches the Phase 15 and 16 pattern of library-then-tools split.
