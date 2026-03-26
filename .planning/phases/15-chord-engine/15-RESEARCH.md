# Phase 15: Chord Engine — Research

**Date:** 2026-03-24
**Phase:** 15-chord-engine
**Requirements:** CHRD-01, CHRD-02, CHRD-03, CHRD-04, CHRD-05

## RESEARCH COMPLETE

## 1. music21 Chord APIs

### 1.1 Building Chords (CHRD-01)

**Primary approach: `harmony.ChordSymbol`**

`harmony.ChordSymbol(root + quality)` builds chords from standard notation:

```python
from music21 import harmony
h = harmony.ChordSymbol('Cmaj7')
# pitches: ['C3', 'E3', 'G3', 'B3'], midi: [48, 52, 55, 59]
```

**Verified quality strings that work:**
- Triads: `C` (major), `Cm` (minor), `Cdim` (diminished), `Caug` (augmented)
- 7ths: `Cmaj7`, `Cm7`, `C7` (dominant), `Cdim7`, `Cm7b5` (half-dim)
- Extended: `C9`, `Cm9`, `C11`, `C13`
- Suspended: `Csus4`, `Csus2`
- Add: `Cadd9`
- Altered: `C7#9`, `C7b5`

**Octave handling:** ChordSymbol defaults to octave 3. Our tool needs to transpose to the user's requested octave (default 4 per D-04). Simple approach: build at default octave, then transpose all pitches by `(target_octave - root_octave) * 12` semitones.

**Quality string mapping:** Since the user sends separate `root` + `quality` params (D-03), we concatenate them: `harmony.ChordSymbol(root + quality)`. The quality string must use ChordSymbol notation (e.g., `maj7` not `major7`). The tool should map short symbols (D-02) to ChordSymbol-compatible strings.

**Key mapping needed:**
- `maj` → `` (empty string for ChordSymbol — `C` = C major)
- `min` → `m`
- `dim` → `dim`
- `aug` → `aug`
- `maj7` → `maj7`
- `min7` → `m7`
- `dom7` or `7` → `7`
- `dim7` → `dim7`
- `hdim7` or `min7b5` → `m7b5`
- `sus2` → `sus2`
- `sus4` → `sus4`
- Extended/altered pass through directly: `9`, `m9`, `11`, `13`, `7#9`, `7b5`, etc.

### 1.2 Inversions (CHRD-02)

**music21 supports inversions natively:**

```python
c = chord.Chord(['C4', 'E4', 'G4'])
c.inversion(1)  # Returns chord with E in bass: [64, 67, 72]
c.inversion(2)  # Returns chord with G in bass: [67, 72, 76]
```

When inverting, music21 rotates the bottom note up an octave. For a triad: 3 inversions (0, 1, 2). For a 7th chord: 4 inversions (0, 1, 2, 3).

**Implementation:** Build chord at target octave, then generate all inversions by calling `.inversion(n)` for n in range(len(chord.pitches)). Return all at once (D-07).

### 1.3 Voicings (CHRD-03)

**music21 does NOT have built-in voicing methods.** Close position is the default. Open, drop-2, and drop-3 must be implemented manually:

- **Close voicing:** Default output from ChordSymbol — all notes within one octave
- **Open voicing:** Spread notes: drop every other note (starting from 2nd from bottom) by one octave, then re-sort
- **Drop-2:** Take the 2nd note from the top and drop it one octave, re-sort
- **Drop-3:** Take the 3rd note from the top and drop it one octave, re-sort

**Verified working approach:**
```python
notes = list(chord.pitches)  # bottom to top
# Drop-2: notes[-2] = notes[-2].transpose(-12), re-sort
# Drop-3: notes[-3] = notes[-3].transpose(-12), re-sort
```

**Edge cases:**
- Drop-2/drop-3 only makes sense for 4+ note chords. For triads: drop-2 works (3 notes), drop-3 would need at least 4 notes.
- If chord has fewer notes than the drop index, skip that voicing or return close position with a note.

### 1.4 Chord Identification (CHRD-04)

**Primary approach: `chord.Chord` from MIDI pitches:**

```python
c = chord.Chord([60, 64, 67])
c.pitchedCommonName  # "C-major triad"
c.root()             # Pitch('C4')
c.quality            # "major"
c.inversion()        # 0
```

**Ranked candidates (D-09):** music21 doesn't have a built-in ranking method. Strategy:
1. Primary identification via `pitchedCommonName` + `root()` + `quality`
2. Check for enharmonic reinterpretations (e.g., C6 vs Am7) by trying different roots
3. Score candidates by: root position preferred > inversions > enharmonic reinterpretation

**Incomplete chords (D-10):**
- Dyads work: `chord.Chord([60, 67])` → "Perfect Fifth above C", root C4
- Power chords (root + 5th): identified as intervals, not triads
- Missing 5th (root + 3rd): still identified with quality

**Inversion detection (D-11):**
- `c.inversion()` returns 0 (root), 1 (first), 2 (second), 3 (third)
- `c.bass()` returns the lowest pitch — use for "bass note" in output

### 1.5 Diatonic Chords (CHRD-05)

**Primary approach: `roman.RomanNumeral`:**

```python
from music21 import key, roman
k = key.Key('C')
rn = roman.RomanNumeral('I', k)
# pitchedCommonName: "C-major triad", pitches: ['C4','E4','G4']
```

**Triads (major key):** I, ii, iii, IV, V, vi, viio
**7th chords (major key):** I7, ii7, iii7, IV7, V7, vi7, viio7

**Minor key:** i, iio, III, iv, v, VI, VII (natural minor per D-14)
**7th chords (minor):** i7, iio7, III7, iv7, v7, VI7, VII7

**Roman numeral convention:** Uppercase = major, lowercase = minor, o = diminished

## 2. Existing Code Patterns

### 2.1 Lazy Import Pattern (from pitch.py)

```python
_chord_module = None
_harmony_module = None

def _get_chord_module():
    global _chord_module
    if _chord_module is None:
        from music21 import chord
        _chord_module = chord
    return _chord_module
```

Need lazy imports for: `chord`, `harmony`, `pitch`, `key`, `roman`

### 2.2 Rich Note Object Pattern (from Phase 14)

```python
{"midi": 60, "name": "C4"}
```

Reuse `_format_note_name()` from `pitch.py` for consistent name formatting. Reuse `_force_sharp()` for default sharp spelling.

### 2.3 Tool Pattern

```python
@mcp.tool()
def build_chord(ctx: Context, root: str, quality: str = "maj", octave: int = 4) -> str:
    try:
        # Validate at tool boundary (D-18)
        # Call library function
        result = _build_chord(root, quality, octave)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(...)
```

## 3. File Structure

### Library: `MCP_Server/theory/chords.py`
- `build_chord(root, quality, octave)` → dict with chord info + note objects
- `get_chord_inversions(root, quality, octave)` → list of inversion dicts
- `get_chord_voicings(root, quality, octave)` → dict of voicing type → note objects
- `identify_chord(midi_pitches)` → list of ranked candidate dicts
- `get_diatonic_chords(key_name, scale_type, octave)` → dict with triads + sevenths arrays

### Tools: `MCP_Server/tools/theory.py` (append 5 new tools)
- Each tool: validate inputs → call library function → json.dumps or format_error

### Exports: `MCP_Server/theory/__init__.py` (add chord function exports)

### Tests: `tests/test_theory.py` (add chord test section)
- Unit tests for each library function
- Integration tests via mcp_server fixture for each tool

## 4. Risk Areas

### 4.1 Quality String Mapping
The mapping from user-facing short symbols to ChordSymbol strings needs careful handling. Edge cases: `maj` should map to empty string (not "maj" which ChordSymbol may not accept). Need a lookup dict.

### 4.2 Voicing Implementation
Drop-2/drop-3 for triads: only drop-2 is meaningful (3 notes, 2nd from top exists). Drop-3 requires 4+ notes. Need graceful handling when voicing doesn't apply.

### 4.3 Ranked Identification
music21's `pitchedCommonName` gives one answer. Building ranked candidates requires:
1. Primary: direct identification
2. Try all possible roots from the pitch set, build chords, check if pitches match
3. Check for enharmonic equivalents

### 4.4 Octave Transposition
ChordSymbol places chords at its default octave. Need reliable transposition to target octave while preserving intervals.

## 5. Validation Architecture

### Test Cases per Requirement

**CHRD-01 (build_chord):**
- Major triad: root=C, quality=maj, octave=4 → [60, 64, 67]
- Minor 7th: root=A, quality=min7, octave=3 → [45, 48, 52, 55]
- Extended: root=G, quality=9, octave=4 → [67, 71, 74, 77, 81]
- Augmented: root=F#, quality=aug → pitches verified
- Invalid quality → format_error

**CHRD-02 (inversions):**
- C major triad: root=0 → [60,64,67], inv=1 → [64,67,72], inv=2 → [67,72,76]
- Cmaj7: 4 inversions (0,1,2,3)
- Verify inversion count = number of pitches

**CHRD-03 (voicings):**
- Cmaj7 close: [60,64,67,71]
- Cmaj7 drop-2: [55,60,64,71] (G3 dropped)
- Cmaj7 drop-3: [52,60,67,71] (E3 dropped)
- Triad: drop-3 gracefully handled (returns close or omitted)

**CHRD-04 (identify):**
- [60,64,67] → top candidate: C major triad, root position
- [64,67,72] → C major, 1st inversion, bass=E4
- [60,67] → dyad identification
- [57,60,64,67] → ranked: Am7 vs C6

**CHRD-05 (diatonic):**
- C major triads: I=Cmaj, ii=Dmin, iii=Emin, IV=Fmaj, V=Gmaj, vi=Amin, vii°=Bdim
- C major 7ths: verified roman numerals + pitches
- A minor triads: i, ii°, III, iv, v, VI, VII
