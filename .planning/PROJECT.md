# AbletonMCP

## What This Is

A comprehensive MCP (Model Context Protocol) server that gives AI assistants full control over Ableton Live 12. It bridges Claude (or any MCP-compatible client) to Ableton via a socket-based Remote Script, enabling AI-driven music production — from composing and arranging to mixing and mastering.

## Core Value

An AI assistant can produce actual music in Ableton — instruments load, notes play, effects shape sound, and the mix comes together. If the tools exist but nothing plays, the whole thing is worthless.

## Requirements

### Validated

- [x] Full track management (MIDI, audio, return, group, master) — Validated in Phase 2
- [x] Comprehensive MIDI editing (notes, quantize, transpose, velocity) — Validated in Phase 4
- [x] Mixing controls (volume, pan, sends, EQ) — Validated in Phase 5
- [x] Device chain management (add, remove, configure effects and instruments) — Validated in Phase 6
- [x] Scene management (create, launch, organize) — Validated in Phase 7
- [x] Transport and playback control — Validated in Phase 1
- [x] Browser navigation and preset loading — Validated in Phase 3
- [x] Instrument and effect loading — Validated in Phase 3
- [x] Undo/redo support — Validated in Phase 8
- [x] Automation (parameter envelopes) — Validated in Phase 9
- [x] Clean, installable package for open-source distribution — Validated in Phase 10
- [x] LOM gap analysis and v2 requirements — Validated in Phase 11

### Active

- [ ] Clip creation, editing, and arrangement (Session and Arrangement views)
- [ ] Export/render capabilities
- [ ] Python 3 only — no Python 2 compatibility code
- [ ] Production-ready error handling and connection management
- [ ] v2 LOM coverage — 58 new requirements across 13 categories (Arrangement, Scale & Key, Clip Launch, Note Expression, Scene Extended, Device Extended, Simpler, Audio Creation, Groove, Mixer Extended, DrumPad Extended, Session, Track Advanced)

### Out of Scope

- Max for Live device development — too complex, different domain
- Audio recording from external inputs — requires hardware config beyond MCP scope
- Real-time audio processing/DSP — MCP latency makes this impractical
- Video features — Ableton's video support is minimal and not worth exposing

## Context

There's an existing codebase with a working but limited MCP server (~15 tools) and a Remote Script. The architecture is sound (two-tier: MCP server ↔ socket ↔ Remote Script), but:

- **Instrument loading is broken** — `load_browser_item` doesn't reliably load instruments onto tracks, resulting in silent MIDI clips
- **Python 2 remnants** — `from __future__` imports, Queue compatibility hacks, old-style class initialization
- **Limited coverage** — basic track/clip/playback only; no mixing, no arrangement, no automation, no export
- **Fragile error handling** — connection drops aren't recovered gracefully

Ableton Live 12 ships with Python 3.11 for Remote Scripts. There is zero reason to support Python 2.

A codebase map exists at `.planning/codebase/` with architecture, stack, and convention analysis.

## Constraints

- **Ableton Remote Script API**: Must work within Ableton's `_Framework` / Live API — undocumented, reverse-engineered from community knowledge
- **Thread safety**: All Ableton API calls must happen on the main thread via `schedule_message()`
- **Socket protocol**: Communication between MCP server and Remote Script uses JSON over TCP on localhost:9877
- **Python 3.11**: Remote Script runs in Ableton's embedded Python 3.11; MCP server uses system Python 3
- **MCP protocol**: Server must conform to Model Context Protocol spec (using FastMCP framework)
- **Installable**: Must be pip-installable with clear setup instructions for the Remote Script side

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Extend existing codebase rather than rebuild | Architecture is sound; rebuilding wastes effort on solved problems | — Pending |
| Python 3 only, strip all Py2 compat | Ableton Live 12 = Python 3.11, no legacy users to support | — Pending |
| Comprehensive API coverage (every Ableton action) | Users want full production capability, not a demo | — Pending |
| Open-source quality | Polished enough for others to install and use | — Pending |

## Current State

Phase 11 complete — LOM gap analysis produced 78 gaps across 12 classes, note expression correctness fix shipped, 58 v2 requirements added to REQUIREMENTS.md. All 11 phases of v1.0 milestone complete. Ready for milestone completion or v2 planning.

---
*Last updated: 2026-03-18 after Phase 11 completion*
