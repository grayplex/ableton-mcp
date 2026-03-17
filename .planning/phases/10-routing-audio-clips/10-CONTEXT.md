# Phase 10: Routing & Audio Clips - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Track signal routing inspection and control (input and output) plus audio clip property adjustment (pitch, gain, warping). All track types supported for routing. Audio clip properties only apply to audio clips (not MIDI). This is the final v1 phase.

</domain>

<decisions>
## Implementation Decisions

### Routing data format
- Flat list of routing type display_name strings from get_input_routing_types / get_output_routing_types
- Response includes `current` field with active routing name alongside the available list
- set_input_routing / set_output_routing accept routing type by display name (string match, case-insensitive)
- Set response includes before/after: {previous: 'Ext. In', current: 'Track 1-Audio', track_name: 'Bass'}
- Both get_track_info and the new routing tools return current routing (redundant but each serves different purpose: overview vs discovery)

### Track type scope for routing
- All track types supported: regular (MIDI/audio), return, master — via existing _resolve_track(track_type, track_index)
- Consistent with mixer tools (Phase 4) which work on all types
- API exposes different routing options per track type — just pass through whatever Ableton provides

### Routing tool structure
- 4 separate tools matching REQUIREMENTS.md exactly: get_input_routing_types, set_input_routing, get_output_routing_types, set_output_routing
- Each tool takes track_type + track_index parameters (reuses _resolve_track)

### Audio clip tool design
- One combined set tool: set_audio_clip_properties(track_index, clip_index, pitch_coarse=None, pitch_fine=None, gain=None, warping=None) — all optional, set whichever you need
- Separate read tool: get_audio_clip_properties(track_index, clip_index) returns all audio-specific properties
- Reuses _resolve_clip_slot from Phase 5 with audio clip type check
- Set response includes before/after for changed properties: {track_name, clip_name, changes: [{property, previous, current}, ...]}
- Gain accepts dB values directly (how musicians think about gain), not normalized 0-1

### Error handling
- Wrong clip type: ValueError with guidance — "Clip at track 0 slot 2 is a MIDI clip, not audio. Audio clip properties only apply to audio clips."
- Invalid routing name: ValueError listing available options — "Routing type 'Ext In' not found. Available: ['Ext. In', 'Track 1-Audio', ...]"
- Pitch range validation: coarse -48 to +48 semitones, fine -50 to +50 cents — validate before sending, include range in error
- All errors include context for AI self-correction (consistent with Phase 4+ pattern)

### Claude's Discretion
- Exact dB-to-internal-value conversion for clip gain (depends on what Ableton API actually exposes)
- Whether warp_mode should be readable in get_audio_clip_properties (bonus info if easy)
- How to handle sub-channels if they become relevant during implementation
- Registry command classification (read vs write timeouts)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Routing & audio clip requirements
- `.planning/REQUIREMENTS.md` — ROUT-01 through ROUT-04 (routing), ACLP-01 through ACLP-03 (audio clip properties)

### Existing patterns to follow
- `AbletonMCP_Remote_Script/handlers/tracks.py` — _resolve_track helper for track type/index addressing
- `AbletonMCP_Remote_Script/handlers/clips.py` — _resolve_clip_slot helper for clip addressing
- `AbletonMCP_Remote_Script/handlers/mixer.py` — Before/after response pattern for set operations, _resolve_track usage across all track types
- `AbletonMCP_Remote_Script/handlers/devices.py` — _resolve_device pattern for parameter name matching (case-insensitive)
- `AbletonMCP_Remote_Script/registry.py` — @command decorator pattern for handler registration

### Known concern
- `.planning/STATE.md` §Blockers/Concerns — "Input/output routing APIs vary by track type and hardware — needs testing against actual Ableton instance before implementation"

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_resolve_track(song, track_type, track_index)` in handlers/tracks.py: Resolves track from type + index, supports regular/return/master
- `_resolve_clip_slot(song, track_index, clip_index)` in handlers/clips.py: Resolves clip from indices, returns (clip_slot, track)
- `_clip_info_dict(clip)` in handlers/clips.py: Standard clip info builder — extend or use as reference for audio clip properties
- `@command` decorator with `write=True` flag for state-modifying operations
- `_to_db` and `_pan_label` in handlers/mixer_helpers.py: Value conversion helpers (reference for gain dB conversion)

### Established Patterns
- Mixin class pattern: New `RoutingHandlers` and `AudioClipHandlers` classes inherit into AbletonMCP
- Before/after response: mixer tools return {previous, current} for set operations
- Case-insensitive name matching: device parameter lookup in _resolve_parameter (Phase 9)
- Conditional dict building for optional parameters (Phase 5+)
- Error messages include current/valid values for AI self-correction (Phase 4+)
- JSON responses with `json.dumps(result, indent=2)` in MCP tools

### Integration Points
- `AbletonMCP_Remote_Script/handlers/`: New `routing.py` + `audio_clips.py` mixins
- `AbletonMCP_Remote_Script/__init__.py`: Add RoutingHandlers + AudioClipHandlers to AbletonMCP MRO
- `MCP_Server/tools/`: New `routing.py` + `audio_clips.py` with MCP tool definitions
- `MCP_Server/tools/__init__.py`: Add routing + audio_clips imports
- `tests/`: Routing + audio clip domain smoke tests following existing conftest pattern

</code_context>

<specifics>
## Specific Ideas

- Combined set_audio_clip_properties tool reduces API calls — AI can pitch-shift + adjust gain + toggle warping in one shot
- Routing tools expose current alongside available — eliminates the common "get current, get options, set new" three-call pattern
- dB for gain matches how Ableton displays it — no mental conversion for the AI or user

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-routing-audio-clips*
*Context gathered: 2026-03-16*
