# Phase 4: Mixing Controls - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete mixer surface control — volume, pan, mute, solo, arm, sends, and master/return channels. Users can SET all mixer parameters (Phase 3 already handles READ via get_track_info). No crossfader, no input monitoring modes, no cue/preview volume, no routing (Phase 10).

</domain>

<decisions>
## Implementation Decisions

### Volume representation
- Input: 0.0-1.0 normalized only (no dB input)
- Pan: -1.0 (full left) to 1.0 (full right), 0 = center
- Send levels: same 0.0-1.0 normalized range as volume
- Validation: error on out-of-range values (no clamping) — error includes current value for AI self-correction
- Response includes dB approximation alongside normalized value (for volume AND sends)
- dB also added to get_track_info and get_all_tracks responses (Phase 3 enhancement)
- dB conversion formula: Claude's discretion (standard formula vs Ableton-matched curve)

### Mute/solo/arm style
- Explicit set only — no toggle (set_track_mute, set_track_solo, set_track_arm as booleans)
- Separate tools per operation — not combined
- Solo supports optional 'exclusive' parameter (unsolos all other tracks when soloing)
- Arm errors with explanation on tracks that can't be armed (e.g., group tracks)
- Mute and solo work on return tracks too (not just regular tracks)
- Master track excluded from mute/solo (consistent with Phase 3)

### Send level addressing
- Sends identified by return track index (not name, not send slot index)
- Send levels use 0.0-1.0 normalized, same as volume
- Send responses include dB approximation
- Send target scope (returns only vs master): Claude's discretion based on API
- Whether to read sends via get_track_info or separate tool: Claude's discretion

### Response content
- Echo actual stored value from Ableton (not the requested value) — accounts for internal quantization
- Master track responses: same structure as regular tracks, but no track_index field
- Mute/solo/arm responses: just the changed state (no mini mixer snapshot)
- Error responses include current value alongside valid range
- Whether to include track name in every response: Claude's discretion (Phase 3 pattern reference)
- Whether to include pan label (e.g., "50% left"): Claude's discretion

### Tool surface design
- Unified tools with track_type parameter — set_track_volume, set_track_pan, etc. all accept track_type='track'/'return'/'master'
- Matches Phase 3 pattern (set_track_name, set_track_color use track_type)
- No dedicated set_master_volume / set_return_volume tools

### Claude's Discretion
- dB conversion formula (standard 20*log10 vs Ableton-matched curve)
- Whether sends are read via expanded get_track_info or a separate get_send_levels tool
- Send response: whether to include return track name for confirmation
- Send target scope: returns-only or also master
- Pan label in responses (e.g., "center", "50% left")
- Track name inclusion in every mixer response

</decisions>

<specifics>
## Specific Ideas

- Error messages designed for AI consumption — include current value in range errors so AI can self-correct
- "Echo actual stored value" — truthful responses, no pretending Ableton stored exactly what was requested
- Carried from Phase 3: all responses give AI enough context to continue without extra calls

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_resolve_track(song, track_type, track_index)` in handlers/tracks.py: resolves track by type and index — direct reuse for all mixer operations
- `MixerHandlers` stub class in handlers/mixer.py: placeholder ready for implementation
- `mixer.py` stub in MCP_Server/tools/: placeholder ready for tool definitions
- `format_error(title, detail, suggestion)` in connection.py: AI-friendly error formatting
- `@command('name', write=True)` decorator for state-modifying commands

### Established Patterns
- Mixin class pattern: MixerHandlers will be inherited by AbletonMCP (like TrackHandlers)
- `@command` decorator with `write=True` for set operations, no flag for read operations
- `track_type` parameter on tools: "track" (default), "return", "master"
- `get_ableton_connection().send_command()` pattern in MCP tools
- JSON response format with json.dumps(result, indent=2)

### Integration Points
- handlers/mixer.py: Add handler methods (set_track_volume, set_track_pan, set_track_mute, set_track_solo, set_track_arm, set_send_level)
- MCP_Server/tools/mixer.py: Add corresponding MCP tool definitions
- handlers/tracks.py: Enhance _get_track_info and _get_all_tracks to include dB values (and potentially sends)
- registry.py: @command decorator auto-registers new handlers
- tests/: Add mixer domain smoke tests

</code_context>

<deferred>
## Deferred Ideas

- Crossfader control (A/B assignment per track) — niche, potential future phase
- Input monitoring modes (In/Auto/Off) — Phase 10 (Routing) or separate
- Cue/preview volume for headphone monitoring — potential future phase

</deferred>

---

*Phase: 04-mixing-controls*
*Context gathered: 2026-03-14*
