# Requirements: AbletonMCP

**Defined:** 2026-03-25
**Core Value:** An AI assistant can produce actual music in Ableton — with harmonic intelligence and genre-aware conventions.

## v1.2 Requirements

Requirements for Genre/Style Blueprints milestone. Each maps to roadmap phases.

### Infrastructure

- [ ] **INFR-01**: Blueprint schema defines all genre dimensions (instrumentation, harmony, rhythm, arrangement, mixing, production tips)
- [ ] **INFR-02**: Catalog registry discovers and indexes all genre modules at import time
- [ ] **INFR-03**: Alias resolution maps common name variants to canonical genre IDs (e.g., "dnb" → "drum_and_bass")
- [ ] **INFR-04**: Subgenre merge combines parent genre base with subgenre overrides via shallow merge
- [ ] **INFR-05**: Schema validation runs at import time, rejecting malformed genre data before server starts

### Tools

- [ ] **TOOL-01**: `list_genre_blueprints` returns all available genres with metadata (name, BPM range, subgenres)
- [ ] **TOOL-02**: `get_genre_blueprint` returns full or section-filtered blueprint for a genre/subgenre
- [ ] **TOOL-03**: `get_genre_palette` returns key-resolved chords, scales, and progressions by bridging blueprint harmony to theory engine

### Genre Content — P0

- [ ] **GENR-01**: House blueprint with subgenres (deep, tech, progressive, acid)
- [ ] **GENR-02**: Techno blueprint with subgenres (minimal, industrial, melodic, Detroit)
- [ ] **GENR-03**: Hip-hop/Trap blueprint with subgenres (boom bap, trap, lo-fi hip-hop)
- [ ] **GENR-04**: Ambient blueprint with subgenres (dark ambient, drone, cinematic)

### Genre Content — P1

- [ ] **GENR-05**: Drum & Bass blueprint with subgenres (liquid, neurofunk, jungle)
- [ ] **GENR-06**: Dubstep blueprint with subgenres (brostep, riddim, melodic)
- [ ] **GENR-07**: Trance blueprint with subgenres (progressive, uplifting, psytrance)
- [ ] **GENR-08**: Neo-soul/R&B blueprint with subgenres (neo-soul, contemporary R&B)

### Genre Content — P2

- [ ] **GENR-09**: Synthwave blueprint with subgenres (retrowave, darksynth, outrun)
- [ ] **GENR-10**: Lo-fi blueprint with subgenres (lo-fi hip-hop, chillhop)
- [ ] **GENR-11**: Future Bass blueprint with subgenres (future bass, kawaii future)
- [ ] **GENR-12**: Disco/Funk blueprint with subgenres (nu-disco, funk, boogie)

### Quality

- [ ] **QUAL-01**: Every blueprint stays within 800-1200 token budget (measured, not estimated)
- [ ] **QUAL-02**: Every chord_type and scale name in blueprints validated against theory engine's supported types
- [ ] **QUAL-03**: Test suite covers schema validation, tool output format, section filtering, and palette bridge correctness

## Future Requirements

### Genre Content — P3+

- **GENR-13**: Additional genres as community requests (garage, grime, UK bass, breakbeat, IDM, etc.)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-genre detection from Ableton session | Fragile — requires analyzing session state; asking the user is better UX |
| Blueprint editing/creation tools | Blueprints are curated reference data, not user-editable content |
| Real-time blueprint updates from web | Introduces network dependency and data trust issues |
| Genre-specific operation tools (e.g., `create_house_track`) | Combinatorial explosion (12 genres x N operations); generic tools + context is correct |
| MIDI pattern generation from blueprints | Blueprint scope is reference/guidance; theory engine + Claude generate MIDI |
| Audio analysis for genre classification | MCP is control layer, not audio pipeline |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 20 | Pending |
| INFR-02 | Phase 20 | Pending |
| INFR-03 | Phase 20 | Pending |
| INFR-04 | Phase 20 | Pending |
| INFR-05 | Phase 20 | Pending |
| TOOL-01 | Phase 21 | Pending |
| TOOL-02 | Phase 21 | Pending |
| TOOL-03 | Phase 24 | Pending |
| GENR-01 | Phase 20 | Pending |
| GENR-02 | Phase 22 | Pending |
| GENR-03 | Phase 22 | Pending |
| GENR-04 | Phase 22 | Pending |
| GENR-05 | Phase 22 | Pending |
| GENR-06 | Phase 22 | Pending |
| GENR-07 | Phase 22 | Pending |
| GENR-08 | Phase 22 | Pending |
| GENR-09 | Phase 23 | Pending |
| GENR-10 | Phase 23 | Pending |
| GENR-11 | Phase 23 | Pending |
| GENR-12 | Phase 23 | Pending |
| QUAL-01 | Phase 24 | Pending |
| QUAL-02 | Phase 24 | Pending |
| QUAL-03 | Phase 24 | Pending |

**Coverage:**
- v1.2 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-03-25*
*Last updated: 2026-03-25 after roadmap creation*
