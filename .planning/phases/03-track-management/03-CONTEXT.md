# Phase 3: Track Management - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Full track type coverage — create, configure, and inspect every track type Ableton supports (MIDI, audio, return, group). Users can create, delete, duplicate, rename, color, and inspect tracks. No mixing controls (Phase 4), no routing (Phase 10), no clip operations (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Track color format
- Friendly color names only — no raw index exposure in the API
- Full palette: name all ~70 Ableton colors including variants (light red, dark red, salmon, etc.)
- Invalid color name returns error with list of valid names — AI can self-correct
- Read format (in get_track_info response): Claude's discretion

### Group track creation
- Both modes: empty group (default) and grouping existing tracks (optional track_indices parameter)
- Grouping moves tracks into the group (matches Ableton's native behavior, tracks become children)
- Response includes new group track index plus new indices of all grouped tracks (AI needs correct indices after reindexing)
- Add fold control: set_group_fold(track_index, folded: bool) and include fold state in get_track_info

### Track info depth
- get_track_info works on ALL track types: regular, return, and master (each returns type-appropriate fields)
- Routing info deferred to Phase 10 (Routing & Audio Clips)
- Send levels deferred to Phase 4 (Mixing Controls)
- Track addressing scheme (type parameter vs unified index): Claude's discretion
- Current fields: name, type, mute, solo, arm, volume, pan, devices, clips, color — add group fold state

### Delete and duplicate scope
- delete_track works on all deletable track types (regular + return). Master track is never deletable.
- delete_track returns info about what was deleted (name, type, index) — AI confirms the right thing was removed
- duplicate_track accepts optional new_name parameter. If omitted, uses Ableton's default naming.
- duplicate_track returns new track's index, name, and type

### Claude's Discretion
- Track addressing scheme: single tool with type parameter vs separate tools vs unified index space
- get_track_info read format for color (name only vs name + index)
- Response format consistency across all create_* tools
- Whether to add a lightweight get_all_tracks tool or rely on get_session_info

</decisions>

<specifics>
## Specific Ideas

- Error messages designed for AI consumption — clean message + technical detail (carried from Phase 1)
- "Hands-off on Remote Script side" — wants it to work without thinking about internals (carried from Phase 1)
- All responses should give AI enough context to continue working without extra calls (e.g., return new indices after operations that shift them)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TrackHandlers` mixin in handlers/tracks.py: already has create_midi_track, set_track_name, get_track_info
- `@command('name', write=True)` decorator for state-modifying commands
- `format_error()` in connection.py for AI-friendly error formatting
- tools/tracks.py: already has get_track_info, create_midi_track, set_track_name MCP tools

### Established Patterns
- Mixin class pattern: `TrackHandlers` inherited by `AbletonMCP`
- `@command` decorator with `write=True` flag for state-modifying operations
- `@mcp.tool()` decorator + `get_ableton_connection().send_command()` pattern
- `format_error(title, detail, suggestion)` for consistent error responses
- Domain smoke tests with mocked socket responses (Phase 2)

### Integration Points
- handlers/tracks.py: Add new handler methods (create_audio_track, create_return_track, create_group_track, delete_track, duplicate_track, set_track_color, set_group_fold)
- tools/tracks.py: Add corresponding MCP tool definitions
- registry.py: @command decorator auto-registers new handlers
- tests/: Add/extend track domain smoke tests

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-track-management*
*Context gathered: 2026-03-14*
