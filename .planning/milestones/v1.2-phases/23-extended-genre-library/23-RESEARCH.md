# Phase 23: Extended Genre Library - Research

**Researched:** 2026-03-26
**Domain:** Genre blueprint data authoring (pure Python dicts)
**Confidence:** HIGH

## Summary

Phase 23 is pure content authoring: create 4 new genre blueprint files (synthwave, lo-fi, future bass, disco/funk) following the exact pattern established in Phase 20 and extended in Phase 22. There is one breaking change -- removing the `lo_fi_hip_hop` subgenre from `hip_hop_trap.py` and updating its tests to reflect 2 subgenres instead of 3.

No new architecture, no new code patterns, no library additions. The catalog auto-discovers new `.py` files in the `MCP_Server/genres/` directory. The only risk is authoring errors: invalid chord types, invalid scale names, wrong dict structure, or alias collisions with existing genres.

**Primary recommendation:** Follow `house.py` as the canonical template exactly. Cross-validate every `chord_type` against `_QUALITY_MAP` (26 entries) and every `scale` name against `SCALE_CATALOG` (38 entries) before committing.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01: Synthwave** -- 4 subgenres: retrowave, darksynth, outrun, synthpop
- **D-02: Lo-fi** -- 3 subgenres: lo-fi hip-hop, chillhop, lo-fi jazz
- **D-03: Future Bass** -- 5 subgenres: kawaii future, melodic future bass, chill future bass, dark wave, hardwave
- **D-04: Disco/Funk** -- 4 subgenres: nu-disco, funk, boogie, electro funk
- **D-05:** Remove `lo_fi_hip_hop` subgenre from `hip_hop_trap.py`. Update hip-hop tests to no longer expect the `lo_fi_hip_hop` subgenre. The `lofi`, `lo-fi`, and `chillhop` aliases all move to the new lo-fi genre.
- **D-06:** Canonical genre ID: `disco_funk`. BPM ranges: base 100-130, funk 95-110, nu-disco 118-128, boogie 108-120, electro funk 100-118.
- **D-07:** Base genre ID: `future_bass`. Parent IS the canonical future bass sound (150-160 BPM). No "future bass" subgenre.
- **D-08:** All 4 genres match house.py depth exactly -- equal detail across all 6 dimensions.
- **D-09:** Tests validate all `chord_types` exist in `_QUALITY_MAP` and all `scale` names exist in `SCALE_CATALOG`.
- File naming: `synthwave.py`, `lo_fi.py`, `future_bass.py`, `disco_funk.py`

### Claude's Discretion
- Exact instrumentation roles per genre (following generic roles pattern)
- Specific chord progressions per genre (must use valid Roman numeral notation)
- Specific BPM values within established ranges
- Arrangement section structures (following bar counts pattern)
- Rhythm dimension details per genre
- Mixing dimension details per genre
- Production tips per genre

### Deferred Ideas (OUT OF SCOPE)
- EDM Trap as standalone genre -- belongs in GENR-13+ (future genre addition)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GENR-09 | Synthwave blueprint with subgenres (retrowave, darksynth, outrun) + synthpop | Template pattern from house.py; 4 subgenres per D-01; valid theory names verified below |
| GENR-10 | Lo-fi blueprint with subgenres (lo-fi hip-hop, chillhop) + lo-fi jazz | Requires hip_hop_trap.py modification per D-05; alias migration for lofi/chillhop |
| GENR-11 | Future Bass blueprint with subgenres (kawaii future + 4 more) | 5 subgenres per D-03; parent is canonical sound per D-07; wide BPM 150-160 base |
| GENR-12 | Disco/Funk blueprint with subgenres (nu-disco, funk, boogie) + electro funk | Hybrid genre per D-06; widest subgenre BPM divergence (95-130) |
</phase_requirements>

## Standard Stack

### Core
No new libraries. This phase is pure data authoring.

| Component | Path | Purpose | Why Standard |
|-----------|------|---------|--------------|
| Genre blueprint template | `MCP_Server/genres/house.py` | Canonical GENRE + SUBGENRES dict structure | All 8 existing genres follow this |
| Schema validation | `MCP_Server/genres/schema.py` | TypedDict + `validate_blueprint()` | Import-time validation |
| Auto-discovery | `MCP_Server/genres/catalog.py` | Registers new .py files automatically | No code changes needed |
| Test pattern | `tests/test_genres.py` | Per-genre test class pattern | TestHouseBlueprint as template |

### Theory Engine Cross-References

**Valid chord types (26):** maj, min, dim, aug, maj7, min7, dom7, 7, dim7, hdim7, min7b5, sus2, sus4, add9, 9, min9, maj9, 11, min11, 13, min13, 7b5, 7#5, 7b9, 7#9, 7#11

**Valid scale names (38):** major, natural_minor, chromatic, ionian, dorian, phrygian, lydian, mixolydian, aeolian, locrian, harmonic_minor, melodic_minor, major_pentatonic, minor_pentatonic, japanese, egyptian, blues, major_blues, blues_bebop, whole_tone, diminished_whole_half, diminished_half_whole, augmented, bebop_dominant, bebop_major, bebop_dorian, bebop_melodic_minor, hungarian_minor, persian, arabic, double_harmonic, enigmatic, neapolitan_major, neapolitan_minor, phrygian_dominant, lydian_dominant, super_locrian

## Architecture Patterns

### Genre File Structure (Mandatory)
```
MCP_Server/genres/
    synthwave.py       # NEW
    lo_fi.py           # NEW
    future_bass.py     # NEW
    disco_funk.py      # NEW
    hip_hop_trap.py    # MODIFIED (remove lo_fi_hip_hop subgenre)
```

### Pattern: Genre Blueprint File
**What:** Each file exports GENRE dict + SUBGENRES dict, no imports, pure data.
**When to use:** Every genre file.
**Example (from house.py):**
```python
"""Genre docstring."""

GENRE = {
    "name": "Display Name",
    "id": "snake_case_id",
    "bpm_range": [min, max],
    "aliases": ["alias1", "alias2"],
    "instrumentation": {"roles": [...]},
    "harmony": {
        "scales": [...],
        "chord_types": [...],
        "common_progressions": [[...], ...],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [min, max],
        "swing": "none|light|heavy",
        "note_values": [...],
        "drum_pattern": "description",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": N},
            ...
        ]
    },
    "mixing": {
        "frequency_focus": "...",
        "stereo_field": "...",
        "common_effects": [...],
        "compression_style": "...",
    },
    "production_tips": {
        "techniques": [...],
        "pitfalls": [...],
    },
}

SUBGENRES = {
    "subgenre_id": {
        "name": "Display Name",
        "bpm_range": [min, max],
        "aliases": ["alias1"],
        # Only override dimensions that differ from base
    },
}
```

### Pattern: Subgenre Override (Shallow Merge)
**What:** Subgenres only include dimensions that differ from the base genre. The catalog performs a shallow merge -- each top-level key in the subgenre replaces the base value entirely.
**Critical detail:** If a subgenre overrides `harmony`, it must include ALL harmony sub-keys (scales, chord_types, common_progressions), not just the ones that differ. The merge is per top-level key, not deep.

### Pattern: Test Class Per Genre
**What:** Each genre gets a test class with: schema validation, dimension completeness, subgenre count, chord type validation, scale name validation, alias resolution, subgenre discovery, and subgenre validation.
**Example (from TestTechnoBlueprint):**
```python
class TestSynthwaveBlueprint:
    """GENR-09: Synthwave blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.synthwave import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.synthwave import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE

    def test_subgenre_count(self):
        from MCP_Server.genres.synthwave import SUBGENRES
        assert len(SUBGENRES) == 4

    def test_chord_types_valid(self):
        from MCP_Server.genres.synthwave import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP

    def test_scale_names_valid(self):
        from MCP_Server.genres.synthwave import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG

    def test_aliases_resolve(self):
        assert resolve_alias("synthwave") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        sw = [g for g in genres if g["id"] == "synthwave"][0]
        assert set(sw["subgenres"]) == {"retrowave", "darksynth", "outrun", "synthpop"}

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["retrowave", "darksynth", "outrun", "synthpop"]:
            bp = get_blueprint("synthwave", subgenre=sub_id)
            validate_blueprint(bp)
```

### Anti-Patterns to Avoid
- **Adding imports to genre files:** Genre files are pure data -- no imports, no functions, no classes.
- **Deep-merging subgenre overrides:** The catalog does shallow merge. If you override `harmony`, include ALL sub-keys.
- **Using chord/scale names not in the theory engine:** Every name must be from the verified lists above.
- **Forgetting `bpm_range` in both GENRE top-level AND `rhythm` section:** Both are required by schema validation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Genre registration | Manual catalog entries | Auto-discovery in catalog.py | Just drop a .py file in genres/ |
| Schema validation | Per-field checks in tests | `validate_blueprint()` | Already validates all dimensions |
| Alias normalization | Custom string matching | `resolve_alias()` with `_normalize_alias()` | Handles case, spaces, hyphens |
| Subgenre merge | Manual dict copying | `get_blueprint(genre, subgenre=sub)` | Shallow merge already implemented |

## Common Pitfalls

### Pitfall 1: Alias Collisions
**What goes wrong:** New genre aliases collide with existing ones. For example, `lo_fi_hip_hop` currently aliases to hip_hop_trap -- if lo-fi genre also uses `lo_fi_hip_hop` as a subgenre ID, whichever module loads second wins.
**Why it happens:** The catalog iterates modules in pkgutil order and overwrites alias map entries.
**How to avoid:** D-05 explicitly removes `lo_fi_hip_hop` from hip_hop_trap.py BEFORE the lo-fi genre is added. The aliases `lofi`, `lo-fi`, `lo_fi`, and `chillhop` must move to the lo-fi genre. Verify no alias appears in two genre files.
**Warning signs:** Tests for hip_hop_trap aliases (`lofi`, `chillhop`) start failing.

### Pitfall 2: Invalid Theory Names
**What goes wrong:** Using a chord type like `min6` or a scale like `pentatonic` that does not exist in the theory engine.
**Why it happens:** Common music terminology differs from the engine's key names.
**How to avoid:** Cross-reference every chord_type and scale name against the verified lists in this document. The tests (D-09) catch this at test time.
**Warning signs:** `test_chord_types_valid` or `test_scale_names_valid` fails.

### Pitfall 3: Shallow Merge Incompleteness
**What goes wrong:** Subgenre overrides `harmony` but only includes `scales`, missing `chord_types` and `common_progressions`. After merge, the subgenre blueprint has an incomplete harmony section.
**Why it happens:** Expecting deep merge behavior.
**How to avoid:** When overriding any section, include ALL required sub-keys for that section. Check `_SECTION_SPEC` in schema.py for required fields per section.
**Warning signs:** `validate_blueprint()` raises ValueError on merged result.

### Pitfall 4: Forgetting to Update Tests for Hip-hop Modification
**What goes wrong:** Removing `lo_fi_hip_hop` from hip_hop_trap.py but not updating `TestHipHopTrapBlueprint` -- specifically `test_subgenre_count` (expects 3, should become 2), `test_subgenres_discovered` (expects set includes `lo_fi_hip_hop`), and `test_all_subgenres_pass_validation` (iterates over `lo_fi_hip_hop`).
**How to avoid:** Update all 3 test methods in TestHipHopTrapBlueprint simultaneously with the data change.

### Pitfall 5: Integration Test Count
**What goes wrong:** `TestAllGenresIntegration.test_eight_genres_total` currently asserts `len(genres) == 8`. After adding 4 genres it must assert 12. Similarly `test_all_genre_ids_present` must add the 4 new IDs to the expected set.
**How to avoid:** Update both integration tests to reflect 12 genres.

### Pitfall 6: BPM Range Consistency
**What goes wrong:** Top-level `bpm_range` says [100, 130] but `rhythm.bpm_range` says [100, 128]. Schema validates both exist and are `[int, int]` but does not check they match.
**How to avoid:** Keep top-level `bpm_range` and `rhythm.bpm_range` identical for the base genre. Subgenres should have matching values in both locations if they override either.

## Code Examples

### New Genre File Template (Synthwave)
```python
"""Synthwave genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

Synthwave with four subgenres: retrowave, darksynth, outrun, and synthpop.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Synthwave",
    "id": "synthwave",
    "bpm_range": [80, 130],
    "aliases": ["synthwave", "synth wave", "retro synth"],
    # ... all 6 dimensions ...
}

SUBGENRES = {
    "retrowave": {
        "name": "Retrowave",
        "bpm_range": [95, 120],
        "aliases": ["retrowave", "retro wave"],
        # override only dimensions that differ
    },
    "darksynth": { ... },
    "outrun": { ... },
    "synthpop": { ... },
}
```

### Hip-hop Modification (D-05)
```python
# BEFORE (hip_hop_trap.py):
SUBGENRES = {
    "boom_bap": { ... },
    "trap": { ... },
    "lo_fi_hip_hop": { ... },  # REMOVE THIS ENTIRE ENTRY
}

# AFTER:
SUBGENRES = {
    "boom_bap": { ... },
    "trap": { ... },
}
```

Also remove from GENRE aliases any that conflict: `lofi`, `lo_fi`, `lo-fi hip-hop`, `lo-fi hip hop`, `chillhop` -- check current aliases list carefully. Currently hip_hop_trap GENRE aliases are: `["hip hop", "hiphop", "hip_hop", "trap", "rap"]` -- none of those conflict. The conflict is in the `lo_fi_hip_hop` subgenre's aliases: `["lo-fi hip hop", "lofi", "lo_fi", "lo-fi hip-hop", "chillhop"]`. Removing the entire subgenre entry removes all these alias registrations.

### Test Modifications Required
```python
# TestHipHopTrapBlueprint changes:
def test_subgenre_count(self):
    from MCP_Server.genres.hip_hop_trap import SUBGENRES
    assert len(SUBGENRES) == 2  # was 3

def test_subgenres_discovered(self):
    genres = list_genres()
    hip_hop = [g for g in genres if g["id"] == "hip_hop_trap"][0]
    assert set(hip_hop["subgenres"]) == {"boom_bap", "trap"}  # removed lo_fi_hip_hop

def test_all_subgenres_pass_validation(self):
    for sub_id in ["boom_bap", "trap"]:  # removed lo_fi_hip_hop
        bp = get_blueprint("hip_hop_trap", subgenre=sub_id)
        validate_blueprint(bp)

# TestAllGenresIntegration changes:
def test_eight_genres_total(self):  # rename to test_twelve_genres_total
    genres = list_genres()
    assert len(genres) == 12  # was 8

def test_all_genre_ids_present(self):
    genres = list_genres()
    ids = {g["id"] for g in genres}
    expected = {
        "house", "techno", "hip_hop_trap", "ambient",
        "drum_and_bass", "dubstep", "trance", "neo_soul_rnb",
        "synthwave", "lo_fi", "future_bass", "disco_funk",  # NEW
    }
    assert ids == expected
```

## Genre-Specific Research Notes

### Synthwave (GENR-09)
- **BPM:** Base ~80-130 (wide range covering slow retrowave to energetic outrun)
- **Scales:** major, natural_minor, dorian, mixolydian (bright 80s tonality)
- **Chord types:** maj, min, maj7, min7, sus4, add9 (clean, bright voicings)
- **Key instruments:** analog synth pad, bass synth, arpeggiated lead, drum machine, gated reverb snare
- **Subgenre BPM ranges:** retrowave 95-120, darksynth 100-130, outrun 110-130, synthpop 100-125

### Lo-fi (GENR-10)
- **BPM:** Base ~60-95 (slow, relaxed tempos)
- **Scales:** dorian, natural_minor, mixolydian, major (jazzy, warm tonality)
- **Chord types:** min7, maj7, min9, maj9, dom7, add9, 9 (extended jazz chords for warmth)
- **Key instruments:** vinyl noise, piano/keys, bass, guitar, drums, sample, pad, fx
- **Subgenre BPM ranges:** lo-fi hip-hop 70-90, chillhop 75-95, lo-fi jazz 60-85
- **CRITICAL:** The `lofi`, `lo_fi`, `lo-fi`, `chillhop` aliases previously belonged to hip_hop_trap's lo_fi_hip_hop subgenre. They MUST move here.

### Future Bass (GENR-11)
- **BPM:** Base 150-160 (half-time feel making it sound ~75-80)
- **Scales:** major, natural_minor, lydian, mixolydian (bright, emotional)
- **Chord types:** maj7, min7, maj9, min9, sus4, add9, 7 (lush, emotional voicings)
- **Key instruments:** supersaw, bass, kick, snare, hi-hats, vocal chop, pad, pluck, fx
- **5 subgenres (most of any P2 genre):** kawaii_future, melodic_future_bass, chill_future_bass, dark_wave, hardwave

### Disco/Funk (GENR-12)
- **BPM:** Base 100-130 (wide range for hybrid genre)
- **Scales:** major, dorian, mixolydian, minor_pentatonic (groove-forward)
- **Chord types:** dom7, min7, maj7, 9, min9, 13 (funk extensions, 9ths and 13ths)
- **Key instruments:** bass guitar, rhythm guitar, kick, snare, hi-hats, brass, strings, keys, clav, percussion
- **Subgenre BPM ranges:** funk 95-110, nu-disco 118-128, boogie 108-120, electro funk 100-118

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pyproject.toml` or `pytest.ini` |
| Quick run command | `python -m pytest tests/test_genres.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GENR-09 | Synthwave blueprint schema + subgenres + theory names | unit | `python -m pytest tests/test_genres.py::TestSynthwaveBlueprint -x` | Wave 0 |
| GENR-10 | Lo-fi blueprint schema + subgenres + theory names + alias migration | unit | `python -m pytest tests/test_genres.py::TestLoFiBlueprint -x` | Wave 0 |
| GENR-11 | Future bass blueprint schema + subgenres + theory names | unit | `python -m pytest tests/test_genres.py::TestFutureBassBlueprint -x` | Wave 0 |
| GENR-12 | Disco/funk blueprint schema + subgenres + theory names | unit | `python -m pytest tests/test_genres.py::TestDiscoFunkBlueprint -x` | Wave 0 |
| D-05 | Hip-hop lo_fi_hip_hop removed, tests updated | unit | `python -m pytest tests/test_genres.py::TestHipHopTrapBlueprint -x` | Exists (needs update) |
| Integration | 12 genres total, all IDs present, all aliases resolve | unit | `python -m pytest tests/test_genres.py::TestAllGenresIntegration -x` | Exists (needs update) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_genres.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `TestSynthwaveBlueprint` class in `tests/test_genres.py` -- covers GENR-09
- [ ] `TestLoFiBlueprint` class in `tests/test_genres.py` -- covers GENR-10
- [ ] `TestFutureBassBlueprint` class in `tests/test_genres.py` -- covers GENR-11
- [ ] `TestDiscoFunkBlueprint` class in `tests/test_genres.py` -- covers GENR-12
- [ ] Update `TestHipHopTrapBlueprint` -- 3 methods need count/set/iteration changes
- [ ] Update `TestAllGenresIntegration` -- count from 8 to 12, add 4 new genre IDs

## Sources

### Primary (HIGH confidence)
- `MCP_Server/genres/house.py` -- canonical genre template (read directly)
- `MCP_Server/genres/schema.py` -- schema TypedDicts and validation (read directly)
- `MCP_Server/genres/hip_hop_trap.py` -- file to modify, lo_fi_hip_hop subgenre at lines 161-209 (read directly)
- `MCP_Server/genres/catalog.py` -- auto-discovery, alias resolution, shallow merge (read directly)
- `MCP_Server/theory/chords.py` -- `_QUALITY_MAP` with 26 chord types (read directly)
- `MCP_Server/theory/scales.py` -- `SCALE_CATALOG` with 38 scale names (read directly)
- `tests/test_genres.py` -- existing test patterns for 8 genres (read directly)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all patterns established in prior phases, code read directly
- Architecture: HIGH -- pure template replication, no new patterns needed
- Pitfalls: HIGH -- identified from code analysis of shallow merge, alias map, and test assertions

**Research date:** 2026-03-26
**Valid until:** Indefinite (pure data authoring against stable schema)
