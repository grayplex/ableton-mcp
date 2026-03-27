# Phase 22: Core Genre Library - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

7 genre blueprint data files (techno, hip-hop/trap, ambient, DnB, dubstep, trance, neo-soul/R&B), each following the exact pattern established by `house.py` in Phase 20. Pure content authoring — no new code architecture. All genres auto-discovered by catalog, aliases resolve, subgenres merge.

</domain>

<decisions>
## Implementation Decisions

### Subgenre Selection (Customized from REQUIREMENTS.md)
- **D-01:** Techno: minimal, industrial, melodic, Detroit, **peaktime/driving** (5 subgenres — added peaktime/driving)
- **D-02:** Hip-hop/Trap: boom bap, trap, lo-fi hip-hop (3 subgenres — unchanged, hip-hop focused)
- **D-03:** Ambient: dark ambient, drone, cinematic (3 subgenres — unchanged)
- **D-04:** DnB: liquid, neurofunk, jungle, **neuro** (4 subgenres — added neuro as distinct from neurofunk: heavier, more experimental)
- **D-05:** Dubstep: brostep, riddim, melodic, **deep dubstep** (4 subgenres — added deep dubstep: original UK sound, 140 BPM, half-time, sub-bass focus)
- **D-06:** Trance: progressive, uplifting, psytrance (3 subgenres — unchanged)
- **D-07:** Neo-soul/R&B: neo-soul, contemporary R&B, **alternative R&B** (3 subgenres — added alternative R&B: darker production, electronic elements, Frank Ocean/Weeknd territory)

### Content Depth
- **D-08:** All 7 genres match house.py depth exactly — equal detail across all 6 dimensions. No P0/P1 priority differentiation in content quality

### Theory Name Validation
- **D-09:** Each genre's tests validate that all `chord_types` exist in `_QUALITY_MAP` and all `scale` names exist in `SCALE_CATALOG` — catches mistakes at authoring time, not deferred to Phase 24

### Claude's Discretion
- Exact instrumentation roles per genre (following generic roles pattern from D-11 Phase 20)
- Specific chord progressions per genre (must use valid Roman numeral notation)
- BPM ranges per genre and subgenre
- Arrangement section structures (following bar counts pattern from D-12 Phase 20)
- Rhythm dimension details (time signature, swing, note values, drum patterns)
- Mixing dimension details (frequency ranges, effects, stereo conventions)
- Production tips per genre
- File naming (e.g., `drum_and_bass.py`, `hip_hop_trap.py`, `neo_soul_rnb.py`)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Reference Implementation
- `MCP_Server/genres/house.py` — Canonical genre blueprint template. ALL 7 new genres must match this structure exactly
- `MCP_Server/genres/schema.py` — TypedDict definitions and `validate_blueprint()` function

### Theory Engine (for D-09 validation)
- `MCP_Server/theory/chords.py` — `_QUALITY_MAP` dict (26 chord qualities): maj, min, dim, aug, maj7, min7, dom7, 7, dim7, hdim7, min7b5, sus2, sus4, add9, 9, min9, maj9, 11, min11, 13, min13, 7b5, 7#5, 7b9, 7#9, 7#11
- `MCP_Server/theory/scales.py` — `SCALE_CATALOG` dict (38 scales): major, natural_minor, dorian, phrygian, lydian, mixolydian, aeolian, locrian, harmonic_minor, melodic_minor, major_pentatonic, minor_pentatonic, blues, + 23 more

### Infrastructure
- `MCP_Server/genres/catalog.py` — Auto-discovery, alias resolution, subgenre merge
- `tests/test_genres.py` — Existing genre test patterns (24 tests)

### Requirements
- `.planning/REQUIREMENTS.md` — GENR-02 through GENR-08 for this phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/genres/house.py` — Exact template to follow: GENRE dict with all 6 dimensions + SUBGENRES dict
- `MCP_Server/genres/catalog.py` — Auto-discovers new genre files without any code changes needed
- `tests/test_genres.py` — TestHouseBlueprint class pattern for per-genre validation tests

### Established Patterns
- Genre file: module docstring → GENRE dict → SUBGENRES dict, no imports, pure data (D-01, D-02)
- Subgenre overrides: only dimensions that differ from base (BPM, harmony, arrangement)
- Aliases: include common alternate names and abbreviations
- Tests: schema validation + completeness + theory name cross-validation

### Integration Points
- No code changes needed — catalog auto-discovers new .py files in `MCP_Server/genres/`
- New genres appear automatically in `list_genre_blueprints` output
- Tests extend `tests/test_genres.py` or create per-genre test files

</code_context>

<specifics>
## Specific Ideas

- Neuro DnB is DISTINCT from neurofunk: heavier, more experimental, harder-hitting (not just an alias)
- Deep dubstep is the original UK sound (140 BPM, half-time, sub-bass focus) — distinct from brostep/riddim which are aggressive
- Alternative R&B includes artists like The Weeknd, Frank Ocean — darker production with electronic elements
- Peaktime/driving techno is festival-oriented, high-energy, distinct from Detroit's minimalism

</specifics>

<deferred>
## Deferred Ideas

- **EDM Trap as standalone genre** — Hex Cougar, ISOxo, RL Grime style. Festival-oriented with heavy bass drops, synth work, build-drop structures. Distinct from hip-hop trap. Belongs in GENR-13+ (future genre addition)

</deferred>

---

*Phase: 22-core-genre-library*
*Context gathered: 2026-03-26*
