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
| v1.6 Self-evaluation | 39-41 | 3 | 9 | Complete | 2026-03-31 |
| v1.7 Prompt Interpretation | 42-44 | 3 | 10 | Complete | 2026-03-31 |

## Phases

<details>
<summary>v1.6 Self-evaluation (Phases 39-41) -- SHIPPED 2026-03-31</summary>

- [x] Phase 39: Evaluation Framework and Mix Balance Evaluator (1/1 plans) -- completed 2026-03-31
- [x] Phase 40: Arrangement, Sound Selection, and Harmonic Evaluators (1/1 plans) -- completed 2026-03-31
- [x] Phase 41: evaluate_session() Tool and Fix Offer Workflow (1/1 plans) -- completed 2026-03-31

See `.planning/milestones/v1.6-ROADMAP.md` for full phase details.

</details>

### v1.7 Prompt Interpretation -- SHIPPED 2026-03-31

**Milestone Goal:** Formalize Claude's natural-language music prompt reasoning into a structured, repeatable planning step — so "lo-fi hip hop beat" consistently yields the same quality of concrete parameters (tempo, scale, groove, instruments, effects) as careful ad-hoc reasoning, every time.

---

### Phase 42: ProductionBrief Schema, Signal Lexicon, and Prompt Parser

**Goal**: The foundation layer exists — a validated `ProductionBrief` TypedDict schema, a signal lexicon covering all 12 genres and common descriptors, and a tokenizer that classifies free-text tokens into five signal types; no derivation logic yet, just extraction and schema
**Depends on**: Nothing (first phase of v1.7)
**Requirements**: PARS-01, LEX-01, BRIEF-01
**Success Criteria** (what must be TRUE):
  1. `MCP_Server/prompt/` package exists with `__init__.py`, `schema.py` (ProductionBrief TypedDict), `lexicon.py` (signal vocabulary), and `parser.py` (tokenizer + classifier); pkgutil auto-discovery not needed — internal module
  2. `ProductionBrief` TypedDict includes all 10 fields from BRIEF-01 and is JSON-serializable without conversion helpers
  3. The signal lexicon covers all 12 genre blueprint IDs (plus their aliases), 25+ mood/energy adjectives each with an energy_level and scale_bias, 15+ instrument references each with role+descriptor, 10+ effect references, and 5+ tempo signals
  4. `parser.classify_prompt("lo-fi hip hop beat")` returns a `SignalSet` with `genre_signals=["lo_fi"]`, `mood_signals=[]`, `instrument_signals=[]`, `effect_signals=[]`, `structural_hints=["beat"]` — signal extraction is exact-match and alias-tolerant
  5. Tests cover: multi-word alias matching, mixed-case input, unknown tokens passed through as raw_descriptors, empty prompt → empty SignalSet with confidence 0.0
**Plans**: TBD

---

### Phase 43: Parameter Derivation Engine

**Goal**: The derivation engine translates a `SignalSet` into a fully-populated `ProductionBrief` — all five DERV-* requirements are implemented with deterministic rules and each derivation step appends a reasoning note; existing genre blueprints and sounds catalog are the only dependencies
**Depends on**: Phase 42
**Requirements**: DERV-01, DERV-02, DERV-03, DERV-04, DERV-05
**Success Criteria** (what must be TRUE):
  1. `deriver.derive("lo-fi hip hop beat")` returns a `ProductionBrief` where `primary_genre="lo_fi"`, `tempo_range=(60, 95)` (from lo-fi blueprint), `key_feel={"scale": "dorian", "mode": "minor"}`, `groove_feel={"pattern_type": "boom_bap", "swing_pct": 65}`, `energy_level=3`, `velocity_style="laid_back"`
  2. An explicit BPM number in the prompt ("140 BPM techno") overrides the genre BPM range with a ±5 window, landing at `tempo_range=(135, 145)`
  3. A mood override works: "euphoric trance" shifts key_feel toward major modes (Ionian or Lydian) rather than trance's default minor
  4. `instrument_hints` for "lo-fi hip hop beat" includes at minimum entries for vinyl_noise, piano/keys, bass, and drums — derived from the lo-fi blueprint's canonical roles merged with top sound descriptors
  5. The `reasoning` list has at least one entry per derived parameter explaining which signal triggered it (≥5 entries for a genre-only prompt)
**Plans**: TBD

---

### Phase 44: interpret_prompt and interpret_prompt_to_plan MCP Tools

**Goal**: Claude can call `interpret_prompt` to get a structured `ProductionBrief` from any music description, and call `interpret_prompt_to_plan` to go straight from text to a full production plan in one tool call — eliminating the current ad-hoc prompt-to-parameters reasoning step
**Depends on**: Phase 43
**Requirements**: TOOL-01, TOOL-02
**Success Criteria** (what must be TRUE):
  1. `interpret_prompt("dark minimal techno")` MCP tool returns a valid `ProductionBrief` JSON with all 10 fields populated and a non-empty `reasoning` list — callable from the MCP tool listing
  2. `interpret_prompt_to_plan("lo-fi hip hop beat")` MCP tool returns both the `ProductionBrief` and a full production plan (same shape as `generate_production_plan` output) in a single response dict — no intermediate tool calls needed
  3. Both tools are registered in `tools/__init__.py` and appear in the MCP tool listing returned by the server
  4. `pyproject.toml` includes `MCP_Server.prompt` in the packages list
  5. A prompt with no recognized signals returns a `ProductionBrief` with `primary_genre=null`, `confidence < 0.3`, and a reasoning entry explaining the low-confidence parse — tool does not raise an exception
**Plans**: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 42 -> 43 -> 44

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-13. MVP Foundation | v1.0 | 33/33 | Complete | 2026-03-23 |
| 14-19. Theory Engine | v1.1 | 12/12 | Complete | 2026-03-26 |
| 20-24. Genre Blueprints | v1.2 | 9/9 | Complete | 2026-03-27 |
| 25-28. Arrangement Intelligence | v1.3 | 8/8 | Complete | 2026-03-28 |
| 29-34. Mix/Master Intelligence | v1.4 | 11/11 | Complete | 2026-03-30 |
| 35. Package Skeleton and First Profile | v1.5 | 2/2 | Complete | 2026-03-31 |
| 36. Instrument Profile Authoring | v1.5 | 2/2 | Complete | 2026-03-31 |
| 37. Descriptor Taxonomy and Scoring Engine | v1.5 | 1/1 | Complete | 2026-03-31 |
| 38. Recommendation Tools and Registration | v1.5 | 1/1 | Complete | 2026-03-31 |
| 39. Evaluation Framework and Mix Balance Evaluator | v1.6 | 1/1 | Complete | 2026-03-31 |
| 40. Arrangement, Sound Selection, and Harmonic Evaluators | v1.6 | 1/1 | Complete | 2026-03-31 |
| 41. evaluate_session() Tool and Fix Offer Workflow | v1.6 | 1/1 | Complete | 2026-03-31 |
| 42. ProductionBrief Schema, Signal Lexicon, and Prompt Parser | v1.7 | 1/1 | Complete | 2026-03-31 |
| 43. Parameter Derivation Engine | v1.7 | 1/1 | Complete | 2026-03-31 |
| 44. interpret_prompt and interpret_prompt_to_plan MCP Tools | v1.7 | 1/1 | Complete | 2026-03-31 |
