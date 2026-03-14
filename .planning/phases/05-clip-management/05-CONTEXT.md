# Phase 5: Clip Management - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Full clip lifecycle — create, edit, loop, launch, delete clips with complete control over loop and playback regions. Clips live on regular tracks only (return/master tracks do not support clip placement). MIDI note editing is Phase 6. Audio clip properties (pitch, gain, warping) are Phase 10.

</domain>

<decisions>
## Implementation Decisions

### Clip info exposure
- Dedicated `get_clip_info` tool (not folded into get_track_info)
- Returns full detail: name, length, color, loop_enabled, loop_start, loop_end, start_marker, end_marker, is_playing, is_triggered, is_audio_clip
- No MIDI note data — Phase 6 handles notes
- Empty slots return `{has_clip: false, slot_index: N}` instead of erroring
- `get_track_info` clip listing enhanced with `is_playing` flag (lightweight addition)
- `set_clip_color` added — uses same 70-color palette as Phase 3's set_track_color

### Duplicate behavior
- AI specifies exact target: `duplicate_clip(track_index, clip_index, target_track_index, target_clip_index)`
- Error if target slot already occupied — AI must delete first
- Response includes new clip details (name, length, target location)

### Loop/region controls
- One combined `set_clip_loop` tool with all optional params: enabled, loop_start, loop_end, start_marker, end_marker
- Validate relationships (loop_end > loop_start, end_marker > start_marker) — error includes all current marker positions for self-correction
- Positions in beats (float) — no bar:beat notation
- Response echoes ALL current loop/marker values regardless of what was changed

### Track addressing
- Regular tracks only — no track_type parameter needed (return/master tracks don't support clips)
- Consistent with current clip handlers which use song.tracks

### Create/delete safety
- create_clip keeps existing error-on-occupied-slot behavior (no overwrite option)
- delete_clip errors on empty slot (consistent with fire_clip, set_clip_name)

### Fire/stop response enhancement
- fire_clip returns {fired: true, is_playing: true, clip_name: "..."}
- stop_clip returns {stopped: true, clip_name: "..."}
- Enhanced from current minimal {fired: true} / {stopped: true}

### Claude's Discretion
- Whether get_clip_info returns additional properties available from the API (e.g., signature_numerator, signature_denominator)
- Internal structure of set_clip_loop validation (order of checks)
- Whether delete_clip returns the deleted clip's name for confirmation

</decisions>

<specifics>
## Specific Ideas

- Error messages designed for AI consumption — include current values in range/relationship errors so AI can self-correct (carried from Phase 4)
- Echo actual stored values from Ableton (carried from Phase 4)
- get_clip_info on empty slot returns data instead of erroring — AI can discover slot state without try/catch

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ClipHandlers` mixin in handlers/clips.py: already has create_clip, set_clip_name, fire_clip, stop_clip — needs extension
- `clips.py` in MCP_Server/tools/: already has corresponding MCP tools — needs extension
- `COLOR_NAMES` dict in handlers/tracks.py: 70 snake_case color names — reuse for set_clip_color
- `format_error(title, detail, suggestion)` in connection.py: AI-friendly error formatting
- `@command('name', write=True)` decorator for state-modifying commands

### Established Patterns
- Mixin class pattern: ClipHandlers inherited by AbletonMCP
- `@command` decorator with `write=True` for set operations
- `get_ableton_connection().send_command()` pattern in MCP tools
- JSON response format with json.dumps(result, indent=2)
- Error responses include current value for AI self-correction

### Integration Points
- handlers/clips.py: Add delete_clip, duplicate_clip, get_clip_info, set_clip_color, set_clip_loop handlers
- MCP_Server/tools/clips.py: Add corresponding MCP tool definitions
- handlers/tracks.py: Enhance _get_track_info to include is_playing in clip listings
- Enhance existing fire_clip, stop_clip handlers with richer responses
- tests/: Add clip domain smoke tests

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-clip-management*
*Context gathered: 2026-03-14*
