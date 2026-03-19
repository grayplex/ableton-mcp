# Roadmap: AbletonMCP

## Overview

This roadmap transforms an existing but broken MCP server into a production-quality Ableton Live 12 bridge. The journey moves in three arcs: first, repair the foundation so the server is reliable (Phases 1-2); second, expand coverage across every production domain (Phases 3-8); third, add advanced capabilities that differentiate from competing implementations (Phases 9-10). Every phase delivers a coherent, verifiable capability — nothing is a pure "all models then all APIs" layer cake.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation Repair** - Fix the broken correctness issues that make the current server unreliable (completed 2026-03-13)
- [x] **Phase 2: Infrastructure Refactor** - Build extensible architecture before feature expansion (completed 2026-03-14)
- [x] **Phase 3: Track Management** - Full track type coverage (MIDI, audio, return, group) (completed 2026-03-14)
- [x] **Phase 4: Mixing Controls** - Complete mixer surface (volume, pan, mute, solo, sends) (completed 2026-03-14)
- [x] **Phase 5: Clip Management** - Full clip lifecycle (create, edit, loop, launch, delete) (completed 2026-03-14)
- [x] **Phase 6: MIDI Editing** - Complete MIDI note editing (add, read, remove, quantize, transpose) (completed 2026-03-14)
- [x] **Phase 7: Device & Browser** - Working instrument loading plus full device parameter control (completed 2026-03-14)
- [x] **Phase 8: Scene & Transport** - Scene management plus complete transport and session control (completed 2026-03-15)
- [x] **Phase 9: Automation** - Clip automation envelopes for parameter movement (completed 2026-03-16)
- [x] **Phase 10: Routing & Audio Clips** - Track routing control and audio clip properties (completed 2026-03-17)
- [x] **Phase 11: Check for Live Object Model Gaps** - LOM gap analysis, correctness fixes, requirements update (completed 2026-03-18)

## Phase Details

### Phase 1: Foundation Repair
**Goal**: The server handles errors visibly, instrument loading works reliably, and concurrent tool calls do not crash
**Depends on**: Nothing (first phase)
**Requirements**: FNDN-01, FNDN-02, FNDN-03, FNDN-04, FNDN-05, FNDN-06
**Success Criteria** (what must be TRUE):
  1. Loading an instrument onto a MIDI track results in audible sound when notes play — no silent clips
  2. Running two MCP tool calls simultaneously does not crash or corrupt the connection
  3. Any failure in a tool call surfaces an error message — no silent pass-through
  4. The Remote Script communicates with the MCP server using length-prefix framing without parsing errors
  5. All Python 2 compatibility code is absent from the codebase — no `from __future__`, no `Queue as queue`, no `decode()` try/except
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Python 3 cleanup: strip Py2 code, upgrade to Py3.11 idioms, replace bare excepts, set up test infrastructure
- [x] 01-02-PLAN.md — Protocol and concurrency: length-prefix framing on both sides, threading.Lock, remove time.sleep delays, ping command
- [x] 01-03-PLAN.md — Dispatch and reliability: dict-based command router, fix instrument loading, browser typo fix, health-check tool

### Phase 2: Infrastructure Refactor
**Goal**: The codebase is organized into domain modules with a scalable dispatch architecture ready to accept 50+ commands
**Depends on**: Phase 1
**Requirements**: FNDN-07, FNDN-08, FNDN-09, FNDN-10
**Success Criteria** (what must be TRUE):
  1. Adding a new MCP tool requires touching exactly one domain module and one handler file — no monolithic files to edit
  2. The Remote Script dispatches commands via dict lookup — no if/elif chain exists
  3. Linting passes with ruff on both the MCP server and Remote Script codebases
  4. A test suite with pytest can run smoke tests against the server using FastMCP in-memory client
**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md — Extract Remote Script handlers into domain package with @command decorator registry (base, transport, tracks, clips, notes, devices, mixer, scenes, browser)
- [x] 02-02-PLAN.md — Split MCP_Server/server.py into connection.py, protocol.py, and tools/ domain modules with standardized tool names and docstrings
- [x] 02-03-PLAN.md — Configure ruff linting and build pytest + FastMCP in-memory smoke test infrastructure across all domains

### Phase 3: Track Management
**Goal**: Users can create, configure, and inspect every track type that Ableton supports
**Depends on**: Phase 2
**Requirements**: TRCK-01, TRCK-02, TRCK-03, TRCK-04, TRCK-05, TRCK-06, TRCK-07, TRCK-08, TRCK-09
**Success Criteria** (what must be TRUE):
  1. User can create a MIDI track, an audio track, a return track, and a group track — each appears in Ableton's track list
  2. User can delete any track and it disappears from the session
  3. User can duplicate a track and the copy appears with its contents intact
  4. User can rename any track and set its color — changes reflect in Ableton's UI
  5. User can get full track info (name, type, devices, clips, routing) for any track in the session
**Plans:** 4 plans

Plans:
- [x] 03-01-PLAN.md — Remote Script track handlers: all track CRUD (create audio/return/group, delete, duplicate), color palette mapping, group fold control, enhanced get_track_info for all track types, get_all_tracks
- [x] 03-02-PLAN.md — MCP tools and smoke tests: all track tool definitions in tools/tracks.py with parameter validation, comprehensive smoke tests for all 11 track tools
- [x] 03-03-PLAN.md — Gap closure: fix _set_track_name handler to use _resolve_track for return/master track rename support (TRCK-07)
- [x] 03-04-PLAN.md — Gap closure: fix _get_track_info to guard mute/solo access with hasattr so master track does not crash (TRCK-05)

### Phase 4: Mixing Controls
**Goal**: Users can control the complete mixer surface — levels, panning, mute/solo/arm, sends, and master/return channels
**Depends on**: Phase 3
**Requirements**: MIX-01, MIX-02, MIX-03, MIX-04, MIX-05, MIX-06, MIX-07, MIX-08
**Success Criteria** (what must be TRUE):
  1. User can set any track's volume and pan and hear the change immediately in Ableton
  2. User can mute, unmute, solo, and unsolo any track — state reflects in Ableton's mixer
  3. User can arm and disarm any track for recording
  4. User can set send levels from any track to any return channel
  5. User can set master track volume and return track volume/pan independently
**Plans:** 2 plans

Plans:
- [x] 04-01-PLAN.md — Remote Script mixer handlers: all 6 command handlers (set_track_volume, set_track_pan, set_track_mute, set_track_solo, set_track_arm, set_send_level) with dB helper, plus _WRITE_COMMANDS update
- [x] 04-02-PLAN.md — MCP mixer tools, smoke tests, and get_track_info enhancement: 6 tool definitions in tools/mixer.py, conftest/init wiring, dB+sends in get_track_info, 14+ smoke tests

### Phase 5: Clip Management
**Goal**: Users can create, edit, launch, and delete clips with full control over loop and playback regions
**Depends on**: Phase 2
**Requirements**: CLIP-01, CLIP-02, CLIP-03, CLIP-04, CLIP-05, CLIP-06, CLIP-07, CLIP-08, CLIP-09
**Success Criteria** (what must be TRUE):
  1. User can create a MIDI clip of a specified length in any clip slot and it appears in Ableton's Session View
  2. User can delete a clip and it disappears from the slot
  3. User can duplicate a clip to another slot and the copy is independent
  4. User can set clip loop enabled/disabled and adjust loop start/end and clip start/end markers
  5. User can fire (launch) a clip and stop it — playback responds immediately
**Plans:** 2 plans

Plans:
- [x] 05-01-PLAN.md — Remote Script clip handlers: _resolve_clip_slot helper, _clip_info_dict helper, 5 new handlers (delete_clip, duplicate_clip, get_clip_info, set_clip_color, set_clip_loop), enhanced fire_clip/stop_clip responses, _WRITE_COMMANDS update
- [x] 05-02-PLAN.md — MCP clip tools and smoke tests: 5 new tool functions (get_clip_info, delete_clip, duplicate_clip, set_clip_color, set_clip_loop), enhanced create_clip/fire_clip/stop_clip to return JSON, 12 smoke tests

### Phase 6: MIDI Editing
**Goal**: Users can read and write MIDI note data with full editing capabilities including quantize and transpose
**Depends on**: Phase 5
**Requirements**: MIDI-01, MIDI-02, MIDI-03, MIDI-04, MIDI-05
**Success Criteria** (what must be TRUE):
  1. User can add notes to a MIDI clip specifying pitch, start time, duration, and velocity — notes appear and play back
  2. User can read all notes from a clip and get the full list with their properties
  3. User can remove notes from a clip by specifying a time/pitch range — targeted notes disappear
  4. User can quantize notes in a clip to a specified grid size with adjustable strength
  5. User can transpose all notes in a clip by semitones — pitches shift correctly
**Plans:** 2 plans

Plans:
- [x] 06-01-PLAN.md — Remote Script note handlers: rewrite NoteHandlers with 5 Live 11+ commands (add_notes_to_clip, get_notes, remove_notes, quantize_notes, transpose_notes), _WRITE_COMMANDS update
- [x] 06-02-PLAN.md — MCP note tools and smoke tests: 4 new tools in tools/notes.py, update add_notes_to_clip to return JSON, conftest/init wiring, 9 smoke tests

### Phase 7: Device & Browser
**Goal**: Users can load instruments and effects onto tracks reliably and control device parameters
**Depends on**: Phase 2
**Requirements**: DEV-01, DEV-02, DEV-03, DEV-04, DEV-05, DEV-06, DEV-07, DEV-08
**Success Criteria** (what must be TRUE):
  1. User can load an instrument onto a MIDI track from the browser and immediately play notes that produce sound
  2. User can load an effect onto any track from the browser and it appears in the device chain
  3. User can get all parameters of any device — name, current value, min, and max
  4. User can set any device parameter by name or index and hear the effect on the sound
  5. User can browse the Ableton browser tree by category and navigate to specific paths including Instrument Racks, Drum Racks, and Effect Racks
  6. User can get a bulk session state dump covering all tracks, clips, and devices in a single call
**Plans:** 3 plans

Plans:
- [x] 07-01-PLAN.md — Remote Script device handlers: get_device_parameters, enhanced set_device_parameter (name/index/clamping/track_type/chain), delete_device, get_rack_chains (Instrument/Effect/Drum Rack)
- [x] 07-02-PLAN.md — Remote Script browser enhancements + session state: max_depth in get_browser_tree, path-based loading in load_instrument_or_effect, parameter list in load response, get_session_state bulk dump
- [x] 07-03-PLAN.md — MCP tools + smoke tests: 5 device tools, updated browser tools (remove load_drum_kit), get_session_state tool, connection.py updates, 20+ smoke tests

### Phase 8: Scene & Transport
**Goal**: Users have complete control over Session View scenes and all transport/playback functions
**Depends on**: Phase 2
**Requirements**: SCNE-01, SCNE-02, SCNE-03, SCNE-04, TRNS-01, TRNS-02, TRNS-03, TRNS-04, TRNS-05, TRNS-06, TRNS-07, TRNS-08, TRNS-09, TRNS-10
**Success Criteria** (what must be TRUE):
  1. User can create, name, fire, and delete scenes — each action reflects immediately in Ableton's Session View
  2. User can start, stop, and continue playback — transport responds as expected
  3. User can stop all clips at once from a single tool call
  4. User can set tempo and time signature — changes take effect during or before playback
  5. User can set the loop region (enabled, start, length) and query the current playback position
  6. User can undo and redo the last action — Live's undo history is accessible
**Plans:** 3 plans

Plans:
- [x] 08-01-PLAN.md — Remote Script scene handlers: SceneHandlers mixin with create_scene, set_scene_name, fire_scene, delete_scene, registry test update
- [x] 08-02-PLAN.md — Remote Script transport handlers: 8 new TransportHandlers commands (continue_playback, stop_all_clips, set_time_signature, set_loop_region, get_playback_position, get_transport_state, undo, redo), set_tempo validation, _WRITE_COMMANDS update
- [x] 08-03-PLAN.md — MCP tools and smoke tests: 4 scene tools, 11 transport tools (3 upgraded to JSON + 8 new), consecutive undo warning, conftest/init wiring, 20+ smoke tests

### Phase 9: Automation
**Goal**: Users can read, write, and clear clip automation envelopes for device parameter movement over time
**Depends on**: Phase 7
**Requirements**: AUTO-01, AUTO-02, AUTO-03
**Success Criteria** (what must be TRUE):
  1. User can get the automation envelope for a specific device parameter in a clip — returns breakpoint data
  2. User can insert automation breakpoints at specified positions and values — parameter moves in playback
  3. User can clear all automation from a clip's envelopes — parameters return to static values
**Plans:** 2/2 plans complete

Plans:
- [x] 09-01-PLAN.md — Remote Script AutomationHandlers mixin: 3 command handlers (get_clip_envelope, insert_envelope_breakpoints, clear_clip_envelopes) with dual-mode list/detail, wired into AbletonMCP MRO, registry test updated to 63
- [x] 09-02-PLAN.md — MCP automation tools, connection wiring, and smoke tests: 3 tool functions in tools/automation.py, _WRITE_COMMANDS update, conftest patch target, 7 smoke tests

### Phase 10: Routing & Audio Clips
**Goal**: Users can inspect and set track signal routing and control audio clip properties
**Depends on**: Phase 3
**Requirements**: ROUT-01, ROUT-02, ROUT-03, ROUT-04, ACLP-01, ACLP-02, ACLP-03
**Success Criteria** (what must be TRUE):
  1. User can get available input and output routing types for any track
  2. User can set a track's input and output routing — signal flow changes as expected
  3. User can set audio clip pitch (coarse and fine) and hear the transposition
  4. User can set audio clip gain and toggle warping on/off
**Plans:** 2/2 plans complete

Plans:
- [ ] 10-01-PLAN.md — Remote Script routing + audio clip handlers: RoutingHandlers (4 commands) and AudioClipHandlers (2 commands) mixin classes, wired into AbletonMCP MRO
- [ ] 10-02-PLAN.md — MCP tools, connection wiring, and smoke tests: 6 tool functions (4 routing + 2 audio clip), _WRITE_COMMANDS update, conftest/registry updates, 16 smoke tests

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Repair | 3/3 | Complete | 2026-03-13 |
| 2. Infrastructure Refactor | 3/3 | Complete | 2026-03-14 |
| 3. Track Management | 4/4 | Complete | 2026-03-14 |
| 4. Mixing Controls | 2/2 | Complete | 2026-03-14 |
| 5. Clip Management | 2/2 | Complete | 2026-03-14 |
| 6. MIDI Editing | 2/2 | Complete | 2026-03-14 |
| 7. Device & Browser | 3/3 | Complete | 2026-03-14 |
| 8. Scene & Transport | 3/3 | Complete | 2026-03-15 |
| 9. Automation | 2/2 | Complete   | 2026-03-16 |
| 10. Routing & Audio Clips | 2/2 | Complete    | 2026-03-17 |
| 11. LOM Gap Analysis | 1/1 | Complete    | 2026-03-18 |

### Phase 11: Check for Live Object Model Gaps

**Goal:** Audit the LOM specification against our 65 MCP tools, produce a structured gap report, fix correctness issues, and update REQUIREMENTS.md with new v2 entries
**Requirements**: TBD (gap analysis produces new requirements)
**Depends on:** Phase 10
**Plans:** 1/1 plans complete

Plans:
- [x] 11-01-PLAN.md — LOM gap report creation, correctness fixes (note expression fields), REQUIREMENTS.md update with ~9 new v2 categories

### Phase 12: Fill in missing gaps

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 11
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 12 to break down)
