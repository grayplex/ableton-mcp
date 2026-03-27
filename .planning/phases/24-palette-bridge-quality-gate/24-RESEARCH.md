# Phase 24: Palette Bridge & Quality Gate - Research

**Researched:** 2026-03-27
**Phase Goal:** Claude can get key-resolved chords, scales, and progressions from any genre, and all blueprints meet quality standards
**Requirements:** TOOL-03, QUAL-01, QUAL-02, QUAL-03

## Key Findings

### 1. Blueprint Harmony Structure

All 12 genres follow identical harmony format (`MCP_Server/genres/house.py:22-31`):

```python
"harmony": {
    "scales": ["natural_minor", "dorian", "mixolydian", "major"],
    "chord_types": ["min7", "maj7", "dom7", "min9", "sus4", "add9"],
    "common_progressions": [
        ["i", "iv"],
        ["i", "bVII", "iv"],
        ["ii", "V", "I"],
        ["i", "bVI", "bVII"],
    ],
},
```

Three fields: `scales` (list of scale name strings), `chord_types` (list of chord quality symbols), `common_progressions` (list of lists of Roman numeral strings). Roman numerals use uppercase=major, lowercase=minor, `b` prefix for flats, optional quality suffixes (`ii7`, `V7b5`).

### 2. Theory Engine Resolution Functions

**`build_chord(root, quality, octave=4)`** — `chords.py:111-179`
- Input: root note name ("C", "F#"), quality symbol ("min7", "dom7"), octave
- Returns: `{"root": str, "quality": str, "notes": [{"midi": int, "name": str}, ...]}`
- For palette bridge: only need `root` and `quality` from return (names, not MIDI per D-02)

**`get_scale_pitches(root, scale_name, octave_start=4, octave_end=5)`** — `scales.py:302-341`
- Input: root note, scale name from SCALE_CATALOG
- Returns: `{"root": str, "scale": str, "pitches": [{"midi": int, "name": str}, ...]}`
- For palette bridge: only need `root` and `scale` (name resolution per D-02)

**`generate_progression(key, numerals, scale_type="major", octave=4)`** — `progressions.py:340-399`
- Input: key root, list of Roman numeral strings, scale type
- Returns: `{"key": str, "scale_type": str, "chords": [{"numeral": str, "root": str, "quality": str, "notes": [...]}, ...]}`
- For palette bridge: extract chord names from `root` + `quality` per chord (D-03)
- **Important**: This function does voice leading internally. For name resolution only, we may want to resolve numerals without full MIDI generation.

### 3. Palette Bridge Design

**Approach**: Read blueprint harmony → resolve each field against theory engine → return names only.

**For `scales`**: Each scale name (e.g., "dorian") + key → "C dorian". Simple string concatenation — no need to call `get_scale_pitches()` unless we want validation. For validation, check `scale_name in SCALE_CATALOG`.

**For `chord_types`**: Each quality (e.g., "min7") + key → "Cmin7". Can use `build_chord()` for validation, but for name-only output, can construct the name string directly. For validation, check `quality in _QUALITY_MAP`.

**For `common_progressions`**: Each progression (e.g., `["i", "bVII", "iv"]`) + key → `["Cmin", "Bbmaj", "Fmin"]`. **Must** call `generate_progression()` or equivalent resolution to correctly map Roman numerals to chord names. The `_resolve_numeral_to_chord()` internal function (`progressions.py:159-247`) does this, but it's not exported. Options:
1. Call `generate_progression()` and extract chord names from the result
2. Build a lightweight numeral resolver that doesn't generate MIDI

Option 1 is simpler and reuses existing tested code. The MIDI data is computed but discarded — acceptable since this is a single tool call, not a hot path.

### 4. Supported Theory Types

**24 chord qualities** (`_QUALITY_MAP` at `chords.py:64-91`):
`maj, min, dim, aug, maj7, min7, dom7, 7, dim7, hdim7, min7b5, sus2, sus4, add9, 9, min9, maj9, 11, min11, 13, min13, 7b5, 7#5, 7b9, 7#9, 7#11`

**38 scales** (`SCALE_CATALOG` at `scales.py:11-248`):
- Diatonic: major, natural_minor, chromatic
- Modal: ionian, dorian, phrygian, lydian, mixolydian, aeolian, locrian
- Minor variants: harmonic_minor, melodic_minor, dorian_b2
- Pentatonic: major_pentatonic, minor_pentatonic, japanese, egyptian
- Blues: blues, major_blues, blues_bebop
- Symmetric: whole_tone, diminished_whole_half, diminished_half_whole, augmented
- Bebop: bebop_dominant, bebop_major, bebop_dorian, bebop_melodic_minor
- World: hungarian_minor, persian, arabic, double_harmonic, enigmatic, neapolitan_major, neapolitan_minor, phrygian_dominant, lydian_dominant, super_locrian

### 5. Existing Tool Pattern

**File**: `MCP_Server/tools/genres.py` (78 lines)

Pattern: `@mcp.tool()` decorator, `ctx: Context` first param, `-> str` return type, `json.dumps()` for success, `format_error()` for errors. Imports from `MCP_Server.genres` and `MCP_Server.connection`.

Constants: `META_KEYS = {"id", "name", "bpm_range"}`, `SECTION_KEYS = {"instrumentation", "harmony", ...}`

New `get_genre_palette` tool fits naturally in this file.

### 6. Test Patterns

**File**: `tests/test_genres.py`

Per-genre test classes (e.g., `TestHouseBlueprint`) validate:
- Schema compliance
- All 6 dimensions present
- `chord_types` in `_QUALITY_MAP`
- `scales` in `SCALE_CATALOG`
- Subgenre validation

For centralized cross-validation (D-08), iterate `list_genres()` + subgenres, collecting all harmony fields, checking against theory engine types in one sweep.

### 7. Token Budget Infrastructure

**tiktoken** is NOT in `pyproject.toml`. Needs to be added as dev dependency:
```toml
dev = [
    "tiktoken>=0.7",  # Token counting for QUAL-01
    ...
]
```

Token measurement: `tiktoken.get_encoding("cl100k_base").encode(json.dumps(blueprint))` → len gives token count.

### 8. Progression Resolution Challenge

Blueprints store progressions as Roman numerals relative to a mode. Example: house uses `["i", "iv"]` (minor context). When resolving in key of C:
- If first scale is "natural_minor" → `i` = Cmin, `iv` = Fmin
- If first scale is "major" → different resolution

**Question**: Which scale_type to use for progression resolution? Options:
1. Use the first scale in the blueprint's `scales` list as the resolution context
2. Infer from Roman numeral case: lowercase `i` = minor key, uppercase `I` = major key
3. Always resolve against "major" (Roman numerals are key-relative)

Option 3 is correct: Roman numerals ARE the scale-degree mapping. `i` means "minor chord on degree 1" regardless of mode. The `generate_progression()` function handles this — it accepts `scale_type` and resolves numerals relative to that scale.

**Recommendation**: Default to "major" scale_type for resolution (standard Roman numeral analysis), but if the blueprint's progressions use predominantly lowercase (minor key context), use "natural_minor". A heuristic: if the first numeral is lowercase `i`, resolve in minor.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `generate_progression()` may fail on some Roman numerals in blueprints | Palette returns partial results | D-04: graceful degradation with unresolved list |
| Token budget exceeded by some genres | Test failures | D-07: soft cap with per-genre override |
| tiktoken version incompatibility | Build failures | Pin to stable version, dev-only dependency |

## Validation Architecture

### Test Categories for QUAL-03

1. **Palette bridge correctness**: Call `get_genre_palette("house", "C")` → verify chord names, scale names, progression resolution
2. **Cross-genre palette**: Call palette for multiple genres with different keys → verify structure consistency
3. **Error handling**: Invalid genre, invalid key → verify graceful error responses
4. **Unresolved names**: If a blueprint has an unsupported type → verify partial results + unresolved list
5. **Centralized cross-validation**: Iterate all genres/subgenres → validate all chord_types and scale_names against theory engine
6. **Token budget**: Measure all 12 genres → assert within budget (with per-genre overrides)

## RESEARCH COMPLETE
