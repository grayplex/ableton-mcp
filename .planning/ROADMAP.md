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
| v1.8 Iterative Refinement Protocol | 45-47 | 3 | 8 | Complete | 2026-03-31 |
| v1.9 Orchestration/Agent Loop | 48-51 | TBD | 8 | Active | — |

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

### v1.8 Iterative Refinement Protocol

**Milestone Goal:** Give Claude the ability to take a follow-up instruction like "make the bridge darker" and act on it correctly — reading back the current section state, interpreting the aesthetic instruction in context (darker: lower register, minor substitutions, filter highs, heavier compression), and surgically modifying just that section's notes and devices without touching anything outside it.

---

### Phase 45: Section State Reader

**Goal**: Claude can read back everything it already built in a named arrangement section — clips, notes, devices, and mix context — in a single structured snapshot; no refinement logic yet, just a reliable read
**Depends on**: Nothing (first phase of v1.8)
**Requirements**: SNAP-01, SNAP-02
**Success Criteria** (what must be TRUE):
  1. `MCP_Server/refinement/` package exists with `__init__.py` and `schema.py` (SectionState, TrackStateEntry, ClipSummary TypedDicts)
  2. `get_section_state("Bridge")` MCP tool resolves the Bridge locator bar range from `get_arrangement_overview`, then collects all clips in that range across all tracks with note summaries (pitch_min, pitch_max, note_count, dominant_octave)
  3. Each `TrackStateEntry` includes `mix_context` with current device names, 3 prominent parameter values per recognized device type, and `recipe_delta` if the track role + genre recipe are resolvable
  4. Calling `get_section_state` on a section with no clips returns `{"section": "Bridge", "tracks": [], "error": null}` — no exception
  5. Tests cover: section not found → descriptive error; section with 2 tracks × 3 clips each → correct clip counts; mix_context populated for a track with a Compressor device
**Plans**: TBD

---

### Phase 46: Refinement Language Engine

**Goal**: Claude can interpret "make the bridge darker" or "add more swing" into a concrete `SectionRefinementPlan` — specific note operations and device parameter targets per track — and update an existing `ProductionBrief` via follow-up refinement text
**Depends on**: Phase 45 (uses `get_section_state`)
**Requirements**: REFN-01, REFN-02, PARS-02
**Success Criteria** (what must be TRUE):
  1. `MCP_Server/refinement/lexicon.py` defines `REFINEMENT_LEXICON` with ≥20 adjectives mapped to `RefinementVector` TypedDicts covering harmonic, timbral, and dynamic dimensions; "darker" maps to `{harmonic: {register_shift_semitones: -3, mode_bias: "minor"}, timbral: {filter_cutoff_delta_pct: -25, brightness_db: -2}, dynamic: {velocity_shift: -8}}`
  2. `interpret_section_refinement("Bridge", "make it darker")` MCP tool returns a `SectionRefinementPlan` listing per-track note operations and device parameter targets derived from current section state + RefinementVector
  3. `SectionRefinementPlan.reasoning` has ≥1 entry per affected track explaining which adjective triggered which change
  4. `refine_prompt(brief_dict, "make it faster and darker")` MCP tool returns an updated `ProductionBrief` where `tempo_range` and `key_feel` changed but `primary_genre`, `groove_feel`, and `instrument_hints` are unchanged — with a `diff` dict showing exactly which fields changed
  5. Unrecognized refinement instruction returns a plan with empty track changes and a reasoning entry explaining no signals were matched — no exception
**Plans**: TBD

---

### Phase 47: Refinement Application Tools

**Goal**: Claude can execute a refinement end-to-end — "make the bridge darker" applies the note and device changes to only the Bridge section and returns a plain-English summary of exactly what changed
**Depends on**: Phase 46 (uses `SectionRefinementPlan`)
**Requirements**: RFNA-01, RFNA-02, RFNA-03
**Success Criteria** (what must be TRUE):
  1. `apply_section_note_refinement("Bridge", "Pad", semitone_shift=-3, density_delta=0, scale_substitutions=[])` transposes all notes in Bridge-range clips on the Pad track down 3 semitones and returns `{"clips_modified": N, "notes_modified": M}` — clips outside the Bridge bar range are untouched
  2. `apply_section_device_refinement("Bridge", "Pad", param_targets={"Auto Filter": {"Frequency": 0.35}}, write_automation=True)` writes automation breakpoints at Bridge start/end that interpolate to the target value and restore pre-refinement value at the section boundary — confirmed by a post-call `get_automation_data` check showing the correct envelope shape
  3. `refine_section("Bridge", "make it darker", genre="house")` end-to-end call returns a result with `tracks_modified`, `note_changes`, `device_changes`, and `reasoning`; internally calls interpret and apply without requiring separate tool calls
  4. `refine_section` on an empty section returns `{"tracks_modified": 0, "reasoning": ["No clips found in Bridge — nothing to refine"]}` — no exception
  5. All three tools are registered in `tools/__init__.py` and appear in the MCP tool listing
**Plans**: TBD

---

### v1.9 Orchestration/Agent Loop

**Milestone Goal:** Give Claude a methodical execution layer for full productions — an agenda of named phases, a concrete tool-call checklist per phase, a checkpoint that reads live Ableton state to determine exactly where the production is, and a next-actions recommender that returns specific ordered tool calls so Claude spends no context budget on "what should I do?" reasoning.

---

### Phase 48: Production Agenda Schema and Genre Phase Catalog

**Goal**: The orchestration package exists — `ProductionAgenda` and `ProductionPhase` TypedDicts defined, a genre phase catalog covering all 12 genres with ordered phase lists, and `get_production_agenda` MCP tool returning a token-efficient agenda for any genre; no execution or checkpoint logic yet
**Depends on**: Nothing (first phase of v1.9)
**Requirements**: AGND-01, AGND-02
**Success Criteria** (what must be TRUE):
  1. `MCP_Server/orchestration/` package exists with `__init__.py`, `schema.py` (ProductionPhase, ProductionAgenda, ExecutionStep, PhaseChecklist, ProductionCheckpoint TypedDicts), and `agenda.py` (genre phase catalog + get_production_agenda logic)
  2. `get_production_agenda("techno")` returns an agenda with phases in genre-appropriate order: setup → drums → bass → sound_design → arrangement → mix → master
  3. All 12 genres have defined phase orderings; melodic genres (ambient, neo_soul_rnb) emphasize harmony/melody phases; rhythmic genres (techno, house, dnb) lead with drums/bass
  4. `brief` parameter accepted; when brief has `energy_level >= 7`, drums phase listed first (before setup would otherwise defer it); when `primary_genre` in brief overrides the genre arg, brief's genre wins
  5. Total JSON output ≤400 tokens; `total_estimated_steps` is the sum of each phase's `estimated_steps`
**Plans**: TBD

---

### Phase 49: Phase Execution Plan Engine

**Goal**: Claude can call `get_phase_execution_plan` for any phase and receive a concrete ordered list of `ExecutionStep` entries with tool names and genre-appropriate suggested args — eliminating the need for Claude to reason about "what tool call exactly?" for each production step
**Depends on**: Phase 48
**Requirements**: EXEC-01, EXEC-02
**Success Criteria** (what must be TRUE):
  1. `get_phase_execution_plan("drums", "house")` returns a `PhaseChecklist` with ≥6 ordered `ExecutionStep` entries: create MIDI track → load Drum Rack → add kick notes on beats 1/2/3/4 → add clap on beats 2/4 → add open hi-hat on off-beats → add closed hi-hat → quantize
  2. `get_phase_execution_plan("mix", "techno")` returns steps: apply_mix_recipe per role → check_gain_staging → suggest_mix_adjustments → apply_master_recipe — each step has `tool_name` and `suggested_args` populated with real tool names that match the MCP server's tool listing
  3. `section_name` parameter scopes note-writing steps: when `section_name="Drop"` is provided, steps that write notes include the section's bar range in `suggested_args`
  4. Every `ExecutionStep` has a non-empty `description` (plain English), a `tool_name` matching a real registered MCP tool, and `suggested_args` with at minimum the required parameters for that tool call
  5. Total checklist JSON ≤500 tokens; steps that reference session-state values (track index) use `"<track_index>"` sentinel with explanation in description
**Plans**: TBD

---

### Phase 50: Production Checkpoint System

**Goal**: Claude can call `get_production_checkpoint` at any moment during a production to get a compact, accurate summary of what phases are complete, what is active, and a single-sentence resume hint — so a context reset doesn't mean losing the thread
**Depends on**: Phase 48
**Requirements**: CHKP-01, CHKP-02
**Success Criteria** (what must be TRUE):
  1. `ProductionCheckpoint` TypedDict in `schema.py` with fields: `genre`, `completed_phases`, `active_phase`, `active_phase_progress` (0.0–1.0 float), `pending_steps`, `session_stats`, `next_phase`, `resume_hint`; serializes to ≤300 tokens of JSON
  2. `get_production_checkpoint("house")` on a session with 4 tracks (Kick, Bass, Chords, Pad), all with instruments loaded and arrangement clips, correctly infers `completed_phases` includes "setup", "drums", "bass", "harmony"; `active_phase` is either "melody" or "arrangement"
  3. Phase completion heuristics cover at minimum: setup (tracks exist), drums (Drum Rack present + clips), bass (bass-named track with clips), harmony (chord/pad track with ≥4-note clips), mix (EQ Eight + Compressor present on ≥1 track), master (GlueCompressor + Limiter on master track)
  4. An empty session returns `{completed_phases: [], active_phase: "setup", active_phase_progress: 0.0, resume_hint: "Session is empty — start with setup: set tempo, set key, and scaffold tracks"}`
  5. `resume_hint` is always a single human-readable sentence; it names the specific next action (not just "continue the production")
**Plans**: TBD

---

### Phase 51: Next-Action Recommender and Phase Transition Gate

**Goal**: Claude can call `get_next_actions` to receive the next N specific, immediately-executable tool calls for a production — and `get_phase_transition_guidance` to get a go/no-go verdict before advancing phases; together these two tools make the agent loop self-directing
**Depends on**: Phase 49, Phase 50
**Requirements**: NEXT-01, NEXT-02
**Success Criteria** (what must be TRUE):
  1. `get_next_actions("house")` reads the checkpoint internally and returns `{checkpoint_summary: str, steps: list[ExecutionStep]}` where steps are the next ≤10 actions from the active phase checklist; calling it on a session mid-way through drum programming skips steps already inferred-complete (kick present → skip add-kick step)
  2. `get_next_actions("house", phase_name="mix")` bypasses checkpoint and returns the full mix phase checklist regardless of session state
  3. `get_next_actions("techno", n=5)` returns exactly 5 steps
  4. `get_phase_transition_guidance("drums", genre="house")` returns `{ready_to_advance: True, completion_pct: 1.0, blockers: [], next_phase: "bass"}` when a Drum Rack with arrangement clips is present; returns `{ready_to_advance: False, completion_pct: 0.4, blockers: ["No clips found in arrangement for Drums track"], fix_hints: ["Call get_phase_execution_plan('drums', 'house') and execute the note-writing steps"]}` when drum track exists but has no clips
  5. Both tools are registered in `tools/__init__.py`, appear in the MCP tool listing, and are importable from `MCP_Server.orchestration`
**Plans**: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 42 -> 43 -> 44 -> 45 -> 46 -> 47 -> 48 -> 49 -> 50 -> 51

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
| 45. Section State Reader | v1.8 | 1/1 | Complete | 2026-03-31 |
| 46. Refinement Language Engine | v1.8 | 1/1 | Complete | 2026-03-31 |
| 47. Refinement Application Tools | v1.8 | 1/1 | Complete | 2026-03-31 |
| 48. Production Agenda Schema and Genre Phase Catalog | v1.9 | 0/TBD | Pending | — |
| 49. Phase Execution Plan Engine | v1.9 | 0/TBD | Pending | — |
| 50. Production Checkpoint System | v1.9 | 0/TBD | Pending | — |
| 51. Next-Action Recommender and Phase Transition Gate | v1.9 | 0/TBD | Pending | — |
