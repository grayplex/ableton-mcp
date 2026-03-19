# Phase 12: Fill in Missing Gaps (Core) - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the high-value "Add" tier gaps from the Phase 11 LOM gap report across Song, Track, and Clip classes. This covers arrangement view support, scale/key awareness, cue points, capture workflows, clip launch settings, note expression operations, warp markers, and device insertion. Scene extensions, Simpler, plugin presets, mixer extensions, groove pool, and drum pad operations are deferred to Phase 13.

</domain>

<decisions>
## Implementation Decisions

### Scope & Prioritization
- Phase 12 covers **~30 core gaps** across Song, Track+Arrangement, and Clip+Notes
- Phase 13 covers **~22 extended gaps** across Scene, Device+Simpler+Plugin, Mixer+Groove+DrumPad
- Plans organized **by LOM class**: Song gaps, Track+Arrangement, Clip+Notes (3 plans minimum, may split further)
- All gaps in "Add" tier are implemented — no further triage within the phase

### Arrangement View
- **Full arrangement support** — all 7 arrangement gaps implemented:
  - `Track.create_midi_clip(start_time, length)` — arrangement MIDI clip creation
  - `Track.create_audio_clip(file_path, position)` — arrangement audio clip from file
  - `Track.arrangement_clips` — list arrangement clips on a track
  - `Track.duplicate_clip_to_arrangement(clip, time)` — session→arrangement bridge
  - `Song.play_selection` — play arrangement selection
  - `Song.jump_by(beats)` — relative position navigation
  - `Song.last_event_time` — arrangement bounds
- **Beats as position unit** — consistent with LOM native units and existing clip/loop/marker APIs (1 beat = 1 quarter note)
- **Session→arrangement bridge** copies clip content only (notes/audio), no automation transfer (matches native LOM behavior)
- **Arrangement clip listing** returns essentials: name, start_time, end_time, length, is_audio_clip, color

### Version Compatibility
- **Assume Live 12.3+** — the LOM spec we reference IS 12.3.5
- No version guards or hasattr() checks — if a user has an older version, the Live API error surfaces normally through existing error handling
- insert_device (Live 12.3+) included in Phase 12 Track plan

### Specialized Devices
- **insert_device** → Phase 12 (Track plan) — dramatically simplifies device loading for native instruments/effects vs browser workflow
- **move_device** → Phase 12 (Song plan) — Song-level function for reorganizing effect chains
- **find_device_position** → Phase 12 (Song plan) — prerequisite for move_device
- **Simpler API** (crop, reverse, warp, slicing) → Phase 13
- **Plugin presets** (list, select by index) → Phase 13
- **Device A/B compare** → Phase 13

### Phase 12 Gap Inventory (by Plan)

**Plan: Song gaps (~16 items)**
- Scale/key: root_note, scale_name, scale_intervals, scale_mode (get/set)
- Cue points: cue_points list, set_or_delete_cue, jump_to_next/prev_cue
- Capture: capture_and_insert_scene, capture_midi
- Session: tap_tempo, metronome (get/set), groove_amount (get/set), swing_amount (get/set)
- Navigation: jump_by, play_selection, song_length/last_event_time
- Devices: move_device, find_device_position
- Control: clip_trigger_quantization (get/set), duplicate_scene, session_record/record_mode

**Plan: Track + Arrangement (~9 items)**
- Arrangement: create_midi_clip, create_audio_clip, arrangement_clips, duplicate_clip_to_arrangement
- Device: insert_device (Live 12.3+)
- Track ops: stop_all_clips (per-track), is_frozen/can_be_frozen, duplicate_clip_slot
- Routing: available_input/output_routing_channels (sub-routing)

**Plan: Clip + Note Expression (~19 items)**
- Launch settings: launch_mode, launch_quantization, legato, velocity_amount
- Clip state: muted (get/set), groove (get/set)
- Clip editing: crop, duplicate_loop, duplicate_region
- Warp markers: get/add/move/remove warp markers
- Note operations: apply_note_modifications, select_all/deselect_all/select_notes_by_id
- Note queries: get_selected_notes_extended, get_all_notes_extended
- Note ID ops: remove_notes_by_id, duplicate_notes_by_id, get_notes_by_id
- Quantize: native quantize(grid, amount), quantize_pitch

### Claude's Discretion
- Exact plan boundaries — may split the 3 logical groups into more plans if needed for manageability
- Handler mixin naming for new functionality (e.g., ArrangementHandlers, ScaleHandlers)
- Whether to create new MCP tool modules or extend existing ones
- Test organization for the new tools
- Error message wording for arrangement-specific edge cases

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### LOM Specification
- `Max9-LOM-en.pdf` — Complete LOM reference for Live 12.3.5 / Max 9. 171 pages. PRIMARY reference for all API signatures, parameter types, and value ranges.

### Gap Report
- `.planning/phases/11-check-for-live-object-model-gaps/11-GAP-REPORT.md` — Complete gap report with 52 Add-tier and 26 Backlog-tier items organized by LOM class. Each entry has tier, description, and AI production value rating.

### Requirements & Architecture
- `.planning/REQUIREMENTS.md` — v1 requirements (complete) and v2 requirements (58 entries from gap analysis). Phase 12 gaps map to v2 entries.
- `.planning/ROADMAP.md` — Phase history, success criteria patterns, plan structure conventions.
- `.planning/STATE.md` — Project state, decisions log, velocity metrics.

### Prior Phase Context
- `.planning/phases/11-check-for-live-object-model-gaps/11-CONTEXT.md` — Phase 11 decisions including audit scope, gap prioritization, correctness findings.

### Existing Implementation
- `AbletonMCP_Remote_Script/handlers/` — All Remote Script handler modules (14 files). Mixin pattern, command registry.
- `AbletonMCP_Remote_Script/handlers/base.py` — Command registry (_READ_COMMANDS, _WRITE_COMMANDS, _BROWSER_COMMANDS) with 4-tuple entries.
- `MCP_Server/tools/` — All MCP tool modules (13 files). @mcp.tool() decorator pattern.
- `MCP_Server/connection.py` — send_command function, timeout tiers.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_resolve_track(song, track_type, track_index)` in handlers/tracks.py — Track resolution for regular/return/master. Will be used heavily for arrangement operations.
- `_resolve_device(self, params)` in handlers/devices.py — Device resolution with chain navigation. Needed for move_device and insert_device.
- `_resolve_clip_slot(song, track_index, clip_index)` in handlers/clips.py — Clip slot resolution for session view. Arrangement clips need a new resolver.
- `_resolve_parameter(self, device, param_name, param_index)` in handlers/automation.py — Parameter lookup. Reusable for any parameter-related operations.
- `_clip_info_dict()` in handlers/clips.py — Clip info builder. Extend for arrangement clip properties.
- Mixin class pattern — All handlers use mixin classes inherited by AbletonMCP in __init__.py.
- Command registry — 4-tuple entries (handler, is_self_scheduling, category, description) in base.py.

### Established Patterns
- Domain handler mixin → MCP tool module → smoke test (consistent across all 11 phases)
- JSON response format with json.dumps(result, indent=2) for all tools
- Conditional param building — only non-None values sent to send_command
- _WRITE_COMMANDS vs _READ_COMMANDS vs _BROWSER_COMMANDS timeout tiers
- Patch get_ableton_connection at import site for test isolation

### Integration Points
- New handler mixins wire into AbletonMCP MRO in AbletonMCP_Remote_Script/handlers/__init__.py
- New MCP tools register via @mcp.tool() in MCP_Server/tools/ modules
- New commands added to _READ_COMMANDS, _WRITE_COMMANDS, or _BROWSER_COMMANDS in base.py
- conftest.py and test files follow existing smoke test patterns
- Arrangement clips are accessed via `track.arrangement_clips` (LOM property), distinct from `track.clip_slots`

</code_context>

<specifics>
## Specific Ideas

- insert_device is a major UX win — one-call device loading vs multi-step browser navigation
- Scale/key awareness (root_note, scale_name) is "Very High" value — lets Claude generate musically correct notes
- capture_and_insert_scene is "Very High" — captures currently playing clips as a new scene, key for AI composition workflow
- Warp markers are "Very High" for audio — essential for audio timing manipulation
- Note expression (probability, velocity_deviation) was partially added in Phase 11 (fields in add/get_notes). Phase 12 adds the remaining note operations (apply_modifications, ID-based ops, selection)
- Arrangement support gives Claude a complete "compose in session → arrange on timeline" workflow

</specifics>

<deferred>
## Deferred Ideas

### Phase 13: Extended Gaps
- Scene extensions: color, per-scene tempo/time_signature, fire_as_selected, is_empty
- Device: A/B preset compare, latency info
- Plugin: preset list/select
- Simpler: crop, reverse, warp_as/double/half, playback_mode, slicing
- Mixer: crossfader, crossfade_assign, panning_mode
- Groove pool: list grooves, groove parameters, clip groove association
- DrumPad: mute/solo, delete_all_chains
- CuePoint management (if not fully covered in Phase 12 Song plan)

### Backlog (from gap report)
- 26 Backlog-tier items (arrangement_overdub, nudge, count_in, scrub, ram_mode, etc.)
- Recording-specific overdub controls
- Meter readings (high CPU)
- Controller emulation (set_fire_button_state)

</deferred>

---

*Phase: 12-fill-in-missing-gaps*
*Context gathered: 2026-03-19*
