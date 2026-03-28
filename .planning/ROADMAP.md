# Roadmap: Ableton MCP

## Milestones

| Milestone | Phases | Plans | Requirements | Status | Shipped |
|-----------|--------|-------|-------------|--------|---------|
| v1.0 MVP | 1-13 | 33 | 53 | Complete | 2026-03-23 |
| v1.1 Theory Engine | 14-19 | 12 | 24 | Complete | 2026-03-26 |
| v1.2 Genre/Style Blueprints | 20-24 | 9 | 23 | Complete | 2026-03-27 |
| v1.3 Arrangement Intelligence | 25-28 | 8 | 10 | Complete | 2026-03-28 |
| v1.4 Mix/Master Intelligence | 29-34 | TBD | 14 | In Progress | - |

## v1.4 Mix/Master Intelligence (Phases 29-34)

**Milestone Goal:** Give Claude reliable mixing and mastering in Ableton by eliminating parameter guessing -- role x genre recipes map principles to exact device values; analysis tools close the feedback loop.

- [ ] **Phase 29: Device Parameter Catalog and Role Taxonomy** - Live-verified parameter catalog for 12 built-in devices plus canonical mixing role definitions
- [ ] **Phase 30: Core Mix Recipes** - Role x genre track recipes for 4 core genres (house, techno, ambient, DnB)
- [ ] **Phase 31: Apply Recipe and Batch Parameter Tools** - Single-call recipe application with atomic device loading and batch parameter setting
- [ ] **Phase 32: Device State Reader and Gain Staging** - Session-wide device state snapshot and role-based gain staging analysis
- [ ] **Phase 33: Mix Adjustment Intelligence** - Suggest parameter changes by diffing current state against recipe targets
- [ ] **Phase 34: Full Genre Recipe Expansion** - Extend track and master bus recipes to all 12 genres

## Phase Details

### Phase 29: Device Parameter Catalog and Role Taxonomy
**Goal**: Users can look up exact API parameter names, value ranges, and unit conversions for all target devices, and retrieve the canonical role taxonomy that organizes recipe lookup
**Depends on**: Nothing (first phase of v1.4; builds on existing device infrastructure)
**Requirements**: CATL-01, ROLE-01
**Success Criteria** (what must be TRUE):
  1. User can query the catalog for any of the 12 target devices (EQ Eight, Compressor, Glue Compressor, Drum Buss, Multiband Dynamics, Reverb, Delay, Auto Filter, Gate, Limiter, Envelope Follower, Utility) and receive exact API parameter names matching what Ableton returns from get_device_parameters
  2. User can retrieve normalized-to-natural-unit conversion formulas (e.g., 0.0-1.0 to Hz for EQ frequency) from the catalog for parameters that use normalized storage
  3. User can retrieve the role taxonomy (kick, bass, lead, pad, chords, vocal, atmospheric, return, master) and use these identifiers as keys for recipe lookup
  4. Catalog entries are validated against a live Ableton session -- no hand-authored parameter names from documentation
**Plans**: 2 plans

Plans:
- [ ] 29-01-PLAN.md -- Devices package, catalog data, MCP tools, and tests
- [ ] 29-02-PLAN.md -- Bootstrap script and live Ableton catalog verification

### Phase 30: Core Mix Recipes
**Goal**: Users can retrieve complete role x genre mix recipes for the 4 highest-impact genres, providing EQ, compression, reverb/delay, panning, and dynamics parameter values per role
**Depends on**: Phase 29
**Requirements**: RECIP-01
**Success Criteria** (what must be TRUE):
  1. User can retrieve a mix recipe for any role in house, techno, ambient, or DnB and receive device parameter values (referencing catalog entries) for EQ, compression, reverb/delay, panning, and dynamics
  2. Recipe values reference validated catalog parameter names -- no recipe can specify a parameter name absent from the catalog
  3. Recipe auto-discovery works via the same pkgutil pattern used by genre blueprints -- adding a new genre recipe file requires zero registration code
**Plans**: TBD

Plans:
- [ ] 30-01: TBD

### Phase 31: Apply Recipe and Batch Parameter Tools
**Goal**: Users can apply a track mix recipe or master bus recipe to an Ableton track in one MCP call with atomic device loading, and set multiple parameters in a single socket round-trip
**Depends on**: Phase 30
**Requirements**: BATCH-01, APPLY-01, APPLY-02, APPLY-03, SIDE-01
**Success Criteria** (what must be TRUE):
  1. User can call apply_mix_recipe with a track index, role, and genre and see the required devices loaded and all parameters set on that track without issuing multiple sequential tool calls
  2. User can call apply_master_recipe with a genre and see a Glue Compressor + Multiband Dynamics + Limiter chain applied to the master track in one operation
  3. Parameters are set only after the device is confirmed as instantiated -- no race condition where parameters are written to a device that hasn't finished loading
  4. User can set a compressor's sidechain input source by track name rather than hardcoded track index
  5. Batch parameter setting completes in a single socket round-trip rather than N sequential calls
**Plans**: TBD

Plans:
- [ ] 31-01: TBD
- [ ] 31-02: TBD

### Phase 32: Device State Reader and Gain Staging
**Goal**: Users can snapshot the entire session's mix state and run a gain staging check that flags tracks outside role-based target ranges
**Depends on**: Phase 31
**Requirements**: STATE-01, GAIN-01, GAIN-02
**Success Criteria** (what must be TRUE):
  1. User can call get_mix_state and receive current device parameters for every device on every track in a single MCP call
  2. User can call check_gain_staging and receive per-track dBFS estimates compared against role-based targets, with tracks significantly above or below target flagged
  3. Gain staging check excludes MIDI tracks with no instrument loaded -- no false-positive flags on empty scaffold tracks from v1.3
**Plans**: TBD

Plans:
- [ ] 32-01: TBD

### Phase 33: Mix Adjustment Intelligence
**Goal**: Users can request AI-driven mix adjustment suggestions that compare current device state against recipe targets and explain each recommended change
**Depends on**: Phase 32
**Requirements**: INTEL-01
**Success Criteria** (what must be TRUE):
  1. User can call suggest_mix_adjustments for a track and receive a list of parameter diffs (current value to suggested value) with a one-sentence reason per change
  2. Suggestions are based on comparing actual device state (from get_mix_state) against the role x genre recipe for that track
  3. Suggestions are returned for review only -- no parameters are changed without explicit user confirmation
**Plans**: TBD

Plans:
- [ ] 33-01: TBD

### Phase 34: Full Genre Recipe Expansion
**Goal**: Users can retrieve track and master bus mix recipes for all 12 genres, completing the full genre coverage
**Depends on**: Phase 30
**Requirements**: RECIP-02, MSTR-01
**Success Criteria** (what must be TRUE):
  1. User can retrieve a role x genre mix recipe for any of the 12 genres (adding synthwave, hip-hop/trap, dubstep, trance, lo-fi, future bass, disco/funk, neo-soul/R&B to the core 4)
  2. User can retrieve a master bus recipe for any of the 12 genres returning Glue Compressor + Multiband Dynamics + Limiter parameter settings appropriate to that genre's loudness and tonal conventions
  3. All 12 genre recipes pass schema validation and reference only catalog-verified parameter names
**Plans**: TBD

Plans:
- [ ] 34-01: TBD

<details>
<summary>v1.3 Arrangement Intelligence (Phases 25-28) - SHIPPED 2026-03-28</summary>

### Phase 25: Blueprint Arrangement Extension
**Goal**: Users can access rich per-section arrangement data from any genre blueprint
**Requirements**: ARNG-01, ARNG-02, ARNG-03
Plans:
- [x] 25-01: Schema extension + house reference implementation
- [x] 25-02: Author arrangement data for remaining 11 genres + 3 subgenre overrides

### Phase 26: Production Plan Builder
**Goal**: Users can generate concrete, token-efficient production plans from genre conventions
**Requirements**: PLAN-01, PLAN-02, PLAN-03
Plans:
- [x] 26-01: Core plan builder tools
- [x] 26-02: Override support

### Phase 27: Locator and Scaffolding Commands
**Goal**: Users can write a production plan into Ableton Arrangement view as locators and tracks
**Requirements**: SCAF-01, SCAF-02
Plans:
- [x] 27-01: scaffold_arrangement MCP tool + Remote Script handlers
- [x] 27-02: get_arrangement_overview MCP tool + get_arrangement_state handler

### Phase 28: Section Execution and Quality Gate
**Goal**: Users can execute sections methodically with checklist guidance
**Requirements**: EXEC-01, EXEC-02
Plans:
- [x] 28-01: Execution tools + test coverage
- [x] 28-02: Live Ableton verification checkpoint

</details>

## Progress

**Execution Order:**
Phases execute in numeric order: 29 -> 30 -> 31 -> 32 -> 33 -> 34
(Phase 34 depends on Phase 30, not Phase 33 -- can execute after Phase 33 or in parallel with Phases 31-33 if desired)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 29. Device Parameter Catalog and Role Taxonomy | 0/2 | Not started | - |
| 30. Core Mix Recipes | 0/TBD | Not started | - |
| 31. Apply Recipe and Batch Parameter Tools | 0/TBD | Not started | - |
| 32. Device State Reader and Gain Staging | 0/TBD | Not started | - |
| 33. Mix Adjustment Intelligence | 0/TBD | Not started | - |
| 34. Full Genre Recipe Expansion | 0/TBD | Not started | - |
