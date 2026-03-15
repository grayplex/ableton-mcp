# Phase 7: Device & Browser - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can load instruments and effects onto tracks reliably and control device parameters. Includes browser navigation with configurable depth, rack chain navigation (fully recursive), device parameter get/set by name or index, device deletion, and a bulk session state dump. Browser text search is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Device parameter addressing
- Accept both `parameter_name` (case-insensitive) and `parameter_index` for get/set operations
- Works on all track types: regular, return, and master (using `track_type` parameter from Phase 3)
- Return full detail per parameter: name, value, min, max, is_quantized
- Include device class type (instrument, audio_effect, midi_effect, rack, drum_machine) in response
- Include explicit position index for each device in chain responses
- Add `delete_device` tool for removing devices from a track's device chain

### Device parameter ambiguity resolution
- Claude's Discretion: when multiple parameters share the same name (e.g. two "Decay" params in Operator), Claude decides whether to use first-match or error-with-indices

### Device enable/disable
- Claude's Discretion: decide whether a separate enable/disable tool is worthwhile or if the "Device On" parameter (index 0) suffices

### Device chain reordering
- Claude's Discretion: evaluate API feasibility during research and decide whether to include move_device

### Rack chain navigation
- Fully recursive — navigate racks of any depth (rack inside rack inside rack), no artificial depth limit
- Drum Rack navigation exposes individual pad details: note number, name, chain devices per pad
- Chain device addressing uses explicit parameters: `chain_index` alongside `device_index`, plus `chain_device_index` for devices within a chain
- `get_device_parameters` and `set_device_parameter` accept optional `chain_index` parameter to address chain devices — same tools, extended addressing
- Dedicated `get_rack_chains` tool returns chain name, index, and device list for each chain in a rack

### Session state dump
- Two tiers: lightweight (default) and detailed (optional `detailed` flag)
- Lightweight: track names, device names, clip slots (name, color, is_playing for occupied slots only — skip empty slots), mixer state (volume, pan, mute, solo, arm, send levels)
- Detailed: adds all device parameter values for every device
- Includes return tracks and master track
- Includes transport state: tempo, time signature, play state, loop settings
- Only occupied clip slots reported (with scene index), not all slots

### Browser enhancements
- `get_browser_tree` gets configurable `max_depth` parameter (default 1 = top level only)
- `load_instrument_or_effect` accepts browser path (e.g. "instruments/Analog") in addition to URI — resolves internally
- Keep single `load_instrument_or_effect` tool (no separate load_instrument/load_effect)
- Remove `load_drum_kit` composite tool — AI can call load_instrument_or_effect twice
- Load responses include the loaded device's full parameter list for immediate configuration
- No browser text search in this phase
- Presets loaded via browser path navigation (no dedicated preset tool)

### Error behavior
- Use existing `format_error` pattern: error message + detail + suggestion
- `set_device_parameter` clamps out-of-range values to min/max and returns clamped value with warning
- Loading instrument on audio track returns clear error: "Cannot load instrument on audio track. Use a MIDI track instead."

</decisions>

<specifics>
## Specific Ideas

No specific references — decisions are focused on API contracts and capability scope.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DeviceHandlers._set_device_parameter`: Basic handler exists (index-only, regular tracks). Needs extension for name addressing, track_type, chain devices
- `DeviceHandlers._get_device_type`: Classifies devices (drum_machine, rack, instrument, audio_effect, midi_effect) — reuse in responses
- `BrowserHandlers.get_browser_tree`: Full implementation exists. Needs `max_depth` parameter for child traversal
- `BrowserHandlers.get_browser_items_at_path`: Full path navigation with `_CATEGORY_MAP` dict. Works for preset browsing
- `BrowserHandlers._load_browser_item`: Race-condition-free loading with device count verification + retry. Needs path-based loading and parameter list in response
- `BrowserHandlers._find_browser_item_by_uri`: Recursive URI search with cache. Used by load operations
- `_browser_path_cache`: URI-to-item cache on the AbletonMCP instance

### Established Patterns
- Mixin class pattern for handler modules (Phase 2)
- `@command` decorator with `write=True` and `self_scheduling=True` flags for browser load operations
- `queue.Queue` + `schedule_message` pattern for self-scheduling commands
- `format_error(message, detail, suggestion)` for structured error responses
- `track_type` parameter with `_resolve_track` helper for regular/return/master addressing (Phase 3)
- Conditional dict building for optional parameters (Phase 5-6)
- `json.dumps(result, indent=2)` for structured tool responses

### Integration Points
- `MCP_Server/tools/devices.py`: Currently only has `load_instrument_or_effect`. Needs get_device_parameters, set_device_parameter, delete_device, get_rack_chains
- `MCP_Server/tools/browser.py`: Has get_browser_tree, get_browser_items_at_path, load_drum_kit (to be removed). Needs max_depth support
- `MCP_Server/tools/session.py`: Likely home for get_session_state tool (or new tools/session_state.py)
- `AbletonMCP_Remote_Script/handlers/devices.py`: Needs get_device_parameters, enhanced set_device_parameter, delete_device, get_rack_chains, rack chain navigation
- `AbletonMCP_Remote_Script/handlers/browser.py`: Needs max_depth in get_browser_tree, path-based loading support
- `tests/`: Smoke tests following established conftest pattern with patched get_ableton_connection

</code_context>

<deferred>
## Deferred Ideas

- Browser text search (recursive walk + string matching) — potential future enhancement
- Device preset saving — requires Ableton file system access, limited API support
- Device chain reordering (move_device) — if API supports it, may be added at Claude's discretion

</deferred>

---

*Phase: 07-device-browser*
*Context gathered: 2026-03-14*
