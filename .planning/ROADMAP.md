# Roadmap: AbletonMCP

## Milestones

- ✅ **v1.0 MVP** — Phases 1-13 (shipped 2026-03-23)
- ✅ **v1.1 Theory Engine** — Phases 14-19 (shipped 2026-03-26)
- 🚧 **v1.2 Genre/Style Blueprints** — Phases 20-24 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-13) — SHIPPED 2026-03-23</summary>

Production-quality Ableton Live 12 MCP bridge: 13 phases, 33 plans, 178 handler commands, 174 MCP tools, 204 tests, 53 requirements complete → [archived](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v1.1 Theory Engine (Phases 14-19) — SHIPPED 2026-03-26</summary>

- [x] Phase 14: Theory Foundation (2/2 plans) — completed 2026-03-24
- [x] Phase 15: Chord Engine (2/2 plans) — completed 2026-03-24
- [x] Phase 16: Scale & Mode Explorer (2/2 plans) — completed 2026-03-24
- [x] Phase 17: Progression Engine (2/2 plans) — completed 2026-03-24
- [x] Phase 18: Harmonic Analysis (2/2 plans) — completed 2026-03-25
- [x] Phase 19: Voice Leading & Rhythm (2/2 plans) — completed 2026-03-25

Music theory intelligence layer: 24 requirements, 23 MCP tools, 224 tests → [archived](milestones/v1.1-ROADMAP.md)

</details>

### v1.2 Genre/Style Blueprints (In Progress)

**Milestone Goal:** Curated genre reference documents that give Claude consistent knowledge of electronic music conventions — instrumentation, harmony, rhythm, arrangement, and mixing — delivered via the MCP server.

- [x] **Phase 20: Blueprint Infrastructure** - Schema, catalog, validation, and house genre as canonical example (completed 2026-03-26)
- [x] **Phase 21: Blueprint Tools** - MCP tool wrappers for genre listing and blueprint retrieval (completed 2026-03-26)
- [x] **Phase 22: Core Genre Library** - P0 remaining (techno, hip-hop/trap, ambient) + P1 genres (DnB, dubstep, trance, neo-soul) (completed 2026-03-26)
- [x] **Phase 23: Extended Genre Library** - P2 genres (synthwave, lo-fi, future bass, disco/funk) (completed 2026-03-27)
- [ ] **Phase 24: Palette Bridge & Quality Gate** - Theory engine bridge tool + cross-validation + full test suite

## Phase Details

### Phase 20: Blueprint Infrastructure
**Goal**: A validated schema and catalog system exists, proven end-to-end with a complete house genre blueprint
**Depends on**: Nothing (first phase of v1.2; builds on existing codebase)
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04, INFR-05, GENR-01
**Success Criteria** (what must be TRUE):
  1. A house genre blueprint can be imported and contains all six dimensions (instrumentation, harmony, rhythm, arrangement, mixing, production tips)
  2. The catalog discovers and indexes genre modules at import time without manual registration
  3. Common aliases (e.g., "deep house", "deep_house") resolve to the correct genre/subgenre
  4. Subgenre data merges with parent genre data, with subgenre values overriding parent values
  5. A malformed genre dict (missing required keys) causes an import-time error, not a silent runtime failure
**Plans**: 2 plans
Plans:
- [x] 20-01-PLAN.md — Schema definitions (TypedDict) and validate_blueprint() function
- [x] 20-02-PLAN.md — Catalog auto-discovery, alias resolution, subgenre merge, and house blueprint

### Phase 21: Blueprint Tools
**Goal**: Claude can discover available genres and retrieve full or section-filtered blueprints through MCP tools
**Depends on**: Phase 20
**Requirements**: TOOL-01, TOOL-02
**Success Criteria** (what must be TRUE):
  1. Calling `list_genre_blueprints` returns all registered genres with name, BPM range, and available subgenres
  2. Calling `get_genre_blueprint` with a genre name returns the full blueprint as structured data
  3. Calling `get_genre_blueprint` with a `sections` filter returns only the requested dimensions (e.g., just harmony and rhythm)
  4. Calling `get_genre_blueprint` with a subgenre returns merged parent+subgenre data
**Plans**: 1 plan
Plans:
- [x] 21-01-PLAN.md — Genre MCP tools (list_genre_blueprints + get_genre_blueprint) with TDD

### Phase 22: Core Genre Library
**Goal**: The 8 most-used electronic genres are available as complete blueprints (P0 + P1 tiers)
**Depends on**: Phase 20
**Requirements**: GENR-02, GENR-03, GENR-04, GENR-05, GENR-06, GENR-07, GENR-08
**Success Criteria** (what must be TRUE):
  1. Techno, hip-hop/trap, and ambient blueprints each pass schema validation and include all defined subgenres
  2. DnB, dubstep, trance, and neo-soul/R&B blueprints each pass schema validation and include all defined subgenres
  3. All 7 new genres appear in `list_genre_blueprints` output alongside house
  4. Every genre's aliases resolve correctly (e.g., "dnb" to drum_and_bass, "hiphop" to hip_hop_trap)
**Plans**: 2 plans
Plans:
- [x] 22-01-PLAN.md — [To be planned]
- [x] 22-02-PLAN.md — [To be planned]

### Phase 23: Extended Genre Library
**Goal**: The full 12-genre catalog is complete (P2 tier)
**Depends on**: Phase 20
**Requirements**: GENR-09, GENR-10, GENR-11, GENR-12
**Success Criteria** (what must be TRUE):
  1. Synthwave, lo-fi, future bass, and disco/funk blueprints each pass schema validation and include all defined subgenres
  2. All 12 genres appear in `list_genre_blueprints` output
  3. Every P2 genre's aliases resolve correctly
**Plans**: 2 plans
Plans:
- [ ] 23-01-PLAN.md — Synthwave + lo-fi blueprints, hip-hop lo_fi_hip_hop removal, all Phase 23 test classes
- [ ] 23-02-PLAN.md — Future bass + disco/funk blueprints, completing the 12-genre catalog

### Phase 24: Palette Bridge & Quality Gate
**Goal**: Claude can get key-resolved chords, scales, and progressions from any genre, and all blueprints meet quality standards
**Depends on**: Phase 21, Phase 22, Phase 23
**Requirements**: TOOL-03, QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. Calling `get_genre_palette` with a genre and key returns concrete chords, scales, and progressions resolved by the theory engine
  2. Every blueprint across all 12 genres stays within the 800-1200 token budget (measured, not estimated)
  3. Every chord_type and scale name referenced in any blueprint is validated against the theory engine's supported types
  4. Test suite covers schema validation, tool output format, section filtering, palette bridge correctness, and theory-name cross-reference
**Plans**: 2 plans
Plans:
- [ ] 24-01-PLAN.md — [To be planned]
- [ ] 24-02-PLAN.md — [To be planned]

## Progress

**Execution Order:**
Phases execute in numeric order: 20 → 21 → 22 → 23 → 24
(Phases 22 and 23 can execute in parallel after Phase 20; Phase 24 requires all prior phases.)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1-13 | v1.0 | 33/33 | Complete | 2026-03-23 |
| 14-19 | v1.1 | 12/12 | Complete | 2026-03-25 |
| 20. Blueprint Infrastructure | v1.2 | 2/2 | Complete    | 2026-03-26 |
| 21. Blueprint Tools | v1.2 | 1/1 | Complete    | 2026-03-26 |
| 22. Core Genre Library | v1.2 | 2/2 | Complete    | 2026-03-26 |
| 23. Extended Genre Library | 2/2 | Complete   | 2026-03-27 | - |
| 24. Palette Bridge & Quality Gate | v1.2 | 0/? | Not started | - |
