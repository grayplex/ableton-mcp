# AbletonMCP

## What This Is

A comprehensive MCP (Model Context Protocol) server that gives AI assistants full control over Ableton Live 12. It bridges Claude (or any MCP-compatible client) to Ableton via a socket-based Remote Script, enabling AI-driven music production — from composing and arranging to mixing and mastering.

## Core Value

An AI assistant can produce actual music in Ableton — instruments load, notes play, effects shape sound, and the mix comes together. If the tools exist but nothing plays, the whole thing is worthless.

## Current State

**Shipped: v1.0** (2026-03-23)

The server is production-quality with comprehensive Ableton Live 12 coverage:
- **178 Remote Script handler commands** across 15 domain modules
- **174 MCP tools** across 15 tool modules
- **204 tests** (all passing)
- **53 v1 requirements** — all complete

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

### Architecture

Two-tier: MCP server (FastMCP/Python 3) ↔ TCP socket (length-prefix framing) ↔ Remote Script (Python 3.11 in Ableton)

- Remote Script uses mixin classes with `@command` decorator registry
- MCP server uses domain-organized tool modules
- Thread-safe connection with `threading.Lock`
- Dict-based command dispatch (no if/elif chains)

## Next Milestone Goals

**v1.1 — Theory Engine**

Add a comprehensive music theory intelligence layer powered by music21 so Claude can compose with harmonic awareness — building chords, generating progressions, analyzing existing clips, and applying voice leading rules. All theory logic lives server-side in MCP_Server; no Remote Script changes needed.

**Goals:**
- Chord building: triads, 7ths, extended, altered, inversions, voicings (close/open/drop-2)
- Scale & mode exploration: all scales/modes, degree generation, scale detection from notes
- Progression engine: common templates by genre, Roman numeral analysis, next-chord suggestion
- Harmonic analysis: key detection from clip notes, chord segmentation, harmonic rhythm analysis
- Voice leading: smooth chord connections, voice-led progression generation
- Rhythm patterns: arpeggios, bass lines, comping patterns applied to chord progressions
- Deep music21 integration as the core theory engine
- 15-25 new granular MCP tools in a dedicated theory module

## Constraints

- **Ableton Remote Script API**: Must work within Ableton's `_Framework` / Live API
- **Thread safety**: All Ableton API calls must happen on the main thread via `schedule_message()`
- **Socket protocol**: JSON over TCP on localhost:9877
- **Python 3.11**: Remote Script runs in Ableton's embedded Python 3.11
- **MCP protocol**: Server conforms to Model Context Protocol spec (FastMCP framework)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Extend existing codebase rather than rebuild | Architecture is sound; rebuilding wastes effort | Validated — 13 phases built on foundation |
| Python 3 only, strip all Py2 compat | Ableton Live 12 = Python 3.11 | Validated — cleaner code, modern idioms |
| Mixin class pattern for handlers | Domain isolation + single inheritance chain | Validated — scales to 15 modules cleanly |
| Length-prefix framing protocol | Eliminates JSON-completeness parsing bugs | Validated — zero framing errors |
| Comprehensive LOM coverage | Users want full production capability | Validated — 178 commands covering most LOM |
| music21 as theory engine | Deep, battle-tested music theory library; avoids reinventing chord/scale/analysis logic | Pending — v1.1 |
| Theory logic server-side only | No Remote Script changes needed; theory is computation, not Ableton API | Pending — v1.1 |
| Granular theory tools | 15-25 individual tools vs. composite mega-tools; better AI tool selection | Pending — v1.1 |

## Context

A codebase map exists at `.planning/codebase/` with architecture, stack, and convention analysis.
v1.0 milestone archived at `.planning/milestones/` with full roadmap and requirements history.

---
*Last updated: 2026-03-23 — v1.1 milestone defined*
