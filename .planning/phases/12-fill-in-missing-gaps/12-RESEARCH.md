# Phase 12: Fill in Missing Gaps (Core) - Research

**Date:** 2026-03-19
**Status:** Complete

## Architecture Overview

### Current System
- 69 registered commands across 14 handler modules (mixin classes)
- 65+ MCP tools across 13 tool modules
- Mixin pattern: handler class → `@command` decorator → registry → dispatch tables
- MCP tools: `@mcp.tool()` → `send_command()` → socket → handler

### Adding New Functionality Pattern
1. **Handler**: Create/extend mixin class with `@command("name", write=bool)` methods
2. **Import**: Add to `handlers/__init__.py` if new module
3. **Tool**: Create `@mcp.tool()` function calling `send_command()`
4. **Timeout**: Add command names to `_WRITE_COMMANDS` or `_BROWSER_COMMANDS` in connection.py
5. **Test**: Smoke test with mock send_command

## Gap Inventory Analysis

### Plan 1: Song Gaps (~16 commands)

#### Scale & Key Awareness
- `Song.root_note` (int, 0-11, get/set) — C=0, C#=1, ..., B=11
- `Song.scale_name` (str, get/set) — e.g., "Major", "Minor", "Dorian"
- `Song.scale_intervals` (tuple, read-only) — e.g., (0,2,4,5,7,9,11) for Major
- `Song.scale_mode` (int, get/set) — 0=major, etc.
- **Handler**: New `ScaleHandlers` mixin or extend `TransportHandlers`
- **Tools**: `get_scale_info` (bulk read), `set_scale` (set root+name+mode)

#### Cue Points
- `Song.cue_points` — list of CuePoint objects
- `Song.set_or_delete_cue()` — toggle cue at current time
- `Song.jump_to_next_cue` / `Song.jump_to_prev_cue` — navigation
- CuePoint properties: `name` (get/set), `time` (read-only), `jump()` — jump to this cue
- **Handler**: New `CuePointHandlers` mixin
- **Tools**: `get_cue_points`, `set_or_delete_cue`, `jump_to_cue` (next/prev/by-index)

#### Capture Workflows
- `Song.capture_and_insert_scene()` — captures currently playing clips as new scene
- `Song.capture_midi()` — captures recently played MIDI input
- Both are simple fire-and-forget calls, no params needed
- **Tools**: `capture_scene`, `capture_midi`

#### Session Controls
- `Song.tap_tempo()` — no params, fires tap
- `Song.metronome` (bool, get/set)
- `Song.groove_amount` (float, 0.0-1.0, get/set) — global groove
- `Song.swing_amount` (float, 0.0-1.0, get/set) — global swing
- `Song.clip_trigger_quantization` (int, 0-14, get/set) — global launch quant
- `Song.session_record` (bool, get/set)
- `Song.record_mode` (bool, get/set)
- **Handler**: Extend `TransportHandlers` or new `SessionHandlers`
- **Tools**: Individual get/set tools or combined `set_session_controls`

#### Navigation & Arrangement Awareness
- `Song.jump_by(beats)` — relative position jump (float, positive or negative)
- `Song.play_selection()` — play arrangement selection (no params)
- `Song.last_event_time` (float, read-only) — end of last arrangement event
- `Song.song_length` (float, read-only) — total song length in beats
- **Tools**: `jump_by`, `play_selection`, `get_song_length`

#### Device Management
- `Song.move_device(device, target, position)` — move device between tracks/chains
  - `device`: Device object (resolve by track+device index)
  - `target`: Track or Chain object (resolve by track_type+track_index or chain path)
  - `position`: int index in target device chain
- `Song.find_device_position(device)` — returns DevicePosition (may not be needed as separate tool)
- **Complexity**: Resolving device and target objects from user params requires existing `_resolve_device` and `_resolve_track` helpers
- **Handler**: New method in `DeviceHandlers` or `TransportHandlers`
- **Tools**: `move_device(source_track_index, device_index, target_track_index, target_position, [chain_index])`

#### Scene Duplicate
- `Song.duplicate_scene(index)` — duplicate scene at index
- Simple call, similar to existing `duplicate_track`
- **Handler**: Extend `SceneHandlers`
- **Tool**: `duplicate_scene`

### Plan 2: Track + Arrangement (~9 commands)

#### Arrangement Clip Creation
- `Track.create_midi_clip(start_time, length)` — create MIDI clip in arrangement
  - Returns: Clip object
  - Position in beats from start of arrangement
  - Must resolve track first via `_resolve_track`
- `Track.create_audio_clip(file_path, position)` — create audio clip from file in arrangement
  - `file_path`: absolute path to audio file
  - `position`: float beats from start
  - Must validate file exists before sending to Ableton
- **Naming**: Differentiate from session `create_clip` → `create_arrangement_midi_clip`, `create_arrangement_audio_clip`

#### Arrangement Clip Listing
- `Track.arrangement_clips` — list property, returns arrangement Clip objects
- Each clip has: name, start_time, end_time, length, is_audio_clip, color (per CONTEXT.md decision)
- **Handler**: New `ArrangementHandlers` mixin
- **Tool**: `get_arrangement_clips(track_index, [track_type])`

#### Session→Arrangement Bridge
- `Track.duplicate_clip_to_arrangement(clip, time)` — copy session clip to arrangement
  - `clip`: resolve from clip_slot
  - `time`: float beats position in arrangement
  - Content only, no automation (per CONTEXT.md decision)
- **Tool**: `duplicate_clip_to_arrangement(track_index, clip_index, arrangement_time)`

#### Device Insertion
- `Track.insert_device(device_name, target_index)` — Live 12.3+ only
  - `device_name`: internal name like "Wavetable", "Analog", "Compressor"
  - `target_index`: position in device chain (0-based)
  - Returns: Device object (or info dict)
- No version guard needed (per CONTEXT.md decision — assume Live 12.3+)
- **Handler**: Extend `DeviceHandlers`
- **Tool**: `insert_device(track_index, device_name, position, [track_type])`

#### Track Operations
- `Track.stop_all_clips()` — stop all clips on a single track (session view)
  - Already have `Song.stop_all_clips()` (global) — this is per-track
- `Track.is_frozen` / `Track.can_be_frozen` (bool, read-only) — freeze state queries
  - Note: freeze/unfreeze operations are v2 (TRKA-01) — this is just query
- `ClipSlot.duplicate_clip_slot(index)` — duplicate clip in-place within track
  - Similar to existing `duplicate_clip_to` but stays in same track

#### Sub-Routing
- `Track.available_input_routing_channels` — list of available input channels
- `Track.available_output_routing_channels` — list of available output channels
- Already have `available_input/output_routing_types` — channels are sub-level
- **Handler**: Extend `RoutingHandlers`
- **Tool**: `get_routing_channels(track_index, direction, [track_type])`

### Plan 3: Clip + Note Expression (~19 commands)

#### Clip Launch Settings
- `Clip.launch_mode` (int, 0-3, get/set) — 0=Trigger, 1=Gate, 2=Toggle, 3=Repeat
- `Clip.launch_quantization` (int, 0-14, get/set) — per-clip launch quant
- `Clip.legato` (bool, get/set) — legato mode
- `Clip.velocity_amount` (float, 0.0-1.0, get/set) — velocity sensitivity
- **Handler**: New methods in `ClipHandlers`
- **Tool**: `set_clip_launch_settings(track_index, clip_index, [launch_mode], [launch_quantization], [legato], [velocity_amount])`

#### Clip State
- `Clip.muted` (bool, get/set) — clip activator (different from track mute)
- `Clip.groove` (Groove object or None, get/set) — associate groove with clip
  - Setting groove requires resolving groove object → may need groove pool access
  - **Consideration**: groove pool is Phase 13 — may need to defer groove association or add minimal groove pool access
- **Decision needed**: If groove association needs GroovePool (Phase 13), consider just exposing `muted` here

#### Clip Editing Operations
- `Clip.crop()` — no params, crops to loop/markers
- `Clip.duplicate_loop()` — no params, doubles loop length + duplicates content
- `Clip.duplicate_region(region_start, region_end, destination_time)` — duplicate notes in region

#### Warp Markers (Audio Clips Only)
- `Clip.warp_markers` — list of WarpMarker objects (sample_time, beat_time)
- `Clip.insert_warp_marker(beat_time, sample_time)` — add warp marker
- `Clip.move_warp_marker(index, new_beat_time)` — move existing marker
- `Clip.remove_warp_marker(index)` — remove marker
- **Precondition**: `clip.warping` must be True
- **Handler**: New `WarpMarkerHandlers` or extend `AudioClipHandlers`
- **Tool**: `get_warp_markers`, `insert_warp_marker`, `move_warp_marker`, `remove_warp_marker`

#### Note Operations (Live 11+ API)
- `Clip.apply_note_modifications(notes)` — modify notes in-place by ID
  - Takes list of MidiNoteSpecification with note_id set
  - More efficient than remove+re-add pattern
  - Requires note_id from get_notes
- `Clip.select_all_notes()` / `Clip.deselect_all_notes()` — selection state
- `Clip.select_notes_by_id(note_ids)` — selective note selection

#### Note ID Operations
- `Clip.get_notes_by_id(note_ids)` — get specific notes by ID
- `Clip.remove_notes_by_id(note_ids)` — remove specific notes by ID
- `Clip.duplicate_notes_by_id(note_ids)` — duplicate specific notes
- Note: note_id is already being returned by `get_notes` (added in Phase 11)

#### Advanced Note Queries
- `Clip.get_selected_notes_extended(from_time, time_span, from_pitch, pitch_span)` — like get_notes but only selected
- `Clip.get_all_notes_extended()` — convenience for get_notes_extended(0, max, 0, 128)

#### Native Quantize
- `Clip.quantize(grid, amount)` — native quantize respecting Song.swing_amount
  - `grid`: quantization grid (1/4, 1/8, etc. as float)
  - `amount`: quantize strength (0.0-1.0)
- `Clip.quantize_pitch(pitch, grid, amount)` — per-pitch quantize
- **Note**: We have manual quantize already — native method adds swing support

## Integration Considerations

### New Handler Modules to Create
1. `arrangement.py` — ArrangementHandlers (arrangement clips, session→arrangement bridge)
2. Extend existing modules for remaining functionality:
   - `transport.py` → scale/key, session controls, navigation, capture
   - `clips.py` → launch settings, clip state, clip editing
   - `notes.py` → note ID ops, note mods, selection, native quantize
   - `devices.py` → insert_device, move_device
   - `scenes.py` → duplicate_scene
   - `routing.py` → routing channels
   - `audio_clips.py` → warp markers

### New Tool Modules to Create
1. `arrangement.py` — arrangement clip tools
2. Extend existing for remaining

### Command Registry Impact
- ~30 new commands to register
- All write operations → `@command("name", write=True)`
- Read operations (get_scale_info, get_cue_points, etc.) → `@command("name")`
- Update `_WRITE_COMMANDS` frozenset in connection.py

### Test Impact
- ~30+ new smoke tests following existing pattern
- Update registry count test (currently expects 69)

## Risk Areas

1. **Groove association without GroovePool**: Clip.groove requires Groove objects from GroovePool. If GroovePool tools are Phase 13, clip.groove set may not be practical yet. Consider: expose get only, or include minimal groove pool access.

2. **move_device complexity**: Resolving device and target objects from simple integer parameters requires careful path through existing resolvers. May need find_device_position as prerequisite.

3. **Warp marker API**: WarpMarker indices may shift after insert/remove. Need to handle carefully in user-facing API.

4. **File path validation for create_audio_clip**: Need to validate file exists on the machine running Ableton, which may differ from MCP server host. Consider: trust the path and let Ableton error if not found.

## Validation Architecture

### Requirement Mapping
Phase 12 has no formal requirement IDs (TBD in roadmap). Validation maps to CONTEXT.md decisions:
- Song gaps: scale/key, cue points, capture, session controls, navigation, device mgmt
- Track+Arrangement: arrangement clips, insert_device, track ops, sub-routing
- Clip+Notes: launch settings, warp markers, note operations

### Verification Strategy
1. Registry count test: expect ~99 commands (69 current + ~30 new)
2. Smoke tests for each new tool: mock send_command, verify params
3. Handler tests: verify command registration and param validation
4. Integration: verify new tools appear in MCP server tool list

---
*Research completed: 2026-03-19*
