# Phase 8: Scene & Transport - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete control over Session View scenes (create, name, fire, delete) and all transport/playback functions (start, stop, continue, stop all clips, tempo, time signature, loop region, playback position, undo, redo). Three transport commands already exist (start_playback, stop_playback, set_tempo) — this phase completes the remaining 11 commands.

</domain>

<decisions>
## Implementation Decisions

### Scene operations
- create_scene takes an optional name parameter — auto-names like Ableton (Scene N) if not provided
- Scene creation returns structured JSON response (consistent with track/clip creation patterns)

### Transport state
- Dedicated get_transport_state tool that returns full state: is_playing, tempo, time_signature, position, loop_enabled, loop_start, loop_length
- get_playback_position returns position only — not playing status or tempo (lightweight check)

### Position & time format
- Loop region (set_loop_region) specified in beats (float) — consistent with Phase 5 clip loop params
- Playback position reported in beats (float) — format details at Claude's discretion

### Undo/redo
- Undo and redo classified as write commands (main thread scheduling, 15s timeout)
- Warn after 3+ consecutive undo calls — return advisory message in response
- Undo/redo feedback format at Claude's discretion

### Claude's Discretion
- Fire scene quantization — whether to expose quantization param or fire immediately
- Scene delete behavior when scene is playing — handle gracefully based on API behavior
- Transport command response richness (beyond get_transport_state)
- stop_all_clips behavior (clips only vs clips + transport) — match Ableton native behavior
- set_tempo validation range (20-999 BPM) — follow existing Phase 4 validation patterns
- set_time_signature validation — accept what Ableton supports
- Whether to add a "panic" tool (combined stop all + stop transport + reset position)
- Playback position format details (raw beats, or also bars.beats)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Follow established patterns from Phases 3-7 for handler structure, tool definitions, and smoke tests.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TransportHandlers` mixin in `handlers/transport.py`: already has start_playback, stop_playback, set_tempo — extend with new commands
- `SceneHandlers` mixin in `handlers/scenes.py`: empty placeholder ready for implementation
- `MCP_Server/tools/transport.py`: 3 existing tools (set_tempo, start_playback, stop_playback)
- `MCP_Server/tools/scenes.py`: empty stub ready for scene tools
- `@command` decorator in `registry.py`: register new handlers with write=True flag
- `_song` accessor from BaseHandlers: provides access to Ableton's Song object for all scene/transport APIs

### Established Patterns
- Mixin class pattern: SceneHandlers and TransportHandlers are mixed into AbletonMCP class
- @command(write=True) for state-modifying commands → scheduled on main thread
- JSON structured responses with json.dumps(result, indent=2) for all tools
- Conditional dict building for optional params (set_clip_loop pattern from Phase 5)
- Parameter validation in handlers with clear error messages including current value (Phase 4 mixer pattern)

### Integration Points
- `AbletonMCP_Remote_Script/__init__.py`: SceneHandlers and TransportHandlers already in MRO
- `AbletonMCP_Remote_Script/handlers/__init__.py`: scenes and transport modules already imported
- `MCP_Server/tools/__init__.py`: import scenes and transport modules
- `MCP_Server/connection.py`: no changes needed — existing send_command infrastructure handles new commands
- Test fixtures: patch get_ableton_connection at tools/scenes.py and tools/transport.py import sites

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-scene-transport*
*Context gathered: 2026-03-14*
