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

### Active

(v1.3 complete — see REQUIREMENTS.md for full traceability)

### Out of Scope

- Mobile app — desktop DAW integration only
- Audio generation/synthesis — Ableton handles audio; MCP handles control
- Real-time audio streaming — MCP is command/response, not audio pipeline
- Non-Ableton DAWs — Ableton Remote Script API is the foundation

## Current Milestone: v1.3 Arrangement Intelligence

**Goal:** Give Claude a systematic production workflow — plan sections from genre conventions, encode the plan into Ableton, and execute section-by-section without dropping the ball at tool call #40.

**Target features:**
- Arrangement templates in genre blueprints (section names, bar counts, energy curve, per-section elements, automation cues)
- Production plan builder: genre + vibe → full section plan or single-section plan on demand
- Session scaffolding: locators + named tracks written into Ableton Arrangement view (the session IS the plan)
- Section execution checklists: methodical per-section execution (kick, bass, riser, filter sweep...) — nothing skipped under context pressure
- Either mode: full track end-to-end OR targeted single section

## Completed Milestone: v1.2 Genre/Style Blueprints (shipped 2026-03-27)

Curated genre reference documents giving Claude consistent knowledge of 12 electronic music genres — instrumentation, harmony, rhythm, arrangement, and mixing — delivered via MCP server with theory engine integration.

## Current State

**Shipped: v1.1 Theory Engine** (2026-03-26)
**Shipped: v1.2 Genre/Style Blueprints** (2026-03-27) — Phases 20-24 complete

- **200 MCP tools** across 18 tool modules (added `list_genre_blueprints`, `get_genre_blueprint`, `get_genre_palette`)
- **178 Remote Script handler commands** across 15 domain modules
- **23 theory functions** in 6 library modules (pitch, chords, scales, progressions, analysis, voicing/rhythm)
- **12-genre catalog complete** — all genres validated against theory engine
- **148 genre tests** (palette bridge + quality gate) + 204 v1.0 + 224 theory — all passing
- **100 requirements** complete (53 v1.0 + 24 v1.1 + 23 v1.2)
- **12 genre blueprints**: house, techno, hip-hop/trap, ambient, DnB, dubstep, trance, neo-soul/R&B, synthwave, lo-fi, future bass, disco/funk

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

- v1.0 milestone archived at `.planning/milestones/v1.0-ROADMAP.md`
- v1.1 milestone archived at `.planning/milestones/v1.1-ROADMAP.md`
- v1.2 milestone archived at `.planning/milestones/v1.2-ROADMAP.md`
- Codebase map at `.planning/codebase/`

---
*Last updated: 2026-03-27 — v1.3 Arrangement Intelligence milestone started*
