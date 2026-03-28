# Roadmap: AbletonMCP

## Milestones

- ✅ **v1.0 MVP** — Phases 1-13 (shipped 2026-03-23)
- ✅ **v1.1 Theory Engine** — Phases 14-19 (shipped 2026-03-26)
- ✅ **v1.2 Genre/Style Blueprints** — Phases 20-24 (shipped 2026-03-27)
- [ ] **v1.3 Arrangement Intelligence** — Phases 25-28 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-13) — SHIPPED 2026-03-23</summary>

Production-quality Ableton Live 12 MCP bridge: 13 phases, 33 plans, 178 handler commands, 174 MCP tools, 204 tests, 53 requirements complete → [archived](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v1.1 Theory Engine (Phases 14-19) — SHIPPED 2026-03-26</summary>

Music theory intelligence layer: 6 phases, 12 plans, 24 requirements, 23 MCP tools, 224 tests → [archived](milestones/v1.1-ROADMAP.md)

</details>

<details>
<summary>✅ v1.2 Genre/Style Blueprints (Phases 20-24) — SHIPPED 2026-03-27</summary>

- [x] Phase 20: Blueprint Infrastructure (2/2 plans) — completed 2026-03-26
- [x] Phase 21: Blueprint Tools (1/1 plans) — completed 2026-03-26
- [x] Phase 22: Core Genre Library (2/2 plans) — completed 2026-03-26
- [x] Phase 23: Extended Genre Library (2/2 plans) — completed 2026-03-27
- [x] Phase 24: Palette Bridge & Quality Gate (2/2 plans) — completed 2026-03-27

Genre blueprint system: 5 phases, 9 plans, 23 requirements, 12 genres, 3 MCP tools, 148 tests → [archived](milestones/v1.2-ROADMAP.md)

</details>

### v1.3 Arrangement Intelligence (In Progress)

**Milestone Goal:** Give Claude a systematic production workflow -- plan sections from genre conventions, encode the plan into Ableton, and execute section-by-section without dropping the ball at tool call #40.

**Phase Numbering:**
- Integer phases (25, 26, 27, 28): Planned milestone work
- Decimal phases (e.g., 26.1): Urgent insertions (marked with INSERTED)

- [x] **Phase 25: Blueprint Arrangement Extension** - Enrich all 12 genre blueprints with per-section energy levels, instrument roles, and transition descriptors
- [ ] **Phase 26: Production Plan Builder** - Server-side plan generation from genre + key + BPM + vibe, with single-section and override support
- [ ] **Phase 27: Locator and Scaffolding Commands** - Atomic locator creation and batch scaffold command writing the plan into Ableton Arrangement view
- [ ] **Phase 28: Section Execution and Quality Gate** - Per-section execution checklists and arrangement progress checking for methodical, complete production

## Phase Details

### Phase 25: Blueprint Arrangement Extension
**Goal**: Users can access rich per-section arrangement data from any genre blueprint -- energy curve, instrument roles, and transition descriptions -- enabling informed arrangement decisions
**Depends on**: Nothing (first phase of v1.3; builds on v1.2 genre blueprint infrastructure)
**Requirements**: ARNG-01, ARNG-02, ARNG-03
**Success Criteria** (what must be TRUE):
  1. User can call get_genre_blueprint for any of the 12 genres and see an integer energy level (1-10) for each arrangement section
  2. User can call get_genre_blueprint and see a list of instrument roles (e.g. [kick, bass, lead, pad]) for each arrangement section
  3. User can call get_genre_blueprint and see a transition_in descriptor string (e.g. "filter sweep + riser") for each arrangement section
  4. All 148 existing genre tests pass without modification (backward-compatible schema extension)

Plans:
- [x] 25-01: Schema extension + house reference implementation
- [x] 25-02: Author arrangement data for remaining 11 genres + 3 subgenre overrides

### Phase 26: Production Plan Builder
**Goal**: Users can generate concrete, token-efficient production plans from genre conventions and personal preferences -- full track or single section, with customizable overrides
**Depends on**: Phase 25
**Requirements**: PLAN-01, PLAN-02, PLAN-03
**Plans:** 2 plans
**Success Criteria** (what must be TRUE):
  1. User can call generate_production_plan with genre, key, BPM, and vibe and receive a flat production plan with all sections, calculated beat positions, and per-section checklists in under 400 tokens
  2. User can call generate_section_plan for a single section name and receive a targeted plan without generating the full track plan
  3. User can pass override parameters (e.g. shorter breakdown, add bridge, change bar counts) and receive a modified plan reflecting those overrides
  4. Production plan output includes beat positions calculated from the session's time signature (not hardcoded to 4/4)

Plans:
- [ ] 26-01-PLAN.md — Core plan builder with generate_production_plan and generate_section_plan tools
- [ ] 26-02-PLAN.md — Override support (resize, add, remove sections) with validation warnings

### Phase 27: Locator and Scaffolding Commands
**Goal**: Users can write a production plan into Ableton's Arrangement view as named locators and named tracks in one operation, and re-orient mid-session by reading the arrangement state back
**Depends on**: Phase 26
**Requirements**: SCAF-01, SCAF-02
**Success Criteria** (what must be TRUE):
  1. User can call scaffold_arrangement with a production plan and see named locators at correct beat positions and named tracks created in Ableton Arrangement view in one atomic operation
  2. User can call get_arrangement_overview and receive a summary of all locators (with positions), track names, and session length for mid-session re-orientation
  3. Scaffold operation completes within the existing 15-second write timeout for a typical 7-section arrangement

Plans:
- [ ] 27-01: TBD
- [ ] 27-02: TBD

**UI hint**: yes

### Phase 28: Section Execution and Quality Gate
**Goal**: Users can execute sections methodically with checklist guidance and verify that no scaffolded tracks were left empty -- nothing is skipped under context pressure
**Depends on**: Phase 27
**Requirements**: EXEC-01, EXEC-02
**Success Criteria** (what must be TRUE):
  1. User can call get_section_checklist for a named section and receive the list of pending instrument roles to be produced in that section
  2. User can call an arrangement progress check and see which scaffolded MIDI tracks have no instrument loaded, preventing silent empty tracks
  3. End-to-end workflow succeeds: genre blueprint to production plan to scaffolded Ableton session to section-by-section execution with checklist tracking

Plans:
- [ ] 28-01: TBD
- [ ] 28-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 25 → 26 → 27 → 28

| Milestone | Phases | Plans | Requirements | Status | Shipped |
|-----------|--------|-------|-------------|--------|---------|
| v1.0 MVP | 1-13 | 33 | 53 | Complete | 2026-03-23 |
| v1.1 Theory Engine | 14-19 | 12 | 24 | Complete | 2026-03-26 |
| v1.2 Genre/Style Blueprints | 20-24 | 9 | 23 | Complete | 2026-03-27 |
| v1.3 Arrangement Intelligence | 25-28 | TBD | 10 | In Progress | — |
