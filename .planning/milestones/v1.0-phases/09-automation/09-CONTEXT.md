# Phase 9: Automation - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Clip automation envelopes for device parameter movement over time. Users can read, write, and clear automation breakpoints on any device parameter within a clip. Regular tracks only (return/master tracks do not have clip slots in Session View). Arrangement automation is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Parameter targeting
- Flat parameters in a single tool call: track_index, clip_index, device_index, parameter_name/parameter_index
- Combines clip addressing (Phase 5 pattern) with device parameter addressing (Phase 7 pattern)
- Supports chain device parameters: optional chain_index + chain_device_index (reuses _resolve_device from Phase 7)
- Regular tracks only — no track_type parameter needed (consistent with Phase 5 clip tools)

### Envelope read (get_clip_envelope)
- Dual mode: no parameter specified → list all parameters that have automation in this clip (names + device info); with parameter specified → return that parameter's breakpoint data
- Breakpoint data format: {time: float (beats), value: float} pairs
- If the Live API doesn't expose raw breakpoints, sample at regular intervals instead

### Envelope write (insert_envelope_breakpoints)
- Batch insert: accepts a list of {time, value} pairs in one call (mirrors add_notes_to_clip pattern from Phase 6)
- Merge with existing automation — new breakpoints added at specified times, existing breakpoints at other times preserved, matching times overwrite
- Response: parameter name, device name, breakpoints_inserted count, total_breakpoints count (lightweight confirmation)

### Envelope clear (clear_clip_envelopes)
- Dual mode (matches get_clip_envelope): with parameter specified → clear just that parameter's envelope; without parameter → clear ALL envelopes on the clip
- Response: list of cleared parameter names (or "all"), envelopes_cleared count

### Claude's Discretion
- Whether to include curve/interpolation info in breakpoint data if the Live API exposes it
- Sampling interval if raw breakpoints aren't directly accessible from the API
- How to handle the Session vs Arrangement envelope distinction internally
- Whether to include parameter min/max in envelope responses for AI context

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Automation requirements
- `.planning/REQUIREMENTS.md` — AUTO-01, AUTO-02, AUTO-03 define the three automation capabilities

### Existing patterns to follow
- `AbletonMCP_Remote_Script/handlers/devices.py` — _resolve_device helper for track/chain/device navigation
- `AbletonMCP_Remote_Script/handlers/clips.py` — _resolve_clip_slot helper for clip addressing
- `AbletonMCP_Remote_Script/handlers/notes.py` — Batch insert pattern (add_notes_to_clip) to replicate for breakpoints
- `AbletonMCP_Remote_Script/registry.py` — @command decorator pattern for handler registration

### Known concern
- `.planning/STATE.md` §Blockers/Concerns — "Automation envelopes require understanding Session vs Arrangement envelope distinction"

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_resolve_clip_slot(song, track_index, clip_index)` in handlers/clips.py: Resolves clip from indices, returns (clip_slot, track)
- `DeviceHandlers._resolve_device(params)` in handlers/devices.py: Navigates track → device → chain with full error handling
- `_clip_info_dict(clip)` in handlers/clips.py: Standard clip info builder — could be extended or used alongside automation
- `@command` decorator with `write=True` flag for state-modifying operations

### Established Patterns
- Mixin class pattern: New `AutomationHandlers` class inherits into AbletonMCP (add to MRO in __init__.py)
- Batch operations: add_notes_to_clip accepts list of notes — same pattern for breakpoints
- Conditional dict building for optional parameters (Phase 5-6)
- Error messages include current values for AI self-correction (Phase 4+)
- JSON responses with `json.dumps(result, indent=2)` in MCP tools

### Integration Points
- `AbletonMCP_Remote_Script/handlers/`: New `automation.py` mixin with AutomationHandlers class
- `AbletonMCP_Remote_Script/__init__.py`: Add AutomationHandlers to AbletonMCP MRO
- `MCP_Server/tools/`: New `automation.py` with MCP tool definitions
- `MCP_Server/tools/__init__.py`: Add automation import
- `tests/`: Automation domain smoke tests following existing conftest pattern

</code_context>

<specifics>
## Specific Ideas

- Dual-mode pattern (list vs detail) on both get_clip_envelope and clear_clip_envelopes gives AI discoverability without extra tools
- Merge-on-insert behavior lets AI build up automation incrementally across multiple calls without losing prior work

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-automation*
*Context gathered: 2026-03-16*
