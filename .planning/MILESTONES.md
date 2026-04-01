# Milestones

## v1.8 Iterative Refinement Protocol (Shipped: 2026-03-31)

**Phases completed:** 3 phases (45-47), 3 plans
**Requirements:** 8/8 complete
**Files changed:** ~15 files, +1,800 / -0 lines (new package)
**Timeline:** 1 day (2026-03-31)
**Tests:** ~30 new tests

**Delivered:** Surgical section refinement system — `get_section_state` reads everything built in a named arrangement section (clips, notes, device params, recipe deltas); `interpret_section_refinement` maps 22 aesthetic adjectives through a RefinementLexicon to per-track note and device change plans; `apply_section_note_refinement` and `apply_section_device_refinement` apply changes to only the target section's clips and parameters; `refine_section` chains all steps in a single call. Two new RS commands (`transpose_arrangement_clip`, `modify_arrangement_clip_notes`) handle arrangement-view note editing.

**Key accomplishments:**

- `schema.py`: `SectionState`, `TrackStateEntry`, `ClipSummary`, `RefinementVector`, `SectionRefinementPlan` TypedDicts — JSON-serializable
- `lexicon.py`: `REFINEMENT_LEXICON` with 22 aesthetic adjectives (darker, brighter, warmer, harder, heavier, sparser, denser...) each mapped to signed-proportional-delta `RefinementVector` across harmonic/timbral/dynamic domains
- `get_section_state` MCP tool: reads locator range → collects clips per track → note summaries + mix_context with device params + recipe_delta
- `interpret_section_refinement` MCP tool: read-only plan generation — tokenize instruction → merge vectors → resolve against current values → per-track change plan with reasoning
- `refine_prompt` MCP tool: partial re-derivation of existing `ProductionBrief` — only affected fields change, unchanged fields preserved, diff returned
- `apply_section_note_refinement` + `apply_section_device_refinement` + `refine_section` MCP tools for end-to-end application

---

## v1.7 Prompt Interpretation (Shipped: 2026-03-31)

**Phases completed:** 3 phases (42-44), 3 plans
**Requirements:** 10/10 complete
**Files changed:** 10 files, +1,200 / -0 lines (new package)
**Timeline:** 1 day (2026-03-31)
**Tests:** 100 new tests

**Delivered:** Deterministic NLP prompt interpretation layer for Ableton — `MCP_Server/prompt/` package with signal lexicon (12 genres, 40+ moods, 20+ instruments, 20+ effects), greedy longest-match parser, and parameter derivation engine. Two new MCP tools: `interpret_prompt(text)` returns a structured `ProductionBrief` with tempo range, scale/mode, groove pattern, instrument hints, effect hints, velocity style, and plain-English reasoning; `interpret_prompt_to_plan(text)` chains directly to `generate_production_plan` for one-call prompt→arrangement workflow.

**Key accomplishments:**

- `schema.py`: `SignalSet` and `ProductionBrief` TypedDicts — JSON-serializable, 11-field brief with nullable primary_genre
- `lexicon.py`: 12-genre map (with all blueprint aliases), 40+ mood adjectives (energy_level + scale_bias), 20+ instrument refs (role + descriptor), 20+ effect refs, 12+ tempo signals, groove hint overrides
- `parser.py`: Greedy longest-match tokenizer — multi-word phrases first (lo_fi_hip_hop → lo_fi), stop words preserved for phrase matching ("drum and bass"), 5-level priority (genre > instrument > effect > mood > tempo)
- `deriver.py`: 5 DERV-* derivation steps — explicit BPM extraction, genre+energy tempo, genre+mood key feel, genre+structural hint groove, blueprint role instrument hints; reasoning list on every call
- `tools/prompt.py`: `interpret_prompt` + `interpret_prompt_to_plan` registered MCP tools; low-confidence warning when genre unresolved; `bars_per_section` override support

---

## v1.6 Self-evaluation (Shipped: 2026-03-31)

**Phases completed:** 3 phases (39-41), 3 plans
**Requirements:** 9/9 complete
**Files changed:** 24 files, +3,809 / -40 lines
**Timeline:** 1 day (2026-03-31)

**Delivered:** Production self-evaluation system for Ableton — single `evaluate_session(genre)` MCP tool running four dimension evaluators (mix balance, arrangement completeness, sound selection coverage, harmonic coherence), returning a composite score (0-10 + letter grade), all issues ranked by severity, and up to 3 `top_fixes` each with the specific MCP tool call to resolve it.

**Key accomplishments:**

- `MCP_Server/evaluation/` package with `EvaluationIssue`, `DimensionScore`, `SessionScore` TypedDicts and `grade_from_score()` helper — JSON-serializable schema used by all evaluators
- Mix balance evaluator diffs device params vs. role×genre recipe targets with DIFF_THRESHOLD + CRITICAL_THRESHOLD severity mapping; gain staging deviations from GAIN_TARGETS included as issues
- Arrangement completeness evaluator checks every track for loaded instrument (critical) and arrangement clips (warning); weighted scoring
- Sound selection coverage evaluator pre-builds role→instrument map from sounds catalog, matches on device display name
- Harmonic coherence evaluator computes in-key pitch classes via pure integer arithmetic (no music21); Session-view clip iteration; empty key → graceful skip with info issue
- `evaluate_session()` MCP tool with `_run_evaluator` per-evaluator isolation, simple-average composite, critical-first issue sort, `top_fixes` with `tool_call = fix_hint`

---

## v1.4 Mix/Master Intelligence (Shipped: 2026-03-30)

**Phases completed:** 6 phases (29-34), 11 plans
**Requirements:** 14/14 complete
**Files changed:** 360 files, +25,793 / -1,167 lines
**Timeline:** 3 days (2026-03-28 → 2026-03-30)

**Delivered:** Full mixing and mastering intelligence for Ableton — device parameter catalog, role×genre mix recipes for 12 genres, one-call recipe application with atomic device loading, session mix state snapshot, gain staging analysis, and AI-driven parameter adjustment suggestions.

**Key accomplishments:**

- Device parameter catalog bootstrapped from live Ableton session — 327 parameters across 12 built-in devices with normalized-to-natural-unit conversion formulas; `get_device_catalog` and `get_role_taxonomy` MCP tools
- Role×genre mix recipes for all 12 genres (house, techno, ambient, DnB, synthwave, dubstep, trance, future bass, hip-hop/trap, disco/funk, neo-soul/R&B, lo-fi) — 9 roles per genre with EQ/compression/reverb/panning/dynamics values; pkgutil auto-discovery
- `apply_mix_recipe` and `apply_master_recipe` MCP tools applying full device chains in one call — atomic RS handler (self_scheduling + response queue) guarantees devices instantiate before parameters are set
- `get_mix_state` full session snapshot and `check_gain_staging` per-track dBFS analysis against role-based targets — empty MIDI scaffold tracks excluded
- `suggest_mix_adjustments` read-only intelligence tool — diffs current device state against recipe targets, returns per-parameter suggestions with one-sentence reasoning and natural-unit display values
- Master bus recipes (GlueCompressor + MultibandDynamics + Limiter) for all 12 genres with dynamic docstrings via `list_recipes()`

---

## v1.3 Arrangement Intelligence (Shipped: 2026-03-28)

**Phases completed:** 4 phases (25-28), 8 plans
**Requirements:** 10/10 complete
**Git range:** feat(25-01) → feat(28-01), 20+ commits
**Timeline:** 1 day (2026-03-28)

**Delivered:** Systematic production workflow for Ableton — plan sections from genre conventions, encode the plan as locators and tracks, execute section-by-section with checklist guidance.

**Key accomplishments:**

- ArrangementEntry schema extended with optional energy (1-10), roles, and transition_in fields — backward-compatible across all 12 genres and 148 tests
- `generate_production_plan` and `generate_section_plan` MCP tools transforming genre blueprints into token-efficient flat JSON plans with bar positions and override support
- `scaffold_arrangement` MCP tool writing production plans into Ableton as named locators and MIDI tracks in one atomic operation
- `get_arrangement_overview` MCP tool reading back locators, tracks, and session length for mid-session re-orientation
- `get_section_checklist` and `get_arrangement_progress` tools enabling methodical per-section execution — nothing skipped under context pressure

---

## v1.2 Genre/Style Blueprints (Shipped: 2026-03-27)

**Phases completed:** 5 phases (20-24), 9 plans
**Requirements:** 23/23 complete
**Git range:** feat(20-01) → feat(24-02), 40+ commits
**Timeline:** 2 days (2026-03-26 → 2026-03-27)

**Delivered:** Curated genre reference system giving Claude consistent knowledge of 12 electronic music genres — instrumentation, harmony, rhythm, arrangement, and mixing — delivered via MCP with theory engine integration.

**Key accomplishments:**

- Blueprint schema (TypedDict) and auto-discovery catalog (pkgutil) with alias resolution, shallow subgenre merge, and import-time validation
- Two MCP tools: `list_genre_blueprints` + `get_genre_blueprint` with section filtering, subgenre support, and alias resolution
- Full 12-genre catalog: P0 (house, techno, hip-hop/trap, ambient), P1 (DnB, dubstep, trance, neo-soul/R&B), P2 (synthwave, lo-fi, future bass, disco/funk) — 35+ subgenres total
- `get_genre_palette` MCP tool bridging blueprint harmony data to theory engine with key-resolved chord names, scales, and progressions
- Centralized quality gate: all 12 genres validated against token budget (537-670 tokens, under 1200 limit) and theory engine name registry

---

## v1.1 Theory Engine (Shipped: 2026-03-26)

**Phases completed:** 6 phases (14-19), 12 plans, 224 tests
**Lines of code:** 5,704 Python (theory library + tools + tests)
**Git range:** feat(14-01) → feat(19-02), 15 feature commits
**Timeline:** 2 days (2026-03-24 → 2026-03-25)

**Delivered:** Comprehensive music theory intelligence layer powered by music21, giving Claude harmonic awareness for composing, analyzing, and arranging in Ableton Live.

**Key accomplishments:**

- Music theory foundation with music21 integration and bidirectional MIDI-to-note mapping across 128 pitches
- Chord engine supporting 26 qualities with build/identify/invert/voice operations
- 38-scale catalog with pitch generation, note validation, scale detection, and modal relationships
- Progression engine with 25-genre catalog, Roman numeral analysis, voice-led generation, and next-chord suggestions
- Harmonic analysis: Krumhansl-Schmuckler key detection, time-grid chord segmentation, harmonic rhythm analysis
- Voice leading with parallel-5ths/octaves avoidance + 18 rhythm patterns producing add_notes_to_clip-ready MIDI

---
