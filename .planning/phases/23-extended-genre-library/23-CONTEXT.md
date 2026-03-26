# Phase 23: Extended Genre Library - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

4 new genre blueprint data files — synthwave, lo-fi, future bass, disco/funk — completing the P2 tier. Pure content authoring following the exact pattern established in Phase 22. Includes one breaking change to an existing blueprint: `lo_fi_hip_hop` subgenre removed from `hip_hop_trap.py` (moved to standalone lo-fi genre). No new code architecture.

</domain>

<decisions>
## Implementation Decisions

### Subgenre Selection

**D-01: Synthwave** — 4 subgenres: retrowave (spec), darksynth (spec), outrun (spec), **synthpop** (added — more vocal/pop-forward, Gary Numan / Depeche Mode adjacent)

**D-02: Lo-fi** — 3 subgenres: lo-fi hip-hop (spec), chillhop (spec), **lo-fi jazz** (added — jazz samples + lo-fi textures, Blue Note aesthetic, slower/more harmonic than chillhop)

**D-03: Future Bass** — 5 subgenres: kawaii future (spec), **melodic future bass** (Illenium/Seven Lions, emotional/festival-oriented), **chill future bass** (88rising territory, mellow drops, laid-back), **dark wave** (SXLND/Whyte Fang, slowed, gloomy atmosphere), **hardwave** (Hex Cougar/Heimanu, high-energy, distorted basses, aggressive but melodic)

**D-04: Disco/Funk** — 4 subgenres: nu-disco (spec), funk (spec), boogie (spec), **electro funk** (added — Zapp/Talk Talk style, synth-driven, vocoder-heavy)

### Lo-fi Naming Conflict Resolution
**D-05:** Remove `lo_fi_hip_hop` subgenre from `hip_hop_trap.py` — lo-fi is now a standalone peer genre, not a hip-hop subgenre. Update hip-hop tests to no longer expect the `lo_fi_hip_hop` subgenre. The `lofi`, `lo-fi`, and `chillhop` aliases all move to the new lo-fi genre.

### Disco/Funk Genre Identity
**D-06:** Canonical genre ID: `disco_funk`. Hybrid parent genre covers the overlap zone (four-on-the-floor, syncopated bass, live orchestration feel). BPM: wide range 100-130 in base genre; subgenres tighten it: funk 95-110, nu-disco 118-128, boogie 108-120, electro funk 100-118.

### Future Bass Genre Identity
**D-07:** Base genre ID: `future_bass`. The parent genre covers the Flume/San Holo core sound (150-160 BPM, supersaw chords, emotional buildups, heavy sidechain). The "future bass" subgenre name is not used as a subgenre — the parent IS the canonical future bass sound.

### Content Depth & Theory Validation
**D-08:** All 4 genres match house.py depth exactly — equal detail across all 6 dimensions (inherited from Phase 22 D-08)
**D-09:** Each genre's tests validate that all `chord_types` exist in `_QUALITY_MAP` and all `scale` names exist in `SCALE_CATALOG` — catching mistakes at authoring time (inherited from Phase 22 D-09)

### Claude's Discretion
- Exact instrumentation roles per genre (following generic roles pattern from Phase 20 D-11)
- Specific chord progressions per genre (must use valid Roman numeral notation)
- Specific BPM values within the ranges established above
- Arrangement section structures (following bar counts pattern from Phase 20 D-12)
- Rhythm dimension details per genre
- Mixing dimension details per genre
- Production tips per genre
- File naming: `synthwave.py`, `lo_fi.py`, `future_bass.py`, `disco_funk.py`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Reference Implementation
- `MCP_Server/genres/house.py` — Canonical genre blueprint template. ALL 4 new genres must match this structure exactly
- `MCP_Server/genres/schema.py` — TypedDict definitions and `validate_blueprint()` function

### Existing Genre to Modify
- `MCP_Server/genres/hip_hop_trap.py` — Remove `lo_fi_hip_hop` subgenre (D-05). Existing file must be edited.

### Theory Engine (for D-09 validation)
- `MCP_Server/theory/chords.py` — `_QUALITY_MAP` dict (26 chord qualities): maj, min, dim, aug, maj7, min7, dom7, 7, dim7, hdim7, min7b5, sus2, sus4, add9, 9, min9, maj9, 11, min11, 13, min13, 7b5, 7#5, 7b9, 7#9, 7#11
- `MCP_Server/theory/scales.py` — `SCALE_CATALOG` dict (38 scales): major, natural_minor, dorian, phrygian, lydian, mixolydian, aeolian, locrian, harmonic_minor, melodic_minor, major_pentatonic, minor_pentatonic, blues, + 23 more

### Infrastructure
- `MCP_Server/genres/catalog.py` — Auto-discovery, alias resolution, subgenre merge
- `tests/test_genres.py` — Existing genre test patterns (modify for lo-fi hip-hop removal)

### Requirements
- `.planning/REQUIREMENTS.md` — GENR-09 through GENR-12 for this phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/genres/house.py` — Exact template to follow: GENRE dict with all 6 dimensions + SUBGENRES dict
- `MCP_Server/genres/catalog.py` — Auto-discovers new genre files without any code changes needed
- `MCP_Server/genres/hip_hop_trap.py` — Must be edited: remove `lo_fi_hip_hop` from SUBGENRES dict
- `tests/test_genres.py` — TestHouseBlueprint and TestHipHopTrapBlueprint class patterns for per-genre validation tests

### Established Patterns
- Genre file: module docstring → GENRE dict → SUBGENRES dict, no imports, pure data
- Subgenre overrides: only dimensions that differ from base (BPM, harmony, arrangement)
- Aliases: include common alternate names and abbreviations
- Tests: schema validation + completeness + theory name cross-validation

### Integration Points
- No catalog code changes needed — catalog auto-discovers new .py files in `MCP_Server/genres/`
- New genres appear automatically in `list_genre_blueprints` output
- Removing lo_fi_hip_hop from hip_hop_trap.py will cause existing tests referencing it to fail — those tests must be updated in the same phase

</code_context>

<specifics>
## Specific Ideas

- Hardwave subgenre of future bass: Hex Cougar, Heimanu — high-energy, distorted basses, aggressive but still melodic. Distinct from dark wave (which is slower/gloomier)
- Dark wave subgenre of future bass: SXLND, Whyte Fang — slowed, gloomy, atmospheric
- Chill future bass: 88rising territory (Higher Brothers, Joji-adjacent productions) — mellow drops, laid-back energy
- Lo-fi jazz: Blue Note aesthetic, jazz samples + lo-fi textures, slower and more harmonically rich than standard chillhop
- Disco/funk base identity: four-on-the-floor kick, syncopated bass, live feel — subgenres diverge into modern electronic (nu-disco), raw groove (funk), '80s synth-pop (boogie), vocoder-heavy (electro funk)

</specifics>

<deferred>
## Deferred Ideas

- **EDM Trap as standalone genre** — already deferred from Phase 22 (Hex Cougar/ISOxo/RL Grime festival-trap style). Note: Hex Cougar appears here as hardwave future bass, which is distinct from the EDM trap aesthetic. Belongs in GENR-13+ (future genre addition).

</deferred>

---

*Phase: 23-extended-genre-library*
*Context gathered: 2026-03-26*
