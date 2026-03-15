# Phase 7: Device & Browser - Research

**Researched:** 2026-03-14
**Domain:** Ableton Live Python API -- device parameters, rack/chain navigation, browser loading, session state
**Confidence:** HIGH

## Summary

Phase 7 extends the existing device and browser handlers with parameter get/set, rack chain navigation, device deletion, and a bulk session state dump. The Ableton Live Python API (Live Object Model) provides all the primitives needed: `device.parameters` for parameter lists, `device.can_have_chains` / `device.can_have_drum_pads` for rack detection, `chain.devices` for chain device access, `DrumPad.chains` / `DrumPad.note` for pad navigation, and `Track.delete_device(index)` / `Chain.delete_device(index)` for device removal.

The existing codebase has substantial foundation: `_load_browser_item` with race-condition-free loading, `_get_device_type` for device classification, `get_browser_tree` and `get_browser_items_at_path` for browser navigation, and `_CATEGORY_MAP` for dict-based category dispatch. The work is primarily additive -- new handler methods and MCP tools using established patterns.

**Primary recommendation:** Build new handlers following the established mixin pattern. Use `_resolve_track` for track addressing, conditional dict building for optional params, and `json.dumps(result, indent=2)` for tool responses. Reuse `_get_device_type` in all device responses. For session state, iterate all tracks/returns/master in a single command to minimize round trips.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Device parameter addressing: Accept both `parameter_name` (case-insensitive) and `parameter_index` for get/set operations
- Works on all track types: regular, return, and master (using `track_type` parameter from Phase 3)
- Return full detail per parameter: name, value, min, max, is_quantized
- Include device class type (instrument, audio_effect, midi_effect, rack, drum_machine) in response
- Include explicit position index for each device in chain responses
- Add `delete_device` tool for removing devices from a track's device chain
- Rack chain navigation: Fully recursive -- navigate racks of any depth, no artificial depth limit
- Drum Rack navigation exposes individual pad details: note number, name, chain devices per pad
- Chain device addressing uses explicit parameters: `chain_index` alongside `device_index`, plus `chain_device_index` for devices within a chain
- `get_device_parameters` and `set_device_parameter` accept optional `chain_index` parameter to address chain devices
- Dedicated `get_rack_chains` tool returns chain name, index, and device list for each chain in a rack
- Session state dump: Two tiers (lightweight default + detailed with `detailed` flag)
- Lightweight: track names, device names, clip slots (occupied only with scene index), mixer state, transport
- Detailed: adds all device parameter values
- Includes return tracks and master track
- `get_browser_tree` gets configurable `max_depth` parameter (default 1)
- `load_instrument_or_effect` accepts browser path in addition to URI
- Keep single `load_instrument_or_effect` tool (no separate load_instrument/load_effect)
- Remove `load_drum_kit` composite tool
- Load responses include loaded device's full parameter list
- No browser text search in this phase
- Presets loaded via browser path navigation
- Use existing `format_error` pattern for errors
- `set_device_parameter` clamps out-of-range values to min/max with warning
- Loading instrument on audio track returns clear error message

### Claude's Discretion
- Device parameter ambiguity resolution: when multiple parameters share same name (e.g. two "Decay" in Operator), decide between first-match or error-with-indices
- Device enable/disable: decide whether separate tool or "Device On" parameter (index 0) suffices
- Device chain reordering (move_device): evaluate API feasibility and decide whether to include

### Deferred Ideas (OUT OF SCOPE)
- Browser text search (recursive walk + string matching)
- Device preset saving
- Device chain reordering (move_device) -- if API does not support it
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEV-01 | User can load instruments onto tracks via browser | Existing `_load_browser_item` with race-condition-free loading. Needs path-based loading and parameter list in response |
| DEV-02 | User can load effects onto tracks via browser | Same mechanism as DEV-01. Effects use `audio_effects`/`midi_effects` browser categories |
| DEV-03 | User can get all parameters of any device (name, value, min, max) | `device.parameters` vector. Each DeviceParameter has `.name`, `.value`, `.min`, `.max`, `.is_quantized` |
| DEV-04 | User can set any device parameter by name or index | Existing `_set_device_parameter` (index-only). Extend with name lookup (case-insensitive) and `track_type` support |
| DEV-05 | User can browse the Ableton browser tree by category | Existing `get_browser_tree` handler. Add `max_depth` for recursive child traversal |
| DEV-06 | User can navigate browser items at a specific path | Existing `get_browser_items_at_path`. Already functional |
| DEV-07 | User can navigate into Instrument Racks, Drum Racks, and Effect Racks | `device.can_have_chains`, `device.can_have_drum_pads`, `device.chains`, `chain.devices`, `DrumPad.chains`, `DrumPad.note` |
| DEV-08 | User can get bulk session state dump | New `get_session_state` command iterating all tracks, clips, devices, transport |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Ableton Live Python API (LOM) | Live 11+ / 12 | Device, DeviceParameter, Chain, DrumPad, Browser, BrowserItem | The only way to interact with Ableton from a Remote Script |
| Python 3.11 | 3.11 | Remote Script runtime | Ableton Live 12 ships Python 3.11 |
| FastMCP | 1.26.0 | MCP tool registration | Project standard from Phase 2 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| queue | stdlib | Self-scheduling browser load commands | Already used by `_load_browser_item` |
| json | stdlib | Structured tool responses | All MCP tool functions use `json.dumps(result, indent=2)` |
| traceback | stdlib | Error logging in handlers | Already used in browser.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Parameter name lookup in handler | Parameter name lookup in MCP tool | Handler-side is simpler -- single round trip, consistent with existing pattern |
| Separate get_instrument_params / get_effect_params | Single get_device_parameters | Single tool is cleaner -- device type returned in response for context |

**Installation:**
No new dependencies. All capabilities come from Ableton's built-in Python API and existing project infrastructure.

## Architecture Patterns

### Recommended Project Structure
```
AbletonMCP_Remote_Script/
  handlers/
    devices.py          # Extended: get_device_parameters, set_device_parameter, delete_device, get_rack_chains, get_session_state
    browser.py          # Extended: max_depth in get_browser_tree, path-based loading in _load_browser_item

MCP_Server/
  tools/
    devices.py          # Extended: get_device_parameters, set_device_parameter, delete_device, get_rack_chains
    browser.py          # Modified: remove load_drum_kit, update get_browser_tree for max_depth, update load_instrument_or_effect for path
    session.py          # Extended: add get_session_state tool

  connection.py         # Update _BROWSER_COMMANDS and _WRITE_COMMANDS sets

tests/
  test_devices.py       # Extended: smoke tests for new device tools
  test_browser.py       # Updated: remove load_drum_kit test, add max_depth tests
  test_session.py       # Extended: smoke test for get_session_state
```

### Pattern 1: Device Parameter Retrieval
**What:** Read all parameters from a device on any track type.
**When to use:** DEV-03 implementation.
**Example:**
```python
# In handlers/devices.py
@command("get_device_parameters")
def _get_device_parameters(self, params):
    track_index = params.get("track_index", 0)
    device_index = params.get("device_index", 0)
    track_type = params.get("track_type", "track")
    chain_index = params.get("chain_index", None)

    track = _resolve_track(self._song, track_type, track_index)

    if device_index < 0 or device_index >= len(track.devices):
        raise IndexError("Device index out of range")

    device = track.devices[device_index]

    # If chain_index specified, navigate into rack chain
    if chain_index is not None:
        if not device.can_have_chains:
            raise ValueError(f"Device '{device.name}' is not a rack")
        if chain_index < 0 or chain_index >= len(device.chains):
            raise IndexError("Chain index out of range")
        chain = device.chains[chain_index]
        # Could further navigate with chain_device_index
        chain_device_index = params.get("chain_device_index", None)
        if chain_device_index is not None:
            if chain_device_index < 0 or chain_device_index >= len(chain.devices):
                raise IndexError("Chain device index out of range")
            device = chain.devices[chain_device_index]

    parameters = []
    for i, param in enumerate(device.parameters):
        parameters.append({
            "index": i,
            "name": param.name,
            "value": param.value,
            "min": param.min,
            "max": param.max,
            "is_quantized": param.is_quantized,
        })

    return {
        "device_name": device.name,
        "device_type": self._get_device_type(device),
        "class_name": device.class_name,
        "parameters": parameters,
    }
```

### Pattern 2: Device Parameter Setting with Name Lookup and Clamping
**What:** Set a device parameter by name or index with out-of-range clamping.
**When to use:** DEV-04 implementation.
**Example:**
```python
@command("set_device_parameter", write=True)
def _set_device_parameter(self, params):
    track_index = params.get("track_index", 0)
    device_index = params.get("device_index", 0)
    track_type = params.get("track_type", "track")
    value = params.get("value")

    track = _resolve_track(self._song, track_type, track_index)
    device = track.devices[device_index]

    # Resolve parameter by name or index
    parameter_name = params.get("parameter_name", None)
    parameter_index = params.get("parameter_index", None)

    if parameter_name is not None:
        # Case-insensitive name lookup
        name_lower = parameter_name.lower()
        param = None
        for p in device.parameters:
            if p.name.lower() == name_lower:
                param = p
                break
        if param is None:
            available = [p.name for p in device.parameters]
            raise ValueError(
                f"Parameter '{parameter_name}' not found. "
                f"Available: {available}"
            )
    elif parameter_index is not None:
        if parameter_index < 0 or parameter_index >= len(device.parameters):
            raise IndexError("Parameter index out of range")
        param = device.parameters[parameter_index]
    else:
        raise ValueError("Provide parameter_name or parameter_index")

    # Clamp value to min/max with warning
    warning = None
    if value < param.min:
        warning = f"Value {value} clamped to min {param.min}"
        value = param.min
    elif value > param.max:
        warning = f"Value {value} clamped to max {param.max}"
        value = param.max

    param.value = value

    result = {
        "device_name": device.name,
        "parameter_name": param.name,
        "value": param.value,
        "min": param.min,
        "max": param.max,
    }
    if warning:
        result["warning"] = warning
    return result
```

### Pattern 3: Rack Chain Navigation (Recursive)
**What:** Navigate racks of any depth -- access chains, their devices, and nested racks.
**When to use:** DEV-07 implementation.
**Example:**
```python
@command("get_rack_chains")
def _get_rack_chains(self, params):
    track_index = params.get("track_index", 0)
    device_index = params.get("device_index", 0)
    track_type = params.get("track_type", "track")

    track = _resolve_track(self._song, track_type, track_index)
    device = track.devices[device_index]

    if not device.can_have_chains:
        raise ValueError(f"Device '{device.name}' is not a rack")

    result = {
        "device_name": device.name,
        "device_type": self._get_device_type(device),
        "chains": [],
    }

    if device.can_have_drum_pads:
        # Drum Rack -- expose pads
        for pad in device.drum_pads:
            pad_info = {
                "note": pad.note,
                "name": pad.name,
                "chains": [],
            }
            for chain in pad.chains:
                chain_info = {
                    "name": chain.name,
                    "devices": [],
                }
                for di, d in enumerate(chain.devices):
                    chain_info["devices"].append({
                        "index": di,
                        "name": d.name,
                        "type": self._get_device_type(d),
                        "can_have_chains": d.can_have_chains,
                    })
                pad_info["chains"].append(chain_info)
            result["pads"] = result.get("pads", [])
            result["pads"].append(pad_info)
    else:
        # Instrument/Effect Rack -- expose chains
        for ci, chain in enumerate(device.chains):
            chain_info = {
                "index": ci,
                "name": chain.name,
                "devices": [],
            }
            for di, d in enumerate(chain.devices):
                chain_info["devices"].append({
                    "index": di,
                    "name": d.name,
                    "type": self._get_device_type(d),
                    "can_have_chains": d.can_have_chains,
                })
            result["chains"].append(chain_info)

    return result
```

### Pattern 4: Browser max_depth Traversal
**What:** Recursively traverse browser children up to a configurable depth.
**When to use:** DEV-05 enhancement.
**Example:**
```python
def process_item(item, depth=0, max_depth=1):
    if not item:
        return None
    info = {
        "name": item.name if hasattr(item, "name") else "Unknown",
        "is_folder": hasattr(item, "children") and bool(item.children),
        "is_device": hasattr(item, "is_device") and item.is_device,
        "is_loadable": hasattr(item, "is_loadable") and item.is_loadable,
        "uri": item.uri if hasattr(item, "uri") else None,
    }
    # Recurse into children if within max_depth
    if depth < max_depth and hasattr(item, "children") and item.children:
        info["children"] = []
        for child in item.children:
            child_info = process_item(child, depth + 1, max_depth)
            if child_info:
                info["children"].append(child_info)
    else:
        info["children"] = []
    return info
```

### Pattern 5: Session State Dump
**What:** Aggregate session data in a single call.
**When to use:** DEV-08 implementation.
**Example:**
```python
@command("get_session_state")
def _get_session_state(self, params=None):
    detailed = (params or {}).get("detailed", False)

    result = {
        "transport": {
            "tempo": self._song.tempo,
            "signature_numerator": self._song.signature_numerator,
            "signature_denominator": self._song.signature_denominator,
            "is_playing": self._song.is_playing,
            "loop_enabled": self._song.loop,
            "loop_start": self._song.loop_start,
            "loop_length": self._song.loop_length,
        },
        "tracks": [],
        "return_tracks": [],
        "master_track": {},
    }

    def build_track_state(track, track_type_hint=None):
        info = {
            "name": track.name,
            "volume": track.mixer_device.volume.value,
            "pan": track.mixer_device.panning.value,
        }
        if hasattr(track, "mute"):
            info["mute"] = track.mute
        if hasattr(track, "solo"):
            info["solo"] = track.solo
        if hasattr(track, "can_be_armed") and track.can_be_armed:
            info["arm"] = track.arm

        # Devices
        devices = []
        for di, device in enumerate(track.devices):
            dev_info = {
                "index": di,
                "name": device.name,
                "type": self._get_device_type(device),
            }
            if detailed:
                dev_info["parameters"] = [
                    {"name": p.name, "value": p.value, "min": p.min, "max": p.max}
                    for p in device.parameters
                ]
            devices.append(dev_info)
        info["devices"] = devices

        # Clip slots (occupied only)
        if hasattr(track, "clip_slots"):
            clips = []
            for si, slot in enumerate(track.clip_slots):
                if slot.has_clip:
                    clips.append({
                        "scene_index": si,
                        "name": slot.clip.name,
                        "color": slot.clip.color_index,
                        "is_playing": slot.clip.is_playing,
                    })
            info["clips"] = clips

        # Sends
        if hasattr(track.mixer_device, "sends"):
            sends = [s.value for s in track.mixer_device.sends]
            if sends:
                info["sends"] = sends

        return info

    # Regular tracks
    for i, track in enumerate(self._song.tracks):
        t = build_track_state(track)
        t["index"] = i
        result["tracks"].append(t)

    # Return tracks
    for i, track in enumerate(self._song.return_tracks):
        t = build_track_state(track)
        t["index"] = i
        result["return_tracks"].append(t)

    # Master track
    result["master_track"] = build_track_state(self._song.master_track, "master")

    return result
```

### Anti-Patterns to Avoid
- **Multiple round trips for session state:** Do NOT call individual track/device commands in a loop from the MCP tool layer. The session state dump must be a single Remote Script command that iterates everything server-side.
- **Accessing `device.drum_pads` on non-drum devices:** Always check `device.can_have_drum_pads` before accessing `.drum_pads`. Accessing it on a non-drum device raises an error.
- **Accessing `device.chains` on non-rack devices:** Always check `device.can_have_chains` first. Not all devices support chains.
- **Loading instruments on audio tracks:** The browser `load_item` call will "succeed" silently but no device appears. Must validate track type before attempting load, or catch the device-count-unchanged case.
- **Forgetting `_resolve_track` for track_type support:** All new handlers MUST use `_resolve_track(self._song, track_type, track_index)` instead of direct `self._song.tracks[track_index]` access.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Track type resolution | Manual if/elif for track/return/master | `_resolve_track(self._song, track_type, track_index)` from tracks.py | Already handles validation, error messages, all 3 track types |
| Device type classification | Inline isinstance/hasattr checks | `self._get_device_type(device)` from devices.py | Already handles drum_machine, rack, instrument, audio_effect, midi_effect |
| Error formatting | Custom f-strings for errors | `format_error(message, detail, suggestion)` from connection.py | Consistent AI-friendly error format across all tools |
| Browser category lookup | String matching with hardcoded attributes | `_CATEGORY_MAP` dict from browser.py | Already fixes the instruments typo, provides clean mapping |
| Race-condition-free loading | Custom load-and-wait logic | Existing `_load_browser_item` with device count verification + retry | Already handles the race condition, just extend for path-based input |
| Browser item URI search | New URI search function | `_find_browser_item_by_uri` with `_browser_path_cache` | Already has caching and recursive search |

**Key insight:** Phase 7 is primarily extension of existing infrastructure, not creation of new patterns. The device/browser handler and MCP tool structure is well established from Phases 2-6.

## Common Pitfalls

### Pitfall 1: Parameter Name Collision in Complex Devices
**What goes wrong:** Devices like Ableton's Operator have multiple parameters with the same display name (e.g., multiple "Decay" parameters for different oscillators).
**Why it happens:** `DeviceParameter.name` is a display name, not a unique identifier. The only guaranteed unique identifier is the parameter index.
**How to avoid:** Use first-match strategy for name lookup (simplest, most predictable) and include the matched parameter's index in the response so the AI can switch to index-based addressing if needed. If ambiguity matters, the AI can call `get_device_parameters` first to see all names with indices.
**Warning signs:** Multiple parameters with identical names in `get_device_parameters` output.

### Pitfall 2: Drum Pad Iteration Can Be Slow
**What goes wrong:** `device.drum_pads` on a fully loaded Drum Rack can return 128 pads. Iterating all pads and their chains can be slow.
**Why it happens:** Each pad can have multiple chains, each with multiple devices. This is O(pads * chains * devices).
**How to avoid:** In `get_rack_chains` for drum racks, only return pads that have content (non-empty chains). Filter with `if pad.chains and len(pad.chains) > 0`. For session state, skip drum pad detail entirely -- just report the device name and type.
**Warning signs:** Slow response times (>5s) for drum rack inspection.

### Pitfall 3: Loading on Wrong Track (Race Condition)
**What goes wrong:** `browser.load_item` loads onto the currently selected track, not a specified track. If the selected track changes between `selected_track = track` and `load_item(item)`, the device loads on the wrong track.
**Why it happens:** These are separate API calls. Other threads or user interaction can change the selection.
**How to avoid:** The existing `_load_browser_item` already uses the same-callback pattern (both calls in one `schedule_message` callback). Keep using this.
**Warning signs:** Device count unchanged on target track after load, but increased on another track.

### Pitfall 4: delete_device Index Shifts
**What goes wrong:** After deleting a device at index N, all devices at indices > N shift down by 1.
**Why it happens:** Device list is contiguous. Deletion reindexes.
**How to avoid:** If deleting multiple devices, delete from highest index to lowest. For single deletions, return the updated device chain in the response.
**Warning signs:** IndexError when trying to delete a second device after the first deletion.

### Pitfall 5: Parameter Value Assignment on Quantized Parameters
**What goes wrong:** Setting a quantized parameter (like a dropdown/toggle) to a non-integer value may silently snap to the nearest valid value or raise an error.
**Why it happens:** `is_quantized` parameters have discrete valid values. The API may accept any float but snap to the nearest valid step.
**How to avoid:** After setting `param.value`, always read back `param.value` to report the actual stored value (it may differ from the requested value). The clamping behavior handles min/max, but quantization steps are separate.
**Warning signs:** Set value does not equal reported value for quantized parameters.

### Pitfall 6: Browser max_depth Performance
**What goes wrong:** Setting `max_depth` too high (e.g., 10) on the full browser tree causes extreme slowness.
**Why it happens:** The browser tree is very deep (categories > instruments > subfolders > presets). Even depth 3 can return thousands of items.
**How to avoid:** Default max_depth=1 (top level children only). Warn in tool description that values >3 may be slow. Consider a reasonable cap (e.g., 5).
**Warning signs:** Timeout errors on `get_browser_tree` with high max_depth.

### Pitfall 7: Session State with Many Tracks and Detailed Mode
**What goes wrong:** `get_session_state` with `detailed=True` on a large session (50+ tracks, many devices) produces a massive JSON response.
**Why it happens:** Each device can have 50+ parameters. Multiply by 10+ devices per track and 50 tracks.
**How to avoid:** Default to lightweight mode. Only use detailed mode when specifically needed. Consider size warnings in the tool description.
**Warning signs:** Response size >1MB, socket timeout on large sessions.

### Pitfall 8: Chain Device vs Track Device Addressing Confusion
**What goes wrong:** User tries to set a parameter on a device inside a rack chain using only `device_index`, missing the `chain_index`.
**Why it happens:** Devices inside rack chains are NOT in the track's top-level `track.devices` list. They are in `track.devices[device_index].chains[chain_index].devices[chain_device_index]`.
**How to avoid:** Clear parameter naming: `device_index` = top-level device on track, `chain_index` = which chain within that rack, `chain_device_index` = which device within that chain.
**Warning signs:** "Device index out of range" when the user thinks they're addressing a chain device.

## Code Examples

Verified patterns from the existing codebase and Ableton Live API:

### Device Parameter Access (Ableton Live API)
```python
# Source: Ableton Live LOM documentation + existing codebase
device = track.devices[0]  # First device on track
for i, param in enumerate(device.parameters):
    print(f"{i}: {param.name} = {param.value} ({param.min}-{param.max})")
    # param.is_quantized tells if parameter has discrete steps
```

### Rack Chain Navigation (Ableton Live API)
```python
# Source: Ableton Live LOM documentation
device = track.devices[0]  # A rack device
if device.can_have_chains:
    for chain in device.chains:
        print(f"Chain: {chain.name}")
        for d in chain.devices:
            print(f"  Device: {d.name}")
            if d.can_have_chains:  # Nested rack!
                for nested_chain in d.chains:
                    print(f"    Nested: {nested_chain.name}")
```

### Drum Pad Navigation (Ableton Live API)
```python
# Source: Ableton Live LOM documentation
device = track.devices[0]  # A Drum Rack
if device.can_have_drum_pads:
    for pad in device.drum_pads:
        if pad.chains:  # Pad has content
            print(f"Pad note={pad.note} name='{pad.name}'")
            for chain in pad.chains:
                for d in chain.devices:
                    print(f"  Device: {d.name}")
```

### Device Deletion (Ableton Live API)
```python
# Source: Ableton Live LOM documentation
# delete_device(index) is available on both Track and Chain
track.delete_device(0)  # Remove first device from track
# For chain devices:
chain.delete_device(0)  # Remove first device from chain
```

### MCP Tool Pattern (Established in Phase 3-6)
```python
# Source: Existing codebase pattern from tools/notes.py, tools/mixer.py
@mcp.tool()
def get_device_parameters(
    ctx: Context,
    track_index: int,
    device_index: int,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get all parameters of a device. ...docstring..."""
    try:
        ableton = get_ableton_connection()
        params: dict = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_device_parameters", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get device parameters",
            detail=str(e),
            suggestion="Verify device exists with get_track_info",
        )
```

### Handler Registration Pattern (Established in Phase 2)
```python
# Source: Existing codebase -- AbletonMCP_Remote_Script/registry.py
from AbletonMCP_Remote_Script.registry import command

class DeviceHandlers:
    @command("get_device_parameters")        # Read command
    def _get_device_parameters(self, params): ...

    @command("set_device_parameter", write=True)  # Write command
    def _set_device_parameter(self, params): ...

    @command("delete_device", write=True)     # Write command
    def _delete_device(self, params): ...
```

## Discretion Decisions (Researcher Recommendations)

### Parameter Name Ambiguity: Use First-Match
**Recommendation:** First-match strategy. When multiple parameters share the same name, return the first one found. Include the matched parameter's index in the response. The AI can then use `get_device_parameters` to see all parameters with indices and switch to index-based addressing if the first match was wrong.
**Rationale:** Error-with-indices adds friction to the common case (most parameters have unique names). First-match is simpler, and the parameter list tool provides a fallback.

### Device Enable/Disable: No Separate Tool
**Recommendation:** Do NOT add a separate enable/disable tool. Device On/Off is already parameter index 0 on all devices. `set_device_parameter(parameter_index=0, value=0.0)` disables, `value=1.0` enables. Document this in the `set_device_parameter` tool description.
**Rationale:** Adding a tool for what is already a single parameter set call adds surface area without capability. The AI can learn "parameter 0 = Device On" from the parameter list.

### Device Chain Reordering (move_device): Do Not Include
**Recommendation:** Do NOT include `move_device`. The Ableton Live Python API does NOT expose a `move_device` method on Track or Chain. The only way to reorder devices is to delete and re-add, which would lose device state (parameter values, custom mappings).
**Rationale:** No API support. Destructive workarounds (delete + re-load) would lose state and are unreliable. This is correctly deferred.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python 2 Remote Scripts | Python 3.11 Remote Scripts | Live 11 (2021) | f-strings, type hints, super(), queue module |
| load_item on main thread without verification | Same-callback pattern + device count check + retry | Phase 1 of this project | Reliable instrument loading |
| Manual if/elif command dispatch | `@command` decorator + `CommandRegistry` | Phase 2 of this project | Clean handler registration |
| Separate load_instrument / load_effect | Single `load_instrument_or_effect` with type auto-detection | Phase 1 of this project | Simpler API surface |

**Deprecated/outdated:**
- `load_drum_kit` composite tool: Being removed in this phase per CONTEXT.md decisions. AI can call `load_instrument_or_effect` twice.

## Open Questions

1. **Track.delete_device availability**
   - What we know: `Chain.delete_device(index)` is documented in the Live API. Multiple sources reference it.
   - What's unclear: Whether `Track.delete_device(index)` has the exact same signature, or if device deletion on a top-level track uses a different API path. The Track class inherits Chain-like behavior in many respects.
   - Recommendation: Implement using `track.delete_device(device_index)`. If that fails, try `self._song.delete_device(track, device_index)` as fallback. Test during UAT.

2. **DrumPad.drum_pads property name**
   - What we know: Drum pads are accessed via `device.drum_pads` (plural). Each pad has `.note`, `.name`, `.chains`.
   - What's unclear: Whether it's `device.drum_pads` or `device.pads` in Live 12 API. The property has been `drum_pads` in all documentation found.
   - Recommendation: Use `device.drum_pads` with a hasattr guard. HIGH confidence this is correct.

3. **Path-based loading resolution**
   - What we know: `load_instrument_or_effect` currently accepts URI only. CONTEXT.md requires it to also accept a browser path.
   - What's unclear: Whether to reuse `get_browser_items_at_path` internally or add a separate path resolution step in `_load_browser_item`.
   - Recommendation: Add path resolution in the handler. If `item_uri` is not provided but `path` is, use the existing path navigation logic to find the item, then call `load_item` on it. Reuse `get_browser_items_at_path` logic (not the method itself, to avoid extra serialization).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml or pytest.ini (project-level) |
| Quick run command | `python -m pytest tests/test_devices.py tests/test_browser.py tests/test_session.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEV-01 | Load instrument via browser | smoke | `pytest tests/test_devices.py::test_load_instrument_calls_send_command -x` | Exists (update) |
| DEV-02 | Load effect via browser | smoke | `pytest tests/test_devices.py::test_load_effect_calls_send_command -x` | Wave 0 |
| DEV-03 | Get device parameters | smoke | `pytest tests/test_devices.py::test_get_device_parameters -x` | Wave 0 |
| DEV-04 | Set device parameter | smoke | `pytest tests/test_devices.py::test_set_device_parameter -x` | Wave 0 |
| DEV-05 | Browse browser tree | smoke | `pytest tests/test_browser.py::test_get_browser_tree_returns_data -x` | Exists (update for max_depth) |
| DEV-06 | Navigate browser path | smoke | `pytest tests/test_browser.py::test_get_browser_items_at_path -x` | Wave 0 |
| DEV-07 | Navigate rack chains | smoke | `pytest tests/test_devices.py::test_get_rack_chains -x` | Wave 0 |
| DEV-08 | Session state dump | smoke | `pytest tests/test_session.py::test_get_session_state -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_devices.py tests/test_browser.py tests/test_session.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_devices.py` -- needs new tests for get_device_parameters, set_device_parameter (name + index), delete_device, get_rack_chains
- [ ] `tests/test_browser.py` -- needs update: remove load_drum_kit test, add max_depth test, add path-based loading test
- [ ] `tests/test_session.py` -- needs new test for get_session_state (lightweight + detailed)
- [ ] `tests/conftest.py` -- no changes needed (mock_connection already patches all tool modules)

## Sources

### Primary (HIGH confidence)
- [Ableton Live 11.0 API Documentation (nsuspray)](https://nsuspray.github.io/Live_API_Doc/11.0.0.xml) -- Device, DeviceParameter, Chain, DrumPad, Browser, BrowserItem class properties and methods
- [Ableton Live 10.0.1 API Documentation (structure-void)](https://structure-void.com/PythonLiveAPI_documentation/Live10.0.1.xml) -- Cross-referenced Device, Chain, Browser APIs
- Existing codebase -- `AbletonMCP_Remote_Script/handlers/devices.py`, `browser.py`, `MCP_Server/tools/devices.py`, `browser.py`, `session.py`

### Secondary (MEDIUM confidence)
- [Ableton Forum - Python API Enhancements](https://forum.ableton.com/viewtopic.php?t=75974) -- Community insights on API capabilities
- [Ableton LiveAPI Tools (Ziforge)](https://github.com/Ziforge/ableton-liveapi-tools) -- Reference implementation with 220 tools including device/rack/chain operations
- [AbletonOSC](https://github.com/ideoforms/AbletonOSC) -- Device parameter and chain navigation patterns

### Tertiary (LOW confidence)
- `move_device` claim: No official documentation found. Multiple searches confirm no `move_device` method in the Live API. LOW confidence that it exists (i.e., HIGH confidence it does NOT exist).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- uses existing project libraries and Ableton's built-in API
- Architecture: HIGH -- extends established mixin/registry pattern from Phase 2
- Pitfalls: HIGH -- many pitfalls identified from existing code (race condition fix) and API documentation
- API specifics: MEDIUM-HIGH -- Live API docs are unofficial but comprehensive and well-maintained
- move_device: HIGH (negative) -- confirmed not available in the API

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days -- stable domain, Ableton API rarely changes)
