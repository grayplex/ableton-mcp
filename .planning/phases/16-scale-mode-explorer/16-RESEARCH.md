# Phase 16: Scale & Mode Explorer - Research

**Researched:** 2026-03-24
**Phase:** 16
**Requirements:** SCLE-01, SCLE-02, SCLE-03, SCLE-04, SCLE-05

## 1. music21 Scale API Analysis

### Available Scale Classes

music21 provides these built-in scale classes via `music21.scale`:

**Direct class support:**
- `MajorScale`, `MinorScale` (natural minor), `HarmonicMinorScale`, `MelodicMinorScale`
- `DorianScale`, `PhrygianScale`, `LydianScale`, `MixolydianScale`, `LocrianScale`
- `WholeToneScale`, `ChromaticScale`, `OctatonicScale` (diminished)

**Not directly available as named classes — need custom construction:**
- Pentatonic scales (major/minor) — build via `AbstractScale` with intervals [2,2,3,2,3] / [3,2,2,3,2]
- Blues scale — `AbstractScale` with [3,2,1,1,3,2]
- Bebop scales — custom intervals
- Other exotic scales

### Key music21 API methods:
- `scale.getPitches(minPitch, maxPitch)` — returns pitches within range
- `scale.pitches` — returns one octave of pitches
- `scale.getRelativeMinor()` / `scale.getRelativeMajor()` — for relative key relationships
- `scale.abstract.getIntervalObjectList()` — get interval objects
- Pitch class: `pitch.midi % 12` for pitch class comparison

### Scale Construction Approaches

**For built-in scales:** Direct instantiation:
```python
from music21 import scale
s = scale.MajorScale('C')
pitches = s.getPitches('C4', 'C6')  # multi-octave
```

**For custom scales:** Use interval-based construction:
```python
from music21 import scale, interval
intervals = [interval.Interval(s) for s in ['M2', 'M2', 'm3', 'M2', 'm3']]
abstract = scale.AbstractScale()
abstract.buildNetworkFromIntervals(intervals)
# Then derive concrete pitches from a root
```

Alternative for custom scales — build from pitch list:
```python
from music21 import pitch, scale
p = pitch.Pitch('C4')
pitches_list = [p]
for semitones in [2, 2, 3, 2, 3]:
    p = p.transpose(semitones)
    pitches_list.append(p)
```

**Recommended approach:** Use a hybrid strategy:
1. Map scale names to music21 classes where available
2. For scales without music21 classes, store semitone interval patterns and construct pitches manually
3. This avoids the complexity of `AbstractScale.buildNetworkFromIntervals()` while still leveraging music21's pitch objects

## 2. Curated Scale Catalog Design

### Proposed 38-Scale Catalog (7 categories)

**Diatonic (3):**
- `major` → MajorScale — [2,2,1,2,2,2,1]
- `natural_minor` → MinorScale — [2,1,2,2,1,2,2]
- `chromatic` → ChromaticScale — [1,1,1,1,1,1,1,1,1,1,1,1]

**Modal (7):**
- `ionian` → MajorScale — [2,2,1,2,2,2,1] (same as major)
- `dorian` → DorianScale — [2,1,2,2,2,1,2]
- `phrygian` → PhrygianScale — [1,2,2,2,1,2,2]
- `lydian` → LydianScale — [2,2,2,1,2,2,1]
- `mixolydian` → MixolydianScale — [2,2,1,2,2,1,2]
- `aeolian` → MinorScale — [2,1,2,2,1,2,2] (same as natural minor)
- `locrian` → LocrianScale — [1,2,2,1,2,2,2]

**Minor Variants (3):**
- `harmonic_minor` → HarmonicMinorScale — [2,1,2,2,1,3,1]
- `melodic_minor` → MelodicMinorScale — [2,1,2,2,2,2,1] (ascending form)
- `dorian_b2` → custom — [1,2,2,2,2,1,2]

**Pentatonic (4):**
- `major_pentatonic` → custom — [2,2,3,2,3]
- `minor_pentatonic` → custom — [3,2,2,3,2]
- `japanese` → custom — [1,4,2,1,4] (in scale)
- `egyptian` → custom — [2,3,2,3,2]

**Blues (3):**
- `blues` → custom — [3,2,1,1,3,2]
- `major_blues` → custom — [2,1,1,3,2,3]
- `blues_bebop` → custom — [3,2,1,1,1,2,2] (8 notes)

**Symmetric (4):**
- `whole_tone` → WholeToneScale — [2,2,2,2,2,2]
- `diminished_whole_half` → OctatonicScale (WH) — [2,1,2,1,2,1,2,1]
- `diminished_half_whole` → OctatonicScale (HW) — [1,2,1,2,1,2,1,2]
- `augmented` → custom — [3,1,3,1,3,1]

**Bebop (4):**
- `bebop_dominant` → custom — [2,2,1,2,2,1,1,1]
- `bebop_major` → custom — [2,2,1,2,1,1,2,1]
- `bebop_dorian` → custom — [2,1,1,1,2,2,1,2]
- `bebop_melodic_minor` → custom — [2,1,2,2,1,1,1,2]

**World/Other (10):**
- `hungarian_minor` → custom — [2,1,3,1,1,3,1]
- `persian` → custom — [1,3,1,1,2,3,1]
- `arabic` → custom — [1,3,1,2,1,3,1]
- `double_harmonic` → custom — [1,3,1,2,1,3,1] (same as arabic/byzantine)
- `enigmatic` → custom — [1,3,2,2,2,1,1]
- `neapolitan_major` → custom — [1,2,2,2,2,2,1]
- `neapolitan_minor` → custom — [1,2,2,2,1,3,1]
- `phrygian_dominant` → custom — [1,3,1,2,1,2,2]
- `lydian_dominant` → custom — [2,2,2,1,2,1,2]
- `super_locrian` → custom — [1,2,1,2,2,2,2] (altered scale)

**Total: 38 scales across 7 categories**

### Implementation: Scale Registry

A dict-based registry mapping scale names to their properties:
```python
SCALE_CATALOG = {
    "major": {
        "intervals": [2, 2, 1, 2, 2, 2, 1],
        "category": "diatonic",
        "music21_class": "MajorScale",  # or None for custom
        "aliases": ["ionian"],
    },
    ...
}
```

For `list_scales`, iterate the catalog and return name, intervals, category.

## 3. Tool Implementation Strategy

### SCLE-01: list_scales
- Return the full curated catalog
- Each entry: `{"name": str, "intervals": [int, ...], "category": str, "note_count": int}`
- No parameters needed (static catalog)

### SCLE-02: get_scale_pitches
- Parameters: `root` (str), `scale_name` (str), `octave_start` (int, default 4), `octave_end` (int, default 5)
- Use music21 class if available, otherwise construct from intervals
- Return: `{"root": str, "scale": str, "pitches": [{"midi": int, "name": str}, ...]}`
- Apply `_force_sharp()` for consistent naming

### SCLE-03: check_notes_in_scale
- Parameters: `midi_pitches` (list[int]), `root` (str), `scale_name` (str)
- Generate scale pitch classes, compare against input pitch classes
- Return: `{"scale": str, "root": str, "in_scale": [note_obj], "out_of_scale": [note_obj], "all_in_scale": bool}`

### SCLE-04: get_related_scales
- Parameters: `root` (str), `scale_name` (str)
- Compute:
  - **Parallel:** Same root, curated list of parallel scales (major/minor/harmonic minor/melodic minor + modes)
  - **Relative:** For major→relative minor, minor→relative major (shift root by appropriate interval)
  - **Modes:** Rotate intervals of parent scale to generate all modes
- Return grouped dict: `{"parallel": [...], "relative": [...], "modes": [...]}`

### SCLE-05: detect_scales_from_notes
- Parameters: `midi_pitches` (list[int])
- Algorithm:
  1. Extract pitch classes from input
  2. For each scale in catalog, for each of 12 possible roots:
     - Generate scale pitch classes
     - Calculate coverage = len(input_pcs & scale_pcs) / len(input_pcs)
  3. Rank by coverage (primary), simplicity tiebreak (secondary)
  4. Return top 5
- Simplicity ranking: major/minor > modes > pentatonic > blues > symmetric > bebop > world
- Return: `[{"root": str, "scale": str, "coverage": float, "matched_notes": int, "total_notes": int}, ...]`

## 4. Extending get_diatonic_chords

### Current Implementation
`get_diatonic_chords(key_name, scale_type="major", octave=4)` in `chords.py`
- Currently supports: `"major"` and `"minor"` (natural minor)
- Uses `key_mod.Key()` + `roman_mod.RomanNumeral()`

### Extension for Harmonic/Melodic Minor
Add `"harmonic_minor"` and `"melodic_minor"` to `scale_type` options.

**music21 approach:** Use `key.Key()` with mode parameter:
- `key.Key('C', 'major')` — already works
- `key.Key('C', 'minor')` — natural minor, already works
- For harmonic minor: construct scale manually, build chords on each degree
- For melodic minor: use ascending form, build chords on each degree

**Roman numeral templates:**
- Harmonic minor: i, ii°, III+, iv, V, VI, vii°
- Harmonic minor 7ths: imaj7, iim7b5, III+maj7, ivm7, V7, VImaj7, viio7
- Melodic minor: i, ii, III+, IV, V, vi°, vii°
- Melodic minor 7ths: imaj7, iim7, III+maj7, IV7, V7, vim7b5, viim7b5

**Implementation:** Add conditional branches in `get_diatonic_chords` for `scale_type` in `("harmonic_minor", "melodic_minor")` with appropriate Roman numeral templates. Use `music21.roman.RomanNumeral` with the appropriate key/scale context.

## 5. Integration Points

### Files to Create
- `MCP_Server/theory/scales.py` — Scale library module (5 functions + catalog)

### Files to Modify
- `MCP_Server/theory/__init__.py` — Add scale function barrel exports
- `MCP_Server/theory/chords.py` — Extend `get_diatonic_chords` for harmonic/melodic minor
- `MCP_Server/tools/theory.py` — Add 5 new @mcp.tool() functions + update get_diatonic_chords tool
- `tests/test_theory.py` — Add scale tests (unit + integration)

### Patterns to Follow
- Lazy music21 imports via `_get_X_module()` pattern (from pitch.py, chords.py)
- `_make_note_obj(p)` for rich note objects (from chords.py)
- `_force_sharp(p)` for consistent naming (from pitch.py)
- Aliased imports in tools.py (e.g., `from MCP_Server.theory import list_scales as _list_scales`)
- MIDI validation at tool boundary, not library level

## 6. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| music21 doesn't have all 38 scales as classes | Medium | Interval-based construction for custom scales — avoids dependency on music21 class coverage |
| Melodic minor ascending vs descending | Low | Use ascending form (jazz convention, standard for harmony) — document in tool description |
| Scale detection with few notes (e.g., 2-3) is ambiguous | Low | Top-5 ranking handles ambiguity; coverage % makes uncertainty visible |
| Performance of detect_scales across 38 scales × 12 roots | Low | 456 comparisons on pitch class sets — trivially fast |
| Extending get_diatonic_chords may break existing tests | Medium | Keep "major"/"minor" behavior identical; add new cases only for new scale_type values |

## Validation Architecture

### SCLE-01 Validation
- list_scales returns 38 scales with name, intervals, category, note_count
- Every interval list sums correctly (e.g., major sums to 12 semitones)
- All 7 categories represented

### SCLE-02 Validation
- get_scale_pitches("C", "major", 4, 5) returns C4 through C5 as 8 pitches
- All returned pitches are rich note objects with midi and name
- MIDI values are within requested octave range

### SCLE-03 Validation
- check_notes_in_scale([60,64,67], "C", "major") → all_in_scale: true
- check_notes_in_scale([60,63,67], "C", "major") → Eb out of scale

### SCLE-04 Validation
- get_related_scales("C", "major") includes relative: A minor
- get_related_scales("C", "major") modes include Dorian, Phrygian, etc.
- Output grouped in {"parallel": [...], "relative": [...], "modes": [...]}

### SCLE-05 Validation
- detect_scales_from_notes([60,62,64,65,67,69,71]) → C major at top with 100% coverage
- Returns top 5 ranked candidates
- Coverage percentages are accurate

---

## RESEARCH COMPLETE

Research covers all 5 SCLE requirements with concrete implementation strategy, music21 API usage, 38-scale catalog design, and get_diatonic_chords extension plan.
