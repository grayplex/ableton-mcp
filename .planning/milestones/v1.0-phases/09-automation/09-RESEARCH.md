# Phase 9: Automation - Research

**Researched:** 2026-03-16
**Domain:** Ableton Live Python API -- clip automation envelopes (Session View)
**Confidence:** MEDIUM

## Summary

Phase 9 implements three automation operations on Session View clips: reading automation envelopes, inserting breakpoints, and clearing envelopes. The Ableton Live Python API provides direct support through `Clip.automation_envelope(DeviceParameter)` returning an `AutomationEnvelope` object, `Clip.clear_envelope(DeviceParameter)`, and `Clip.clear_all_envelopes()`. The `AutomationEnvelope` class exposes `insert_step(time, value, step_length)` for writing and `value_at_time(time)` for reading.

The critical API limitation is that there is no method to enumerate or iterate breakpoints directly from an `AutomationEnvelope`. The API only exposes `value_at_time()` for reading, which means "get breakpoints" must be implemented as sampling at regular intervals. The `insert_step()` method takes three float parameters (time, value, step_length) whose exact semantics are not fully documented by Ableton -- the third parameter appears to control the duration of the step. The `has_envelopes` property on `Clip` can be used as a quick check before iterating device parameters.

**Primary recommendation:** Implement the three automation handlers following the established mixin pattern. For reading, sample `value_at_time()` at configurable intervals. For writing, call `insert_step()` in a batch loop. For clearing, use the native `clear_envelope()` and `clear_all_envelopes()` methods directly.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Parameter targeting: Flat parameters in a single tool call: track_index, clip_index, device_index, parameter_name/parameter_index
- Combines clip addressing (Phase 5 pattern) with device parameter addressing (Phase 7 pattern)
- Supports chain device parameters: optional chain_index + chain_device_index (reuses _resolve_device from Phase 7)
- Regular tracks only -- no track_type parameter needed (consistent with Phase 5 clip tools)
- Envelope read (get_clip_envelope): Dual mode -- no parameter specified returns list of all parameters with automation; with parameter specified returns breakpoint data. Breakpoint data format: {time: float (beats), value: float} pairs. If Live API doesn't expose raw breakpoints, sample at regular intervals.
- Envelope write (insert_envelope_breakpoints): Batch insert accepting list of {time, value} pairs. Merge with existing automation. Response: parameter name, device name, breakpoints_inserted count, total_breakpoints count.
- Envelope clear (clear_clip_envelopes): Dual mode -- with parameter clears that parameter's envelope; without parameter clears ALL envelopes. Response: list of cleared parameter names, envelopes_cleared count.

### Claude's Discretion
- Whether to include curve/interpolation info in breakpoint data if the Live API exposes it
- Sampling interval if raw breakpoints aren't directly accessible from the API
- How to handle the Session vs Arrangement envelope distinction internally
- Whether to include parameter min/max in envelope responses for AI context

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTO-01 | User can get automation envelope for a device parameter in a clip | `Clip.automation_envelope(DeviceParameter)` returns `AutomationEnvelope`; `value_at_time(float)` samples values; `Clip.has_envelopes` for quick check; iterate device parameters to list all automated ones |
| AUTO-02 | User can insert automation breakpoints into a clip envelope | `AutomationEnvelope.insert_step(time, value, step_length)` inserts breakpoints; batch loop pattern from `add_notes_to_clip` |
| AUTO-03 | User can clear automation envelopes from a clip | `Clip.clear_envelope(DeviceParameter)` for single parameter; `Clip.clear_all_envelopes()` for all; dual mode per CONTEXT decision |

</phase_requirements>

## Standard Stack

This phase adds no new external dependencies. It extends the existing codebase using the same patterns as previous phases.

### Core (existing project stack)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Ableton Live Python API (LOM) | Live 12 / Python 3.11 | Clip automation envelope control | Native API, no alternative exists |
| mcp[cli] | >=1.3.0 | MCP tool registration | Already in project |
| pytest + pytest-asyncio | >=8.3 / >=0.25 | Smoke testing | Already configured |
| ruff | >=0.15.6 | Linting | Already configured |

### Supporting
No new libraries needed. All automation functionality is provided by the Live Object Model.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Sampling via value_at_time() | Breakpoint enumeration API | No breakpoint enumeration exists in LOM; sampling is the only option |

## Architecture Patterns

### Recommended Project Structure (additions only)
```
AbletonMCP_Remote_Script/
  handlers/
    automation.py       # NEW: AutomationHandlers mixin class
MCP_Server/
  tools/
    automation.py       # NEW: 3 MCP tool functions
tests/
  test_automation.py    # NEW: Smoke tests for automation tools
```

### Pattern 1: Mixin Handler Class (established Phase 2+)
**What:** New `AutomationHandlers` class in `handlers/automation.py` following the mixin pattern.
**When to use:** Every new domain handler.
**Example:**
```python
# Source: Established project pattern (handlers/notes.py, handlers/devices.py)
from AbletonMCP_Remote_Script.handlers.clips import _resolve_clip_slot
from AbletonMCP_Remote_Script.registry import command


class AutomationHandlers:
    """Mixin class for automation envelope command handlers."""

    @command("get_clip_envelope")
    def _get_clip_envelope(self, params):
        ...

    @command("insert_envelope_breakpoints", write=True)
    def _insert_envelope_breakpoints(self, params):
        ...

    @command("clear_clip_envelopes", write=True)
    def _clear_clip_envelopes(self, params):
        ...
```

### Pattern 2: Clip + Device Resolution Combination
**What:** Automation tools combine clip addressing (`_resolve_clip_slot`) and device parameter resolution (`_resolve_device` or inline parameter lookup) in a single handler.
**When to use:** Automation operations that target a specific parameter on a specific clip.
**Example:**
```python
# Resolve the clip first (Phase 5 pattern)
clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
clip = clip_slot.clip

# Resolve the device (Phase 7 _resolve_device pattern)
device, _ = self._resolve_device(params)

# Find the parameter by name or index (Phase 7 pattern)
param = self._resolve_parameter(device, parameter_name, parameter_index)

# Get the automation envelope for this parameter on this clip
envelope = clip.automation_envelope(param)
```

### Pattern 3: Dual-Mode Commands (list vs. detail)
**What:** A single command returns different response shapes depending on whether a parameter is specified.
**When to use:** `get_clip_envelope` and `clear_clip_envelopes` per CONTEXT decisions.
**Example:**
```python
@command("get_clip_envelope")
def _get_clip_envelope(self, params):
    # If parameter_name/parameter_index not provided: list mode
    # If provided: detail mode with breakpoint data
    if parameter_name is None and parameter_index is None:
        # Iterate all device parameters, check which have envelopes
        return {"parameters_with_automation": [...]}
    else:
        # Return sampled breakpoint data for specific parameter
        return {"parameter_name": ..., "breakpoints": [...]}
```

### Pattern 4: Sampling Envelope Values (reading breakpoints)
**What:** Since the LOM does not expose raw breakpoints, sample `value_at_time()` at regular intervals to reconstruct the envelope shape.
**When to use:** `get_clip_envelope` detail mode.
**Example:**
```python
# Sample the envelope at regular intervals across the clip length
envelope = clip.automation_envelope(param)
if envelope is None:
    return {"parameter_name": param.name, "has_automation": False, "breakpoints": []}

sample_interval = 0.25  # beats (1/16th note default)
breakpoints = []
t = 0.0
while t <= clip.length:
    val = envelope.value_at_time(t)
    breakpoints.append({"time": round(t, 4), "value": round(val, 6)})
    t += sample_interval

return {
    "parameter_name": param.name,
    "device_name": device.name,
    "has_automation": True,
    "sample_interval": sample_interval,
    "breakpoints": breakpoints,
}
```

### Pattern 5: Batch Insert (writing breakpoints)
**What:** Accept a list of {time, value} pairs and call `insert_step()` for each in sequence, mirroring the `add_notes_to_clip` batch pattern.
**When to use:** `insert_envelope_breakpoints`.
**Example:**
```python
@command("insert_envelope_breakpoints", write=True)
def _insert_envelope_breakpoints(self, params):
    # ... resolve clip, device, parameter ...
    envelope = clip.automation_envelope(param)
    # envelope may be None if no automation exists yet;
    # insert_step may create it implicitly (needs runtime validation)

    breakpoints = params.get("breakpoints", [])
    step_length = params.get("step_length", 0.0)

    for bp in breakpoints:
        envelope.insert_step(bp["time"], bp["value"], step_length)

    return {
        "parameter_name": param.name,
        "device_name": device.name,
        "breakpoints_inserted": len(breakpoints),
    }
```

### Anti-Patterns to Avoid
- **Attempting to read raw breakpoints from AutomationEnvelope:** The LOM has no method to enumerate breakpoints directly. Do not try to access internal breakpoint lists. Use `value_at_time()` sampling instead.
- **Assuming automation_envelope() creates the envelope:** It returns `None` if no automation exists. The `insert_step()` call on a non-existent envelope will fail. Need to handle the case where `automation_envelope()` returns None before the first `insert_step()` call.
- **Using track_type parameter for clip operations:** Per CONTEXT, clip automation is regular tracks only (consistent with Phase 5 clip tools). Do not add a track_type parameter.
- **Arrangement automation:** `automation_envelope()` returns `None` for Arrangement clips. This phase only covers Session View clip envelopes. No special handling needed -- just ensure clear error messages if the clip is an arrangement clip.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Clip resolution | Custom clip finder | `_resolve_clip_slot(song, track_index, clip_index)` from clips.py | Already handles bounds checking and error messages |
| Device resolution | Custom device navigator | `self._resolve_device(params)` from DeviceHandlers | Already handles track_type, chain navigation, error messages |
| Parameter lookup | Custom parameter search | Inline loop matching `set_device_parameter` pattern | Case-insensitive first-match already proven in Phase 7 |
| Envelope clearing | Manual per-parameter loop | `clip.clear_all_envelopes()` | Native LOM method, handles all edge cases |
| Command registration | Manual dispatch dict | `@command` decorator from registry.py | Project standard since Phase 2 |

**Key insight:** The automation domain reuses TWO existing resolution patterns (clip + device) rather than introducing new ones. The only truly new code is the envelope interaction logic.

## Common Pitfalls

### Pitfall 1: automation_envelope() Returns None
**What goes wrong:** Calling methods on `None` when no automation exists for a parameter.
**Why it happens:** `automation_envelope()` returns `None` if (a) no automation exists for that parameter, (b) the clip is an Arrangement clip, or (c) the parameter belongs to a different track.
**How to avoid:** Always check `if envelope is None` before calling `insert_step()` or `value_at_time()`. For insert operations, may need to call `insert_step()` once to create the envelope, or handle the None case with a clear error.
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'insert_step'`

### Pitfall 2: insert_step() Third Parameter Semantics
**What goes wrong:** The third parameter of `insert_step(time, value, step_length)` is not officially documented. Passing wrong values may create unexpected automation shapes.
**Why it happens:** Ableton's internal API documentation only shows type signatures, not semantic parameter names.
**How to avoid:** Default `step_length` to 0.0 for point breakpoints (instantaneous value changes). Allow the caller to optionally specify it. Document that this parameter controls the duration of the step and may need runtime experimentation.
**Warning signs:** Automation shapes don't match expected behavior in Ableton's UI.

### Pitfall 3: Session vs Arrangement Envelope Distinction
**What goes wrong:** `automation_envelope()` returns `None` for Arrangement clips, leading to confusing "no automation" errors when automation visibly exists in Ableton.
**Why it happens:** In Arrangement View, automation lives on track lanes, not on clips. The `Clip.automation_envelope()` method only works for Session View clips.
**How to avoid:** Check `clip.is_arrangement_clip` (if available) or document that this feature only works with Session View clips. Include a clear error message: "Automation envelopes are only supported for Session View clips."
**Warning signs:** All automation reads return empty on arrangement clips.

### Pitfall 4: Parameter Belongs to Different Track
**What goes wrong:** `automation_envelope()` returns `None` even though the parameter exists, because the parameter's device is on a different track than the clip.
**Why it happens:** You can only automate parameters from devices on the same track as the clip.
**How to avoid:** The flat parameter targeting (track_index, clip_index, device_index) naturally prevents this since both the clip and device are resolved from the same track. But document this constraint clearly.
**Warning signs:** `automation_envelope()` returns `None` despite correct parameter.

### Pitfall 5: Enumeration of Automated Parameters is Expensive
**What goes wrong:** The "list mode" (no parameter specified) for `get_clip_envelope` requires iterating ALL parameters of ALL devices on the track and checking each with `automation_envelope()`. This can be slow for tracks with many devices.
**Why it happens:** The LOM has `Clip.has_envelopes` (boolean) but no method to get a list of which parameters have automation.
**How to avoid:** Use `clip.has_envelopes` as an early exit -- if `False`, return empty list immediately without iterating. Consider limiting to a reasonable number of devices/parameters or adding a timeout.
**Warning signs:** Slow response times on tracks with many devices/parameters.

### Pitfall 6: Value Range Mismatch
**What goes wrong:** Breakpoint values inserted outside the parameter's min/max range cause unexpected behavior.
**Why it happens:** Automation values should be within the parameter's `min`/`max` range, but `insert_step()` may not clamp automatically.
**How to avoid:** Clamp breakpoint values to `param.min`/`param.max` before calling `insert_step()`, with a warning in the response (same pattern as `set_device_parameter`).
**Warning signs:** Automation line appears flat at min or max in Ableton's UI.

## Code Examples

Verified patterns from the Live Object Model API and existing project code.

### Getting an Automation Envelope
```python
# Source: Live 11.0.0 API Documentation (nsuspray.github.io)
# Clip.automation_envelope(DeviceParameter) -> AutomationEnvelope | None
envelope = clip.automation_envelope(param)  # param is a DeviceParameter object
if envelope is None:
    # No automation exists for this parameter on this clip
    pass
```

### Reading Envelope Values
```python
# Source: Live 11.0.0 API Documentation
# AutomationEnvelope.value_at_time(float) -> float
value = envelope.value_at_time(2.0)  # Value at beat 2.0
```

### Inserting Automation Steps
```python
# Source: Live 11.0.0 API Documentation
# AutomationEnvelope.insert_step(float, float, float) -> None
# Parameters: (time, value, step_length)
envelope.insert_step(0.0, 0.5, 0.0)   # Point at beat 0, value 0.5
envelope.insert_step(2.0, 1.0, 0.0)   # Point at beat 2, value 1.0
envelope.insert_step(4.0, 0.0, 0.25)  # Step at beat 4, value 0.0, 0.25 beat duration
```

### Clearing Envelopes
```python
# Source: Live 11.0.0 API Documentation
# Clear a specific parameter's automation
clip.clear_envelope(param)  # param is a DeviceParameter object

# Clear ALL automation from the clip
clip.clear_all_envelopes()
```

### Checking for Existing Automation
```python
# Source: LOM documentation (cycling74.com Max 8 docs)
# Clip.has_envelopes -> bool (property)
if clip.has_envelopes:
    # Iterate device parameters to find which ones have automation
    for param in device.parameters:
        env = clip.automation_envelope(param)
        if env is not None:
            # This parameter has automation
            pass
```

### Resolving Parameter by Name or Index (existing pattern)
```python
# Source: handlers/devices.py _set_device_parameter
# Case-insensitive first-match lookup
if parameter_name is not None:
    name_lower = parameter_name.lower()
    param = None
    for i, p in enumerate(device.parameters):
        if p.name.lower() == name_lower:
            param = p
            matched_index = i
            break
    if param is None:
        available = [p.name for p in device.parameters]
        raise ValueError(f"Parameter '{parameter_name}' not found. Available: {available}")
elif parameter_index is not None:
    if parameter_index < 0 or parameter_index >= len(device.parameters):
        raise IndexError(f"Parameter index {parameter_index} out of range (0-{len(device.parameters) - 1})")
    param = device.parameters[parameter_index]
```

### MCP Tool Pattern (existing pattern)
```python
# Source: MCP_Server/tools/notes.py, devices.py
@mcp.tool()
def get_clip_envelope(
    ctx: Context,
    track_index: int,
    clip_index: int,
    device_index: int,
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
    sample_interval: float = 0.25,
) -> str:
    """Get automation envelope for a device parameter in a clip..."""
    try:
        ableton = get_ableton_connection()
        params = {"track_index": track_index, "clip_index": clip_index, "device_index": device_index}
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        if sample_interval != 0.25:
            params["sample_interval"] = sample_interval
        result = ableton.send_command("get_clip_envelope", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error("Failed to get clip envelope", detail=str(e), suggestion="...")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No automation API | `Clip.automation_envelope()` + `AutomationEnvelope` class | Live 9+ | Enables programmatic automation control |
| Python 2 Remote Scripts | Python 3.11 Remote Scripts | Live 11 | All code uses modern Python idioms |
| Manual breakpoint enumeration | `value_at_time()` sampling | Always (API never exposed raw breakpoints) | Must sample; cannot read native breakpoint list |

**Deprecated/outdated:**
- The `Clip.automation_envelope()` method existed since at least Live 9. No indication of deprecation in Live 12.
- No newer automation API has been introduced -- `insert_step` and `value_at_time` remain the standard approach.

## Open Questions

1. **What exactly does insert_step's third parameter (step_length) control?**
   - What we know: The C++ signature is `void insert_step(AAutomation {lvalue}, double, double, double)`. Based on method name and context, the three parameters are (time, value, step_length).
   - What's unclear: Whether step_length=0.0 creates a point breakpoint (instantaneous change) or a zero-duration step. Whether non-zero values create a held step or affect curve interpolation.
   - Recommendation: Default to 0.0 in the handler. Include as an optional parameter for power users. Document as "step duration in beats" with a note that this needs runtime validation. Confidence: LOW.

2. **Does insert_step create the envelope if automation_envelope() returns None?**
   - What we know: `automation_envelope()` returns `None` when no automation exists. `insert_step()` is a method on `AutomationEnvelope`, so it cannot be called on `None`.
   - What's unclear: Whether calling `insert_step()` on a freshly-obtained (non-None) envelope for a parameter that had no automation creates the automation, or if there's a separate "create envelope" step needed.
   - Recommendation: Try getting the envelope, and if `None`, try inserting a breakpoint and then re-fetching. If the first insert fails, investigate `clip.clear_envelope(param)` as a potential "create then clear" workaround. This needs runtime testing. Confidence: LOW.

3. **Can Clip.has_envelopes distinguish between Session and Arrangement automation?**
   - What we know: `has_envelopes` is a boolean property. `automation_envelope()` returns `None` for Arrangement clips.
   - What's unclear: Whether `has_envelopes` returns True for Arrangement clips that have track-level automation.
   - Recommendation: Rely on `automation_envelope()` returning `None` as the definitive check rather than `has_envelopes` alone. Confidence: MEDIUM.

4. **What is a reasonable default sampling interval?**
   - What we know: 0.25 beats (1/16th note) is common for automation granularity. Finer intervals produce more data points.
   - What's unclear: Performance impact of very fine sampling (e.g., 0.0625 = 1/64th) on large clips.
   - Recommendation: Default to 0.25 (1/16th note). Allow override via parameter. For a 4-beat clip, this produces 17 samples -- lightweight. For a 64-beat clip, 257 samples -- still reasonable. Confidence: HIGH.

## Discretion Decisions (Research Recommendations)

Based on the "Claude's Discretion" items from CONTEXT.md:

1. **Curve/interpolation info:** The API does not expose curve type or interpolation mode per breakpoint. `insert_step` has only time/value/step_length. **Recommendation:** Do not include curve info -- it is not accessible. Document this limitation.

2. **Sampling interval:** Default 0.25 beats (1/16th note). Configurable via `sample_interval` parameter. **Recommendation:** 0.25 is a good balance of detail vs. response size.

3. **Session vs Arrangement distinction:** `automation_envelope()` returns `None` for Arrangement clips. **Recommendation:** Let the API handle it naturally. If envelope is None and clip has no automation, return clear message. No need for explicit Session/Arrangement detection code.

4. **Parameter min/max in responses:** **Recommendation:** Yes, include parameter `min`, `max`, and `value` (current static value) in the envelope read response. This gives the AI context about the parameter's range without requiring a separate `get_device_parameters` call. Minimal overhead since the parameter object is already resolved.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.25+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_automation.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTO-01 | get_clip_envelope tool registered + returns JSON | smoke | `pytest tests/test_automation.py::test_automation_tools_registered -x` | Wave 0 |
| AUTO-01 | get_clip_envelope list mode (no param) | smoke | `pytest tests/test_automation.py::test_get_clip_envelope_list_mode -x` | Wave 0 |
| AUTO-01 | get_clip_envelope detail mode (with param) | smoke | `pytest tests/test_automation.py::test_get_clip_envelope_detail_mode -x` | Wave 0 |
| AUTO-02 | insert_envelope_breakpoints sends batch | smoke | `pytest tests/test_automation.py::test_insert_envelope_breakpoints -x` | Wave 0 |
| AUTO-03 | clear_clip_envelopes single param | smoke | `pytest tests/test_automation.py::test_clear_clip_envelopes_single -x` | Wave 0 |
| AUTO-03 | clear_clip_envelopes all | smoke | `pytest tests/test_automation.py::test_clear_clip_envelopes_all -x` | Wave 0 |
| ALL | Registry count updated to 63 | unit | `pytest tests/test_registry.py::TestFullRegistry -x` | Existing (needs update) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_automation.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_automation.py` -- covers AUTO-01, AUTO-02, AUTO-03 (smoke tests for MCP tools)
- [ ] `tests/test_registry.py` -- update expected count from 60 to 63 (3 new commands)
- [ ] `conftest.py` -- add `MCP_Server.tools.automation.get_ableton_connection` to `_GAC_PATCH_TARGETS`

## Integration Checklist

Files that MUST be modified (beyond new files):

1. **`AbletonMCP_Remote_Script/handlers/__init__.py`** -- add `from . import automation` to trigger `@command` registration
2. **`AbletonMCP_Remote_Script/__init__.py`** -- add `AutomationHandlers` to `AbletonMCP` MRO
3. **`MCP_Server/tools/__init__.py`** -- add `automation` to imports
4. **`MCP_Server/connection.py`** -- add automation write commands to `_WRITE_COMMANDS` frozenset
5. **`tests/conftest.py`** -- add `MCP_Server.tools.automation.get_ableton_connection` to `_GAC_PATCH_TARGETS`
6. **`tests/test_registry.py`** -- update expected count from 60 to 63 and add automation commands to expected set

## Sources

### Primary (HIGH confidence)
- [Live 11.0.0 API Documentation](https://nsuspray.github.io/Live_API_Doc/) -- `AutomationEnvelope` class, `Clip.automation_envelope()`, `clear_all_envelopes()`, `clear_envelope()`, `insert_step()`, `value_at_time()` signatures confirmed
- [Live 10.0.1 API Documentation](https://structure-void.com/PythonLiveAPI_documentation/Live10.0.1.xml) -- Cross-verified API signatures
- [AbletonLive-API-Stub](https://github.com/cylab/AbletonLive-API-Stub) -- API type stubs confirming method signatures
- [LOM - Max 8 Documentation](https://docs.cycling74.com/max8/vignettes/live_object_model) -- `Clip.has_envelopes`, `clear_all_envelopes`, `clear_envelope` confirmed
- Existing codebase: `handlers/devices.py`, `handlers/clips.py`, `handlers/notes.py`, `tools/notes.py`, `tools/devices.py` -- established patterns

### Secondary (MEDIUM confidence)
- [Clip Envelopes - Ableton Reference Manual 12](https://www.ableton.com/en/live-manual/12/clip-envelopes/) -- Session vs Arrangement distinction, clip envelope behavior
- [Ziforge/ableton-liveapi-tools](https://github.com/Ziforge/ableton-liveapi-tools) -- Confirms automation tools are feasible with 6 clip automation tools in their implementation

### Tertiary (LOW confidence)
- `insert_step` parameter semantics (time, value, step_length) -- inferred from C++ signature and method name; not officially documented with named parameters. Needs runtime validation.
- Whether `insert_step()` creates automation on a parameter that has none -- not documented. Needs runtime validation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all LOM methods confirmed in multiple API docs
- Architecture: HIGH -- follows established project patterns exactly (mixin, @command, MCP tool)
- API methods exist: HIGH -- `automation_envelope`, `insert_step`, `value_at_time`, `clear_envelope`, `clear_all_envelopes` confirmed in Live 10 and 11 API docs
- insert_step semantics: LOW -- third parameter meaning inferred, not officially named
- Envelope creation flow: LOW -- unclear if insert_step works when automation_envelope returns None
- Pitfalls: MEDIUM -- based on API behavior described in docs plus inference from method signatures

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable -- LOM API rarely changes between Live versions)
