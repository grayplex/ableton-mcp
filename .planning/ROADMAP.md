# Roadmap: Ableton MCP

## Milestones

| Milestone | Phases | Plans | Requirements | Status | Shipped |
|-----------|--------|-------|-------------|--------|---------|
| v1.0 MVP | 1-13 | 33 | 53 | Complete | 2026-03-23 |
| v1.1 Theory Engine | 14-19 | 12 | 24 | Complete | 2026-03-26 |
| v1.2 Genre/Style Blueprints | 20-24 | 9 | 23 | Complete | 2026-03-27 |
| v1.3 Arrangement Intelligence | 25-28 | 8 | 10 | Complete | 2026-03-28 |
| v1.4 Mix/Master Intelligence | 29-34 | 11 | 14 | Complete | 2026-03-30 |
| v1.5 Sound Selection Intelligence | 35-38 | 7 | 11 | Complete | 2026-03-31 |
| v1.6 Self-evaluation | 39-41 | TBD | 9 | Active | — |

## Phases

<details>
<summary>v1.4 Mix/Master Intelligence (Phases 29-34) -- SHIPPED 2026-03-30</summary>

- [x] Phase 29: Device Parameter Catalog and Role Taxonomy (2/2 plans) -- completed 2026-03-28
- [x] Phase 30: Core Mix Recipes (2/2 plans) -- completed 2026-03-28
- [x] Phase 31: Apply Recipe and Batch Parameter Tools (2/2 plans) -- completed 2026-03-28
- [x] Phase 32: Device State Reader and Gain Staging (2/2 plans) -- completed 2026-03-28
- [x] Phase 33: Mix Adjustment Intelligence (1/1 plan) -- completed 2026-03-28
- [x] Phase 34: Full Genre Recipe Expansion (2/2 plans) -- completed 2026-03-30

See `.planning/milestones/v1.4-ROADMAP.md` for full phase details.

</details>

<details>
<summary>v1.3 Arrangement Intelligence (Phases 25-28) -- SHIPPED 2026-03-28</summary>

- [x] Phase 25: Blueprint Arrangement Extension (2/2 plans) -- completed 2026-03-28
- [x] Phase 26: Production Plan Builder (2/2 plans) -- completed 2026-03-28
- [x] Phase 27: Locator and Scaffolding Commands (2/2 plans) -- completed 2026-03-28
- [x] Phase 28: Section Execution and Quality Gate (2/2 plans) -- completed 2026-03-28

See `.planning/milestones/v1.3-ROADMAP.md` for full phase details.

</details>

### v1.5 Sound Selection Intelligence -- SHIPPED 2026-03-31

**Milestone Goal:** Give Claude instrument-selection taste -- map descriptor tags like "warm pad" or "punchy kick" to the right native Ableton instrument and browser category path, eliminating random preset fumbling.

- [x] **Phase 35: Package Skeleton and First Profile** - sounds/ package with auto-discovery, browser path validation against live Ableton, Wavetable profile as reference implementation (completed 2026-03-31)
- [x] **Phase 36: Instrument Profile Authoring** - Remaining 5 instrument profiles (Analog, Operator, Drift, Simpler, Drum Rack) following the Wavetable reference (completed 2026-03-31)
- [x] **Phase 37: Descriptor Taxonomy and Scoring Engine** - Weighted sum scoring in catalog.py, descriptor tag vocabulary, list_sound_descriptors MCP tool (completed 2026-03-31)
- [x] **Phase 38: Recommendation Tools and Registration** - get_sound_recommendation and get_instrument_profile MCP tools, tools/__init__.py registration, pyproject.toml update (completed 2026-03-31)

### v1.6 Self-evaluation -- ACTIVE

**Milestone Goal:** Give Claude production self-awareness — evaluate the current Ableton session across four dimensions (mix balance, arrangement completeness, harmonic coherence, sound selection coverage), return a composite score with letter grade and ranked issues, and offer the top-priority fixes by name.

- [x] **Phase 39: Evaluation Framework and Mix Balance Evaluator** - `MCP_Server/evaluation/` package with issue schema, score model, dimension protocol; mix balance evaluator wrapping check_gain_staging + suggest_mix_adjustments (completed 2026-03-31)
- [ ] **Phase 40: Arrangement, Sound Selection, and Harmonic Evaluators** - Arrangement completeness, sound selection coverage, and harmonic coherence evaluators (planned 2026-03-31)
- [ ] **Phase 41: evaluate_session() Tool and Fix Offer Workflow** - Composite evaluate_session() MCP tool, SessionScore, top_fixes list, registration in tools/__init__.py (planned 2026-03-31)

## Phase Details

### Phase 39: Evaluation Framework and Mix Balance Evaluator
**Goal**: The `MCP_Server/evaluation/` package exists with a working issue schema, score model, and dimension protocol; the mix balance evaluator runs against a live session and returns a populated DimensionScore
**Depends on**: Nothing (first phase of v1.6)
**Requirements**: EVAL-01, EVAL-02, MIX-01, MIX-02
**Success Criteria** (what must be TRUE):
  1. `MCP_Server/evaluation/` package exists with `__init__.py`, `schema.py` (issue schema + score model), and `mix_balance.py` (mix balance evaluator)
  2. `EvaluationIssue` carries dimension, severity (critical/warning/info), message, and fix_hint; `DimensionScore` carries name, score 0-10, letter grade, and issues list; `SessionScore` carries composite score, letter grade, and per-dimension breakdown
  3. Mix balance evaluator reads current mix state and compares device parameters against role×genre recipe targets; tracks with >threshold deviation produce EvaluationIssue entries with severity proportional to the magnitude
  4. Mix balance evaluator returns a `DimensionScore` with score 0-10 derived from in-range parameter percentage + gain staging deviations included as issues
**Plans**: TBD

### Phase 40: Arrangement, Sound Selection, and Harmonic Evaluators
**Goal**: All three remaining evaluators are implemented and unit-tested; each returns a populated DimensionScore from live session data
**Depends on**: Phase 39
**Requirements**: ARNG-01, SND-01, HARM-01
**Success Criteria** (what must be TRUE):
  1. `arrangement.py` evaluator checks scaffold tracks for loaded instruments + placed clips; tracks missing instruments flagged as critical, tracks with instruments but no clips flagged as warnings
  2. `sounds_coverage.py` evaluator maps each track's role tag to the sounds/ descriptor profile and flags role-instrument mismatches as warnings
  3. `harmonic.py` evaluator reads MIDI clip notes, compares against session key/scale from `get_session_info`, and flags out-of-key notes with clip name, bar position, and MIDI note number
  4. All three evaluators return a `DimensionScore` with issues correctly populated; unit tests cover empty-session, all-pass, and all-fail cases for each
**Plans**: TBD

### Phase 41: evaluate_session() Tool and Fix Offer Workflow
**Goal**: Claude can call a single `evaluate_session()` MCP tool and receive a complete SessionScore with top_fixes — completing the full self-evaluation loop
**Depends on**: Phase 40
**Requirements**: SESS-01, SESS-02
**Success Criteria** (what must be TRUE):
  1. `evaluate_session()` MCP tool runs all four evaluators in sequence and returns a `SessionScore` with composite score (0-10), composite letter grade, and per-dimension DimensionScore breakdown
  2. All issues from all dimensions are merged and ranked in the response — critical issues first, then warnings, then info
  3. Response includes `top_fixes` — up to 3 highest-severity issues each annotated with the specific MCP tool name and suggested arguments that directly resolves it
  4. `evaluate_session` is registered in `tools/__init__.py` and appears in the MCP tool listing; `MCP_Server.evaluation` is in `pyproject.toml` packages list
**Plans**: TBD

## Phase Details (Archived)

### Phase 35: Package Skeleton and First Profile
**Goal**: The sounds/ package exists with working auto-discovery and one validated instrument profile, proving the data schema and browser paths are correct before committing to all 6 profiles
**Depends on**: Nothing (first phase of v1.5)
**Requirements**: PKG-01, INST-01
**Success Criteria** (what must be TRUE):
  1. `MCP_Server/sounds/` package exists with `__init__.py` and `catalog.py`, and `pkgutil.iter_modules` discovers the Wavetable profile module at import time
  2. The Wavetable profile contains sonic character, strengths, weaknesses, descriptor affinities (role + character axes with 0.0-1.0 weights), and browser category paths
  3. Browser load paths in the Wavetable profile have been validated against a live Ableton session using `get_browser_items_at_path` -- the instrument root path loads successfully via `load_instrument_or_effect`
  4. `catalog.get_profile("wavetable")` returns the complete Wavetable profile dict with alias normalization (case-insensitive, whitespace-tolerant)
**Plans**: 2 plans
Plans:
- [x] 35-01-PLAN.md -- Package skeleton, catalog, Wavetable profile, and tests (TDD)
- [x] 35-02-PLAN.md -- Browser path validation against live Ableton (checkpoint)

### Phase 36: Instrument Profile Authoring
**Goal**: All 6 native Ableton instruments have complete profiles with validated browser paths, giving the scoring engine a full dataset to rank against
**Depends on**: Phase 35
**Requirements**: INST-02, INST-03, INST-04, INST-05, INST-06
**Success Criteria** (what must be TRUE):
  1. Analog, Operator, Drift, Simpler, and Drum Rack profiles exist as individual modules in `sounds/` and are auto-discovered by the catalog (6 total instruments returned)
  2. Each profile follows the Wavetable reference schema -- sonic character, strengths, weaknesses, descriptor affinities, and browser category paths
  3. Simpler profile covers all three modes (Classic, One-Shot, Slice) in its character description
  4. Drum Rack profile uses the correct browser root path (validated against live Ableton) and covers percussive roles (kick, snare, hi-hat)
  5. All 6 instrument load paths verified loadable via `load_instrument_or_effect` in a live Ableton session
**Plans**: TBD

### Phase 37: Descriptor Taxonomy and Scoring Engine
**Goal**: The scoring engine can accept a natural-language descriptor string, tokenize it, score all 6 instruments by summing affinity weights, and return ranked results -- and Claude can discover the full descriptor vocabulary
**Depends on**: Phase 36
**Requirements**: PKG-02, SREC-02
**Success Criteria** (what must be TRUE):
  1. `catalog.recommend("warm pad")` returns the top-ranked instrument with name, browser load path, category hint, and one-line reasoning
  2. `catalog.list_descriptors()` returns all supported tags grouped by axis (role tags: bass, lead, pad, keys, kick, snare, hi-hat, etc.; character tags: warm, bright, dark, evolving, punchy, etc.)
  3. `list_sound_descriptors` MCP tool is callable and returns the grouped descriptor vocabulary
  4. No two distinct descriptors produce identical top-1 results unless intentionally documented (scoring provides meaningful differentiation)
**Plans**: TBD

### Phase 38: Recommendation Tools and Registration
**Goal**: Claude can get sound recommendations and instrument profiles through MCP tools, completing the full descriptor-to-loaded-instrument workflow
**Depends on**: Phase 37
**Requirements**: SREC-01, SREC-03
**Success Criteria** (what must be TRUE):
  1. `get_sound_recommendation("warm pad")` MCP tool returns instrument name, browser load path (directly usable with `load_instrument_or_effect`), category hint, and one-line plain-language reasoning
  2. `get_instrument_profile("wavetable")` MCP tool returns the full instrument character document including strengths, weaknesses, best-for roles, and browser paths
  3. All 3 sound tools (`get_sound_recommendation`, `list_sound_descriptors`, `get_instrument_profile`) are registered in `tools/__init__.py` and appear in the MCP tool listing
  4. `pyproject.toml` includes `MCP_Server.sounds` in the packages list

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 35 -> 36 -> 37 -> 38

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-13. MVP Foundation | v1.0 | 33/33 | Complete | 2026-03-23 |
| 14-19. Theory Engine | v1.1 | 12/12 | Complete | 2026-03-26 |
| 20-24. Genre Blueprints | v1.2 | 9/9 | Complete | 2026-03-27 |
| 25-28. Arrangement Intelligence | v1.3 | 8/8 | Complete | 2026-03-28 |
| 29-34. Mix/Master Intelligence | v1.4 | 11/11 | Complete | 2026-03-30 |
| 35. Package Skeleton and First Profile | v1.5 | 2/2 | Complete    | 2026-03-31 |
| 36. Instrument Profile Authoring | v1.5 | 2/2 | Complete   | 2026-03-31 |
| 37. Descriptor Taxonomy and Scoring Engine | v1.5 | 1/1 | Complete | 2026-03-31 |
| 38. Recommendation Tools and Registration | v1.5 | 1/1 | Complete | 2026-03-31 |
| 39. Evaluation Framework and Mix Balance Evaluator | v1.6 | 0/TBD | Pending | — |
| 40. Arrangement, Sound Selection, and Harmonic Evaluators | v1.6 | 0/TBD | Pending | — |
| 41. evaluate_session() Tool and Fix Offer Workflow | v1.6 | 0/TBD | Pending | — |
