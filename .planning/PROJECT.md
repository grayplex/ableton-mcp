# AbletonMCP

## What This Is

A comprehensive MCP (Model Context Protocol) server that gives AI assistants full control over Ableton Live 12 — including music theory intelligence. It bridges Claude (or any MCP-compatible client) to Ableton via a socket-based Remote Script, enabling AI-driven music production with harmonic awareness: composing, arranging, analyzing, mixing, and mastering.

## Core Value

An AI assistant can produce actual music in Ableton — instruments load, notes play, effects shape sound, and the mix comes together. Theory tools ensure compositions are harmonically informed, not brute-force guessing.

## Requirements

### Validated

- ✓ 53 v1.0 requirements — full Ableton Live 12 LOM coverage (tracks, clips, devices, MIDI, audio, routing, automation, scenes, transport, grooves) — v1.0
- ✓ THRY-01..03: music21 integration, theory module structure, MIDI ↔ note mapping — v1.1
- ✓ CHRD-01..05: Chord build/identify/invert/voice/diatonic (26 qualities) — v1.1
- ✓ SCLE-01..05: Scale catalog (38 scales), pitches, validation, detection, relationships — v1.1
- ✓ PROG-01..04: Progression catalog (25 genres), generation, Roman numeral analysis, suggestions — v1.1
- ✓ ANLY-01..03: Key detection, chord segmentation, harmonic rhythm analysis — v1.1
- ✓ VOIC-01..02: Voice-led chord connections and progression generation — v1.1
- ✓ RHYM-01..02: Rhythm pattern templates and chord-to-MIDI application — v1.1
- ✓ 23 v1.2 requirements — genre blueprint infrastructure, tools, 12 genres, palette bridge, quality gate — v1.2
- ✓ ARNG-01..03: ArrangementEntry schema extended with optional energy/roles/transition_in; all 12 genres + 4 subgenres fully authored — v1.3 Phase 25
- ✓ PLAN-01..03: generate_production_plan and generate_section_plan MCP tools with override support (resize/add/remove sections) — v1.3 Phase 26
- ✓ SCAF-01..02: scaffold_arrangement (writes locators + MIDI tracks to Arrangement view) and get_arrangement_overview (reads back arrangement state) MCP tools — v1.3 Phase 27
- ✓ EXEC-01..02: get_section_checklist (per-role instrument status for a named section) and get_arrangement_progress (tracks with no instrument loaded) MCP tools — v1.3 Phase 28
- ✓ CATL-01: Device parameter catalog — 12 built-in Ableton devices with 327 real parameters from live session; get_device_catalog MCP tool — v1.4 Phase 29
- ✓ ROLE-01: Role taxonomy — 9 canonical mixing roles; get_role_taxonomy MCP tool — v1.4 Phase 29
- ✓ RECIP-01: Core mix recipes — 4 genres × 9 roles, natural-unit parameter values for EQ/compression/reverb/panning/dynamics; get_mix_recipe MCP tool with alias support; pkgutil auto-discovery — v1.4 Phase 30
- ✓ BATCH-01: set_device_parameters RS command — batch parameter set in single socket round-trip; registered in _WRITE_COMMANDS — v1.4 Phase 31
- ✓ APPLY-01: apply_mix_recipe MCP tool — loads devices + converts natural-unit recipe to normalized payload + sends apply_recipe command in one call — v1.4 Phase 31
- ✓ APPLY-02: apply_master_recipe MCP tool — applies full GlueCompressor + MultibandDynamics + Limiter chain to master track; MASTER_RECIPE constants for 4 core genres — v1.4 Phase 31
- ✓ APPLY-03: apply_recipe RS handler with self_scheduling=True — recursive load + verify pattern guarantees atomicity; no race condition — v1.4 Phase 31
- ✓ SIDE-01: set_sidechain_source RS handler + MCP tool — resolves source track by name via case-insensitive substring match on routing display names — v1.4 Phase 31
- ✓ STATE-01: get_mix_state RS command + MCP tool — full device parameter snapshot for all tracks in one call — v1.4 Phase 32
- ✓ GAIN-01: check_gain_staging MCP tool — per-track dBFS estimates vs role-aware target ranges — v1.4 Phase 32
- ✓ GAIN-02: MIDI scaffold track exclusion in get_track_meters RS handler — v1.4 Phase 32
- ✓ INTEL-01: suggest_mix_adjustments MCP tool — diffs current device state against role×genre recipe; per-parameter suggestions with one-sentence reasoning; read-only, no auto-apply — v1.4 Phase 33
- ✓ RECIP-02: Full genre recipe expansion — 8 new genre recipe files (synthwave, dubstep, trance, future_bass, hip_hop_trap, disco_funk, neo_soul_rnb, lo_fi); pkgutil auto-discovery; all 12 genres available via get_mix_recipe — v1.4 Phase 34
- ✓ MSTR-01: Master bus recipes for all 12 genres — MASTER_RECIPE constants (GlueCompressor + MultibandDynamics + Limiter) per genre; dynamic _get_master_genres() replaces hardcoded list — v1.4 Phase 34
- ✓ EVAL-01..02: Evaluation issue schema (dimension/severity/message/fix_hint) and score model (DimensionScore + SessionScore TypedDicts with grade_from_score()) — v1.6 Phase 39
- ✓ MIX-01..02: Mix balance evaluator — recipe-vs-current param diff with DIFF/CRITICAL thresholds; DimensionScore 0-10 from in-range % + gain staging deviations — v1.6 Phase 39
- ✓ ARNG-01: Arrangement completeness evaluator — scaffold tracks checked for instrument (critical) and clips (warning); weighted scoring — v1.6 Phase 40
- ✓ SND-01: Sound selection coverage evaluator — role→instrument match via sounds catalog descriptor affinities — v1.6 Phase 40
- ✓ HARM-01: Harmonic coherence evaluator — in-key pitch class check via pure integer arithmetic; empty key → graceful info skip — v1.6 Phase 40
- ✓ SESS-01..02: evaluate_session() MCP tool — 4-dimension composite score (0-10, A-F grade), critical-first issue sort, top_fixes list with specific MCP tool calls — v1.6 Phase 41

### Active

- PARS-01: Prompt signal extractor — tokenizes free-text and classifies into genre/mood/instrument/effect/structural signal types — v1.7
- LEX-01: Signal lexicon — 12 genres + aliases, 25+ mood adjectives, 15+ instrument refs, 10+ effect refs, 5+ tempo signals — v1.7
- BRIEF-01: ProductionBrief TypedDict schema — tempo_range, key_feel, groove_feel, energy_level, instrument_hints, effect_hints, velocity_style, confidence, reasoning — v1.7
- DERV-01: Tempo derivation — explicit BPM or genre blueprint range + energy modifier — v1.7
- DERV-02: Key feel derivation — genre convention + mood signal override — v1.7
- DERV-03: Groove derivation — pattern_type + swing_pct from genre + structural hints — v1.7
- DERV-04: Instrument hints — explicit prompt refs merged with genre blueprint roles + sound descriptors — v1.7
- DERV-05: Velocity style — derived from energy level, overridable by prompt signals — v1.7
- TOOL-01: interpret_prompt(text) MCP tool — returns ProductionBrief + reasoning — v1.7
- TOOL-02: interpret_prompt_to_plan(text) MCP tool — interpret_prompt → generate_production_plan in one call — v1.7


### Out of Scope

- Mobile app — desktop DAW integration only
- Audio generation/synthesis — Ableton handles audio; MCP handles control
- Real-time audio streaming — MCP is command/response, not audio pipeline
- Non-Ableton DAWs — Ableton Remote Script API is the foundation

## Current Milestone: v1.7 Prompt Interpretation (active 2026-03-31)


**Goal:** Formalize Claude's natural-language music prompt reasoning into a structured, repeatable planning step — so "lo-fi hip hop beat" consistently yields concrete parameters (tempo range, scale/mode, groove pattern, instrument hints, effect hints, velocity style) via a deterministic derivation engine rather than ad-hoc in-context reasoning.

**Phases:** 42 (ProductionBrief schema + signal lexicon + parser), 43 (parameter derivation engine), 44 (MCP tools: interpret_prompt + interpret_prompt_to_plan)

## Completed Milestone: v1.6 Self-evaluation (shipped 2026-03-31)

**Delivered:** Production self-evaluation — `evaluate_session(genre)` MCP tool evaluates mix balance, arrangement completeness, sound selection coverage, and harmonic coherence; returns composite score (0-10 + letter grade), ranked issues, and up to 3 `top_fixes` with specific MCP tool calls.

## Completed Milestone: v1.5 Sound Selection Intelligence (shipped 2026-03-31)

**Delivered:** Instrument-selection intelligence — 6 native Ableton instrument profiles (Wavetable, Analog, Operator, Drift, Simpler, Drum Rack) with sonic character, descriptor affinities, and browser category paths; weighted-sum scoring engine; `get_sound_recommendation`, `list_sound_descriptors`, and `get_instrument_profile` MCP tools.

## Completed Milestone: v1.4 Mix/Master Intelligence (shipped 2026-03-30)

**Delivered:** Full mixing and mastering intelligence — device parameter catalog (327 params, 12 devices), role×genre recipes for all 12 genres, one-call recipe application with atomic device loading, session mix state snapshot, gain staging analysis, and AI-driven parameter adjustment suggestions.

## Completed Milestone: v1.3 Arrangement Intelligence (shipped 2026-03-28)

**Goal:** Give Claude a systematic production workflow — plan sections from genre conventions, encode the plan into Ableton, and execute section-by-section without dropping the ball at tool call #40.

**Delivered:**
- Arrangement templates in genre blueprints (section names, bar counts, energy curve, per-section elements, automation cues)
- Production plan builder: genre + vibe → full section plan or single-section plan on demand
- Session scaffolding: locators + named tracks written into Ableton Arrangement view (the session IS the plan)
- Section execution checklists: methodical per-section execution (kick, bass, riser, filter sweep...) — nothing skipped under context pressure
- Arrangement progress check: identifies scaffolded MIDI tracks with no instrument loaded

## Completed Milestone: v1.2 Genre/Style Blueprints (shipped 2026-03-27)

Curated genre reference documents giving Claude consistent knowledge of 12 electronic music genres — instrumentation, harmony, rhythm, arrangement, and mixing — delivered via MCP server with theory engine integration.

## Current State

**Milestone v1.7 active** (2026-03-31) — Prompt Interpretation in progress

- **Self-evaluation**: `MCP_Server/evaluation/` package with 4 evaluators + `evaluate_session()` MCP tool; 40 tests
- **Sound selection**: sounds/ package with 6 instrument profiles + weighted-sum scoring engine + 3 MCP tools
- **Mix/master intelligence**: 12-genre recipe system + apply tools + gain staging + adjustment suggestions
- **~46,500 lines Python** total codebase (estimated)
- **144 requirements** complete (53 v1.0 + 24 v1.1 + 23 v1.2 + 10 v1.3 + 14 v1.4 + 11 v1.5 + 9 v1.6 = 144 — see REQUIREMENTS archives)
- **12 genre mix recipes** with 9 roles each + master bus recipes (GlueCompressor + MultibandDynamics + Limiter)
- **MCP tools**: `get_device_catalog`, `get_role_taxonomy`, `get_mix_recipe`, `apply_mix_recipe`, `apply_master_recipe`, `set_sidechain_source`, `get_mix_state`, `check_gain_staging`, `suggest_mix_adjustments`, `get_sound_recommendation`, `list_sound_descriptors`, `get_instrument_profile`, `evaluate_session`

### Capabilities

| Domain | Tools | Description |
|--------|-------|-------------|
| Track Management | 15 | MIDI/audio/return/group CRUD, rename, color, info |
| Mixing Controls | 9 | Volume, pan, mute, solo, arm, sends, crossfader |
| Clip Management | 12 | Create, delete, duplicate, launch, stop, loop, color |
| MIDI Editing | 12 | Notes CRUD, quantize, transpose, note expression, ID ops |
| Device & Browser | 30 | Load instruments/effects, parameters, Racks, Simpler, DrumPad |
| Scene & Transport | 23 | Scenes, playback, tempo, time sig, loop, undo/redo, cue points |
| Automation | 3 | Envelope read/write/clear |
| Routing | 6 | Input/output routing types and assignment |
| Audio Clips | 8 | Pitch, gain, warp, warp markers, session audio creation |
| Arrangement | 4 | MIDI/audio clip creation, listing, session-to-arrangement |
| Groove Pool | 3 | List, parameters, clip association |
| Session | 10+ | Scale/key, capture, metronome, recording, session state |
| Theory | 23 | Chords, scales, progressions, analysis, voice leading, rhythm |

### Architecture

Two-tier: MCP server (FastMCP/Python 3) ↔ TCP socket (length-prefix framing) ↔ Remote Script (Python 3.11 in Ableton)

- Remote Script uses mixin classes with `@command` decorator registry
- MCP server uses domain-organized tool modules
- Theory engine: `MCP_Server/theory/` library with music21 backend
- Genre blueprints: `MCP_Server/genres/` package with auto-discovery catalog
- Thread-safe connection with `threading.Lock`
- Dict-based command dispatch (no if/elif chains)

## Constraints

- **Ableton Remote Script API**: Must work within Ableton's `_Framework` / Live API
- **Thread safety**: All Ableton API calls must happen on the main thread via `schedule_message()`
- **Socket protocol**: JSON over TCP on localhost:9877
- **Python 3.11**: Remote Script runs in Ableton's embedded Python 3.11
- **MCP protocol**: Server conforms to Model Context Protocol spec (FastMCP framework)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Extend existing codebase rather than rebuild | Architecture is sound; rebuilding wastes effort | ✓ Good — 19 phases built on foundation |
| Python 3 only, strip all Py2 compat | Ableton Live 12 = Python 3.11 | ✓ Good — cleaner code, modern idioms |
| Mixin class pattern for handlers | Domain isolation + single inheritance chain | ✓ Good — scales to 15 modules cleanly |
| Length-prefix framing protocol | Eliminates JSON-completeness parsing bugs | ✓ Good — zero framing errors |
| Comprehensive LOM coverage | Users want full production capability | ✓ Good — 178 commands covering most LOM |
| music21 as theory engine | Deep, battle-tested music theory library; avoids reinventing chord/scale/analysis logic | ✓ Good — 23 functions, all validated |
| Theory logic server-side only | No Remote Script changes needed; theory is computation, not Ableton API | ✓ Good — zero Remote Script modifications |
| Granular theory tools (23) | Individual tools vs. composite mega-tools; better AI tool selection | ✓ Good — clean separation of concerns |
| Interval-based scale construction | No music21 class dependency for scales; pitch class set comparison | ✓ Good — 38 scales, fast detection |
| Permutation-based voice leading | O(n!) but n≤5 notes; simpler than constraint solver | ✓ Good — real-time performance |
| Genre blueprints as Python dicts | Matches existing data patterns (scales.py, progressions.py); auto-discovery via pkgutil | ✓ Good — 12 genres, zero registration code |
| One file per genre with subgenres | Genre + subgenres co-located; catalog handles merge | ✓ Good — scales to 12 genres cleanly |
| Palette bridge returns names only | Claude has existing tools for MIDI resolution; keeps palette output lightweight | ✓ Good — clean separation of concerns |
| tiktoken for token budget measurement | Standard LLM tokenizer; reproducible counts; dev-only dependency | ✓ Good — all blueprints 537-670 tokens |

## Context

- v1.0–v1.4 milestones archived at `.planning/milestones/`
- Codebase map at `.planning/codebase/`

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-31 — v1.7 Prompt Interpretation milestone opened*
