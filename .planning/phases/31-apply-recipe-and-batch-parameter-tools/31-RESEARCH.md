# Phase 31: Apply Recipe and Batch Parameter Tools - Research

**Researched:** 2026-03-28
**Domain:** Ableton LOM device loading, batch parameter setting, sidechain routing, natural-to-normalized conversion
**Confidence:** HIGH

## Summary

Phase 31 bridges the recipe data (Phase 30) and the existing device control infrastructure into three new MCP tools and three new RS commands that let users apply an entire mix recipe or master bus recipe in a single call. The core technical challenges are: (1) natural-to-normalized unit conversion on the MCP side, (2) atomic device loading + parameter setting within a single RS handler that blocks until device instantiation is confirmed, (3) sidechain source resolution by track name, and (4) batch parameter setting in a single socket round-trip.

The existing codebase provides all the building blocks: `load_browser_item` with its self-scheduling/verify pattern for device loading, `set_device_parameter` for single-param writes, `set_compressor_sidechain` for index-based sidechain routing, the device CATALOG with conversion metadata, and the mixing recipe modules with natural-unit values.

**Primary recommendation:** Build the natural-to-normalized converter as a pure function in `MCP_Server/devices/convert.py`, then compose the three RS commands (`apply_recipe`, `set_device_parameters`, `set_sidechain_source`) as write+self_scheduling handlers in `devices.py` that reuse existing `_resolve_track` and `_resolve_device` helpers. MCP tools go in `MCP_Server/tools/mixing.py` alongside the existing `get_mix_recipe`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** RS command `apply_recipe` handles entire load + wait + set in one socket round-trip. RS handler checks existing devices, loads missing via browser path, blocks until `track.devices` confirms, then sets all params. Atomicity guaranteed inside RS handler.
- **D-02:** Browser paths for built-in devices are hardcoded in RS handler as `DEVICE_PATHS` dict keyed by catalog class name.
- **D-03:** Natural-unit to normalized conversion happens on MCP side. MCP tool reads recipe + catalog conversion metadata, converts to normalized floats, sends `{device_class: {param_name: normalized_value}}` payload to RS. RS handler receives only normalized values.
- **D-04:** Update-in-place: if device of required class already exists on track, set params without reloading. Only load absent devices. Match by `device.class_name`.
- **D-05:** Multiple devices of same class: use first match by index. No error.
- **D-06:** Full master bus recipes for 4 core genres (house, techno, ambient, DnB) with Glue Compressor + Multiband Dynamics + Limiter chain. Live in genre files or separate master files (Claude's discretion).
- **D-07:** `apply_master_recipe(genre)` applies chain to master track (`track_type="master"`). Same conflict handling as D-04.
- **D-08:** RS command `set_sidechain_source` accepts `track_index`, `device_index`, `source_track_name`. RS resolves name to index by iterating `Live.Song.tracks`.
- **D-09:** If `source_track_name` not found, abort with error. No partial state.
- **D-10:** `set_sidechain_source` also exposed as standalone MCP tool.

### Claude's Discretion
- Whether master bus recipes live as `MASTER_RECIPE` constants in existing genre files or in separate `master_house.py` files
- Exact normalized parameter values for master bus recipes per genre
- Internal structure of `apply_recipe` RS handler (single method vs. helper decomposition)
- Whether `set_device_parameters` RS primitive (BATCH-01) is also exposed as a standalone MCP tool

### Deferred Ideas (OUT OF SCOPE)
- Full master bus recipes for 8 remaining genres (Phase 34)
- Auto-wire all genre-conventional sidechain connections in one call (v1.5)
- `set_device_parameters` as standalone user-facing MCP tool (Claude's discretion; not required by any SC)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BATCH-01 | Batch set multiple device parameters in a single socket call | New RS command `set_device_parameters` reuses existing `_resolve_device` + parameter-by-name lookup pattern from `_set_device_parameter`; batches all writes in one handler call |
| APPLY-01 | Apply role x genre mix recipe to track in one MCP call | MCP tool `apply_mix_recipe` converts natural->normalized via catalog metadata, sends payload to `apply_recipe` RS command which loads + sets atomically |
| APPLY-02 | Apply genre master bus recipe to master track in one MCP call | MCP tool `apply_master_recipe` uses same conversion + RS command with `track_type="master"`; master recipes authored for 4 core genres |
| APPLY-03 | Parameters set only after device confirmed instantiated (no race) | RS `apply_recipe` handler uses `self_scheduling=True` with same verify pattern as `load_browser_item` -- schedule_message callback checks `track.devices` before setting params |
| SIDE-01 | Set compressor sidechain source by track name | New RS command `set_sidechain_source` resolves name via `song.tracks` iteration, then delegates to existing `available_input_routing_types` API |
</phase_requirements>

## Architecture Patterns

### Recommended Project Structure

New and modified files:

```
MCP_Server/
  devices/
    convert.py            # NEW: natural_to_normalized() conversion functions
  mixing/
    house.py              # MODIFIED: add MASTER_RECIPE constant
    techno.py             # MODIFIED: add MASTER_RECIPE constant
    ambient.py            # MODIFIED: add MASTER_RECIPE constant
    drum_and_bass.py      # MODIFIED: add MASTER_RECIPE constant
    catalog.py            # MODIFIED: add get_master_recipe() public API
  tools/
    mixing.py             # MODIFIED: add apply_mix_recipe, apply_master_recipe, set_sidechain_source tools
AbletonMCP_Remote_Script/
  handlers/
    devices.py            # MODIFIED: add apply_recipe, set_device_parameters, set_sidechain_source handlers
MCP_Server/
  connection.py           # MODIFIED: add new commands to _WRITE_COMMANDS and _BROWSER_COMMANDS
tests/
  test_mixing.py          # MODIFIED: add conversion tests, master recipe validation
  test_convert.py         # NEW: unit tests for natural_to_normalized conversion
```

### Pattern 1: Natural-to-Normalized Conversion (MCP Side)

**What:** Pure function that converts a recipe's natural-unit values to 0.0-1.0 normalized floats using CATALOG conversion metadata.

**When to use:** Called by `apply_mix_recipe` and `apply_master_recipe` before sending payload to RS.

**Implementation notes:**

The CATALOG stores three conversion types:
- `log`: logarithmic mapping (Hz frequencies). Formula: `normalized = log(natural/natural_min) / log(natural_max/natural_min)`
- `linear`: linear mapping. Formula: `normalized = (natural - natural_min) / (natural_max - natural_min)`
- `linear_db`: linear dB mapping. Formula: `normalized = (natural - natural_min) / (natural_max - natural_min)`
- `None` (no conversion dict): value is already in normalized/raw range -- pass through directly

**Key detail from recipes:** Parameters with `conversion: None` in the CATALOG are stored in recipes using the raw min/max range values (e.g., Compressor2 Ratio is 0-1 range, not a natural ratio). So no conversion is needed for those -- they are already normalized or use the device's native range.

**Edge case:** Quantized parameters (filter type enums, on/off toggles) have `is_quantized: True` and `conversion: None`. These are integer values that map directly to the parameter value -- no conversion needed.

### Pattern 2: Atomic Apply Recipe RS Handler (self_scheduling)

**What:** A `self_scheduling=True` write handler that loads missing devices, verifies instantiation, then sets parameters.

**When to use:** For `apply_recipe` RS command.

**Design based on existing `load_browser_item` pattern:**

1. Handler receives `{track_index, track_type, devices: [{class_name, params: {name: value}}]}`
2. For each device entry:
   - Scan `track.devices` for existing device with matching `class_name`
   - If found: use it (D-04 update-in-place)
   - If not found: load via `DEVICE_PATHS[class_name]` using browser, verify load
3. After all devices resolved: set all parameters in sequence
4. Return summary of devices loaded and parameters set

**Critical: The `load_browser_item` pattern uses `schedule_message` + `response_queue` for async verification.** The `apply_recipe` handler must use the same approach -- `self_scheduling=True` so it manages its own thread coordination.

### Pattern 3: DEVICE_PATHS Dict

**What:** Hardcoded mapping from CATALOG class names to browser paths.

**Verified device classes in CATALOG (from `catalog.py`):**

```python
DEVICE_PATHS = {
    "Eq8": "audio_effects/EQ Eight",
    "Compressor2": "audio_effects/Compressor",
    "GlueCompressor": "audio_effects/Glue Compressor",
    "DrumBuss": "audio_effects/Drum Buss",
    "MultibandDynamics": "audio_effects/Multiband Dynamics",
    "Reverb": "audio_effects/Reverb",
    "Delay": "audio_effects/Delay",
    "AutoFilter2": "audio_effects/Auto Filter",
    "Gate": "audio_effects/Gate",
    "Limiter": "audio_effects/Limiter",
    "EnvelopeFollower": "audio_effects/Envelope Follower",
    "StereoGain": "audio_effects/Utility",
}
```

**Confidence:** HIGH for built-in effect names. These are the standard browser paths used by `load_instrument_or_effect` (path-based loading) which is already tested.

### Pattern 4: Sidechain Source Resolution by Name

**What:** RS handler that resolves `source_track_name` to a track, then finds its entry in the device's `available_input_routing_types`.

**Existing infrastructure:** The `set_compressor_sidechain` RS handler (line 1159 in `devices.py`) already sets sidechain by index. The new handler adds name resolution on top.

**LOM API for sidechain routing:**
- `device.available_input_routing_types` -- list of routing type objects (each has `.display_name`)
- `device.input_routing_type = types[i]` -- sets the source type
- `device.available_input_routing_channels` -- list of channel objects
- `device.input_routing_channel = channels[i]` -- sets the source channel

**Resolution strategy:**
1. Iterate `song.tracks` to find track with matching name (case-insensitive)
2. Iterate `device.available_input_routing_types` to find entry whose `display_name` matches the track name
3. Set `device.input_routing_type` to the matched entry
4. Set `device.input_routing_channel` to "Pre FX" or first available channel

### Pattern 5: Master Recipe Data Structure

**Recommendation:** Add `MASTER_RECIPE` as a separate constant in each existing genre file (`house.py`, `techno.py`, `ambient.py`, `drum_and_bass.py`). This keeps recipe data co-located per genre and follows the existing pattern.

**Structure:**
```python
MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -8,       # dB
        "Ratio": 0.4,          # 0-1 (approx 2:1)
        "Attack": 10,          # ms
        "Release": 200,        # ms
        ...
    },
    "MultibandDynamics": {
        ...
    },
    "Limiter": {
        "Ceiling": -0.3,       # dB
        "Gain": 0.0,           # dB
        ...
    },
}
```

**Discovery update:** `mixing/catalog.py` needs a `get_master_recipe(genre)` function that discovers and returns `MASTER_RECIPE` from genre modules (parallel to `get_recipe()` for `RECIPE`).

### Anti-Patterns to Avoid

- **Polling from MCP side:** Do NOT have the MCP tool poll for device load completion. All verification happens inside the RS handler. One socket round-trip, one response.
- **Converting in RS:** Do NOT put conversion logic in the Remote Script. RS receives only normalized values (D-03).
- **Matching devices by display name:** Use `device.class_name`, not `device.name` (user-renameable per D-04).
- **Loading devices that already exist:** Always check `track.devices` first before loading (D-04).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Device loading | Custom browser navigation | Existing `_resolve_browser_path` + `browser.load_item` pattern from `load_browser_item` handler | Handles URI caching, retry logic, verification |
| Track resolution | Manual track index/type logic | Existing `_resolve_track(song, track_type, track_index)` | Already handles "track", "return", "master" |
| Device resolution | Manual device indexing | Existing `_resolve_device(params)` from `DeviceHandlers` | Already handles chain navigation |
| Parameter lookup by name | Custom iteration | Reuse the case-insensitive pattern from `_set_device_parameter` | Handles case, reports available params on miss |
| Sidechain index routing | Custom routing logic | Build on existing `set_compressor_sidechain` which uses `available_input_routing_types` API | Already validates indices, handles errors |

## Common Pitfalls

### Pitfall 1: Device Load Timing Race Condition
**What goes wrong:** Setting parameters on a device that hasn't finished loading, resulting in errors or silently dropped values.
**Why it happens:** `browser.load_item()` is asynchronous in Ableton. The device appears in `track.devices` after some ticks.
**How to avoid:** Use the `schedule_message` + verify pattern from `load_browser_item`. After calling `load_item`, schedule a verification callback that checks `len(track.devices)` increased, THEN set parameters.
**Warning signs:** Intermittent parameter-set failures; devices loaded but with default params.

### Pitfall 2: Log Conversion Edge Cases
**What goes wrong:** Division by zero or math domain errors in logarithmic conversion.
**Why it happens:** `log(0)` is undefined. If `natural_min` is 0 or `natural` value is 0, the formula breaks.
**How to avoid:** Clamp input values to `max(natural, natural_min)` before applying log conversion. CATALOG has `natural_min: 20` for frequency params so 0 Hz should not appear in recipes, but defensive clamping is cheap.
**Warning signs:** `ValueError: math domain error` during recipe application.

### Pitfall 3: Quantized Parameter Conversion
**What goes wrong:** Applying floating-point conversion to enum/toggle parameters produces fractional values that Ableton rejects or rounds unexpectedly.
**Why it happens:** Filter type (0-7), on/off (0-1), etc. have `is_quantized: True` and `conversion: None`. They need integer values, not float conversion.
**How to avoid:** For params with `conversion: None`, pass through directly. For quantized params, round to nearest int after any processing.

### Pitfall 4: Master Track Has No track_index
**What goes wrong:** RS handler tries to index `song.tracks[track_index]` when `track_type == "master"`.
**Why it happens:** Master track is `song.master_track`, not in the `song.tracks` collection.
**How to avoid:** `_resolve_track` already handles this -- when `track_type == "master"`, it returns `song.master_track` and ignores `track_index`. Use it consistently.

### Pitfall 5: Sidechain Routing Type Display Name Mismatch
**What goes wrong:** Track name doesn't match any `available_input_routing_types` entry.
**Why it happens:** Ableton may format routing type names differently from track names (e.g., adding "-Audio" suffix or truncating).
**How to avoid:** Use substring/contains matching when scanning `available_input_routing_types` for the track name. Log available types on failure for debugging.

### Pitfall 6: Connection Timeout for Multi-Device Apply
**What goes wrong:** `apply_recipe` command times out because loading multiple devices takes longer than the default socket timeout.
**Why it happens:** Default write timeout is 15s. Loading 3+ devices with verification could take 10-30s.
**How to avoid:** Add `apply_recipe` and `apply_master_recipe` to `_BROWSER_COMMANDS` in `connection.py` (30s timeout), or increase the RS self_scheduling timeout. The `load_browser_item` precedent uses 30s.

## Code Examples

### Natural-to-Normalized Conversion Function

```python
# MCP_Server/devices/convert.py
import math
from MCP_Server.devices.catalog import CATALOG


def natural_to_normalized(device_class: str, param_name: str, natural_value: float) -> float:
    """Convert a natural-unit value to normalized 0.0-1.0 for the Ableton API.

    For params with no conversion metadata, returns the value unchanged.
    """
    entry = CATALOG.get(device_class)
    if entry is None:
        return natural_value

    param_info = None
    for p in entry["parameters"]:
        if p["name"] == param_name:
            param_info = p
            break
    if param_info is None:
        return natural_value

    conv = param_info.get("conversion")
    if conv is None:
        # No conversion -- value is already in device's native range
        # Clamp to parameter min/max
        return max(param_info["min"], min(param_info["max"], natural_value))

    n_min = conv["natural_min"]
    n_max = conv["natural_max"]
    conv_type = conv["type"]

    # Clamp to natural range
    clamped = max(n_min, min(n_max, natural_value))

    if conv_type == "log":
        if n_min <= 0:
            n_min = 1e-10  # defensive
        return math.log(clamped / n_min) / math.log(n_max / n_min)
    elif conv_type in ("linear", "linear_db"):
        return (clamped - n_min) / (n_max - n_min)
    else:
        return natural_value
```

### Batch Conversion for Full Recipe

```python
# In MCP_Server/tools/mixing.py
def _convert_recipe_to_normalized(recipe: dict) -> list:
    """Convert a recipe dict {device_class: {param: natural_value}} to RS payload.

    Returns list of {class_name, params: {param_name: normalized_value}}.
    """
    devices = []
    for device_class, params in recipe.items():
        normalized = {}
        for param_name, natural_value in params.items():
            normalized[param_name] = natural_to_normalized(
                device_class, param_name, natural_value
            )
        devices.append({"class_name": device_class, "params": normalized})
    return devices
```

### RS apply_recipe Handler Skeleton

```python
# In AbletonMCP_Remote_Script/handlers/devices.py
@command("apply_recipe", write=True, self_scheduling=True)
def _apply_recipe(self, params):
    """Atomically load missing devices and set all parameters.

    Params:
        track_index: int
        track_type: "track" | "return" | "master"
        devices: list of {class_name: str, params: {param_name: normalized_value}}
    """
    track_index = params.get("track_index", 0)
    track_type = params.get("track_type", "track")
    devices_spec = params.get("devices", [])

    track = _resolve_track(self._song, track_type, track_index)
    response_queue = queue.Queue()

    # Phase 1: identify existing vs. missing devices
    existing = {}  # class_name -> device object (first match)
    for d in track.devices:
        cn = d.class_name
        if cn not in existing:
            existing[cn] = d

    to_load = []
    for spec in devices_spec:
        cn = spec["class_name"]
        if cn not in existing:
            to_load.append(spec)

    # Phase 2: load missing devices, then set all params
    # ... (uses schedule_message pattern like load_browser_item)
```

### RS set_sidechain_source Handler Skeleton

```python
@command("set_sidechain_source", write=True)
def _set_sidechain_source(self, params):
    """Set compressor sidechain source by track name.

    Params:
        track_index: int (track containing the compressor)
        device_index: int
        track_type: "track" | "return" | "master"
        source_track_name: str (name of the source track)
    """
    source_track_name = params.get("source_track_name")
    device, _track = self._resolve_device(params)

    if not hasattr(device, "available_input_routing_types"):
        raise ValueError(f"Device '{device.name}' does not support sidechain routing")

    # Resolve source track name to routing type
    name_lower = source_track_name.lower()
    matched_type = None
    for rt in device.available_input_routing_types:
        if name_lower in rt.display_name.lower():
            matched_type = rt
            break

    if matched_type is None:
        available = [rt.display_name for rt in device.available_input_routing_types]
        raise ValueError(
            f"Source track '{source_track_name}' not found in sidechain routing options. "
            f"Available: {available}"
        )

    device.input_routing_type = matched_type
    # ... set channel to Pre FX or first available
```

## Project Constraints (from CLAUDE.md)

No CLAUDE.md file exists in the project root. No additional project-specific constraints beyond the CONTEXT.md decisions.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N sequential `set_device_parameter` calls per recipe | Single `apply_recipe` RS command (this phase) | Phase 31 | Reduces N+M socket round-trips to 1 |
| Manual device loading + param setting | Atomic load-then-set in RS handler | Phase 31 | Eliminates race conditions on device instantiation |
| Sidechain by track index | Sidechain by track name | Phase 31 | User-friendly; resilient to track reordering |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pytest.ini` (if exists) or default |
| Quick run command | `python -m pytest tests/test_mixing.py tests/test_convert.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BATCH-01 | Batch param set in one RS round-trip | unit (mock) | `pytest tests/test_mixing.py::TestBatchParameterSetting -x` | Wave 0 |
| APPLY-01 | apply_mix_recipe MCP tool returns success | unit (mock) | `pytest tests/test_mixing.py::TestApplyMixRecipe -x` | Wave 0 |
| APPLY-02 | apply_master_recipe MCP tool applies chain | unit (mock) | `pytest tests/test_mixing.py::TestApplyMasterRecipe -x` | Wave 0 |
| APPLY-03 | Atomicity -- params set after device confirmed | unit (mock) | `pytest tests/test_mixing.py::TestApplyAtomicity -x` | Wave 0 |
| SIDE-01 | set_sidechain_source resolves by name | unit (mock) | `pytest tests/test_mixing.py::TestSidechainSource -x` | Wave 0 |
| N/A | natural_to_normalized conversion correctness | unit (pure) | `pytest tests/test_convert.py -x` | Wave 0 |
| N/A | MASTER_RECIPE data structure + catalog validation | unit (pure) | `pytest tests/test_mixing.py::TestMasterRecipeData -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_mixing.py tests/test_convert.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_convert.py` -- natural_to_normalized unit tests (pure functions, no mocks needed)
- [ ] `tests/test_mixing.py` -- add TestMasterRecipeData, TestApplyMixRecipe, TestApplyMasterRecipe, TestSidechainSource, TestBatchParameterSetting classes
- [ ] `tests/conftest.py` -- add `"MCP_Server.tools.mixing.get_ableton_connection"` to `_GAC_PATCH_TARGETS`

## Open Questions

1. **Browser path for Multiband Dynamics**
   - What we know: All other built-in effect paths follow `audio_effects/<Display Name>` pattern
   - What's unclear: Whether Ableton's browser uses "Multiband Dynamics" or a different name
   - Recommendation: Include "audio_effects/Multiband Dynamics" in DEVICE_PATHS; verify during manual UAT. HIGH confidence based on pattern.

2. **Sidechain routing type display names**
   - What we know: `available_input_routing_types` returns objects with `.display_name` properties
   - What's unclear: Exact format of display names (e.g., "1-Kick" vs "Kick" vs track name verbatim)
   - Recommendation: Use substring matching (contains) rather than exact match. Log available options on failure.

3. **apply_recipe timeout for many devices**
   - What we know: Typical recipe has 2-4 devices. `load_browser_item` uses 30s timeout for one device.
   - What's unclear: Whether loading 4 devices sequentially within one RS handler could exceed 30s
   - Recommendation: Use 30s timeout (same as browser commands). If needed, can increase later. Most recipes have 3 devices max.

## Sources

### Primary (HIGH confidence)
- `AbletonMCP_Remote_Script/handlers/devices.py` -- existing `set_device_parameter`, `set_compressor_sidechain` patterns
- `AbletonMCP_Remote_Script/handlers/browser.py` -- `load_browser_item` self_scheduling + verify pattern
- `AbletonMCP_Remote_Script/registry.py` -- `@command(write=True, self_scheduling=True)` decorator
- `MCP_Server/devices/catalog.py` -- CATALOG with conversion metadata (type: log/linear/linear_db)
- `MCP_Server/mixing/*.py` -- recipe data structure (RECIPE constant, natural units)
- `MCP_Server/connection.py` -- timeout constants, _BROWSER_COMMANDS, _WRITE_COMMANDS sets

### Secondary (MEDIUM confidence)
- `MCP_Server/tools/devices.py` -- MCP tool patterns for `load_instrument_or_effect`, `set_device_parameter`
- `MCP_Server/tools/mixing.py` -- existing `get_mix_recipe` MCP tool pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries and patterns are existing project code; no new dependencies
- Architecture: HIGH -- directly extends proven patterns (load_browser_item, set_device_parameter, mixing catalog)
- Pitfalls: HIGH -- identified from examining actual async loading code and conversion metadata
- Conversion logic: HIGH -- three conversion types verified in CATALOG; math is straightforward

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- internal project architecture, no external dependencies)
