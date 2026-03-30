# Phase 33: Mix Adjustment Intelligence - Research

**Researched:** 2026-03-28
**Domain:** MCP tool implementation -- diff computation between live device state and recipe targets
**Confidence:** HIGH

## Summary

Phase 33 delivers a single MCP tool `suggest_mix_adjustments` that compares a track's current device state (from `get_mix_state`) against the role x genre recipe and returns per-parameter diffs with one-sentence reasoning. This is a read-only analysis tool -- no parameters are changed.

The implementation is entirely MCP-side Python. No Remote Script changes are needed. The tool reuses existing infrastructure: `get_mix_state` RS command for current state, `get_recipe()` for target values, `natural_to_normalized()` for conversion, and `_infer_role()` for role inference. The one new piece is a `normalized_to_natural()` reverse conversion function for human-readable display values.

**Primary recommendation:** Implement `intelligence.py` as a single new tool module following the `analysis.py` pattern, with the reverse conversion helper added to `convert.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
1. **Tool Interface:** `suggest_mix_adjustments(track_name: str, genre: str, role: str = None) -> str` -- case-insensitive substring match on track_name, role inferred via `_infer_role()` if absent
2. **Diff Computation:** Convert recipe natural-unit values to normalized 0.0-1.0 via existing `natural_to_normalized()`, compare against current normalized values from `get_mix_state`
3. **Diff Threshold:** Skip suggestions where `abs(current - suggested) < 0.03` (fixed constant)
4. **Unloaded Device Handling:** Skip silently if recipe device not found on track's device chain
5. **Output Structure:** JSON grouped by device, with `total_suggestions` count, `current_display`/`suggested_display` natural-unit strings, and `reason` field per suggestion
6. **Implementation Scope:** MCP side only, new file `MCP_Server/tools/intelligence.py`, register in `MCP_Server/tools/__init__.py`

### Claude's Discretion
- Priority/impact ranking (sort suggestions by largest delta or most impactful parameter) -- nice-to-have, add if low cost

### Deferred Ideas (OUT OF SCOPE)
- Whole-session suggestions (suggest for all tracks at once) -- Phase 35 candidate
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INTEL-01 | User can request mix adjustment suggestions for a track -- returns parameter diffs with one-sentence reasons, based on comparing current device state against role x genre recipe, suggestions for review only | Fully supported by existing infrastructure: `get_mix_state` (STATE-01), `get_recipe()` (RECIP-01), `natural_to_normalized()` (convert.py). New: reverse conversion for display, diff logic, reason generation. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (json, math) | 3.10+ | JSON output, math for reverse log conversion | No external deps needed |
| mcp.server.fastmcp | 1.26.0 | `@mcp.tool()` decorator, `Context` type | Project-standard MCP registration |

### Supporting (existing project modules)
| Module | Purpose | When to Use |
|--------|---------|-------------|
| `MCP_Server.tools.analysis._infer_role` | Role inference from track name | When `role` param is None |
| `MCP_Server.devices.convert.natural_to_normalized` | Recipe natural values to normalized | Diff computation |
| `MCP_Server.mixing.catalog.get_recipe` | Fetch role x genre recipe dict | Recipe lookup |
| `MCP_Server.connection.get_ableton_connection` | RS socket connection | Calling `get_mix_state` RS command |
| `MCP_Server.connection.format_error` | Standardized error JSON | Error responses |
| `MCP_Server.devices.catalog.CATALOG` | Device parameter metadata | Reverse conversion (natural units for display) |

## Architecture Patterns

### Recommended Project Structure
```
MCP_Server/
  tools/
    intelligence.py      # NEW: suggest_mix_adjustments tool
    __init__.py           # ADD: import intelligence
  devices/
    convert.py            # ADD: normalized_to_natural() reverse conversion
```

### Pattern 1: Tool Module Pattern (from analysis.py)
**What:** Each tool module imports `mcp` from `MCP_Server.server`, decorates functions with `@mcp.tool()`, and is imported in `tools/__init__.py` to trigger registration.
**When to use:** All new MCP tools.
**Example:**
```python
# Source: MCP_Server/tools/analysis.py (existing pattern)
import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import get_ableton_connection
from MCP_Server.server import mcp

@mcp.tool()
def suggest_mix_adjustments(ctx: Context, track_name: str, genre: str, role: str = None) -> str:
    """..."""
    # 1. Get mix state via RS
    conn = get_ableton_connection()
    result = conn.send_command("get_mix_state", {})
    # 2. Find matching track
    # 3. Resolve role
    # 4. Get recipe
    # 5. Diff computation
    # 6. Return JSON
```

### Pattern 2: Track Name Matching (from check_gain_staging)
**What:** Case-insensitive substring match against track names from RS response. The tool iterates tracks from `get_mix_state` output and matches by substring.
**When to use:** Finding a user-specified track by name.
**Key detail:** `get_mix_state` returns tracks in `result["tracks"]` (regular), `result["return_tracks"]` (returns), and `result["master_track"]` (master). Must search all three groups.

### Pattern 3: Device Matching Between State and Recipe
**What:** Both `get_mix_state` RS output and recipe keys use CATALOG class names (e.g., `Eq8`, `Compressor2`, `DrumBuss`). Direct string equality match.
**Why it works:** The RS handler reads `device.class_name` from the Ableton LOM, and recipe dicts are keyed by the same CATALOG class names.
**Key detail from CATALOG:**
| Class Name | Display Name |
|------------|-------------|
| `Eq8` | EQ Eight |
| `Compressor2` | Compressor |
| `DrumBuss` | Drum Buss |
| `Reverb` | Reverb |
| `Delay` | Delay |
| `StereoGain` | Utility |
| `GlueCompressor` | Glue Compressor |
| `AutoFilter2` | Auto Filter |
| `Gate` | Gate |
| `Limiter` | Limiter |
| `MultibandDynamics` | Multiband Dynamics |

### Pattern 4: Reverse Conversion (normalized_to_natural)
**What:** Inverse of `natural_to_normalized()` -- converts a 0.0-1.0 normalized value back to natural units (Hz, dB, ms, etc.) for human-readable display strings.
**Implementation (from convert.py conversion formulas):**
- `log`: `natural_value = natural_min * (natural_max / natural_min) ^ normalized`
- `linear` / `linear_db`: `natural_value = natural_min + normalized * (natural_max - natural_min)`
- `None` (no conversion): value is already in device range `[min, max]` -- return as-is (or "N/A")

**Where to add:** `MCP_Server/devices/convert.py` alongside `natural_to_normalized()`.

### Anti-Patterns to Avoid
- **Using display names for device matching:** The output structure shows display names like "EQ Eight" in the JSON output, but matching logic MUST use `class_name` (e.g., `Eq8`). Display names are for the output JSON keys only (per CONTEXT.md section 5).
- **Calling get_mix_state MCP tool instead of RS command:** The intelligence tool should call `conn.send_command("get_mix_state", {})` directly, not invoke the MCP tool wrapper. The MCP tool returns a JSON string; the RS command returns a dict. Calling the RS command directly avoids a redundant JSON serialize/deserialize cycle.
- **Modifying parameters:** This is a read-only analysis tool. No `set_device_parameter` or `apply_recipe` calls.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Natural-to-normalized conversion | Custom math per device | `natural_to_normalized()` from convert.py | Already handles log, linear, linear_db for all CATALOG params |
| Role inference | Custom string matching | `_infer_role()` from analysis.py | Already handles ROLES ordering, case insensitivity |
| Recipe lookup with alias resolution | Direct dict access | `get_recipe(role, genre)` from mixing/catalog.py | Handles genre aliases (dnb -> drum_and_bass), role aliases |
| Error formatting | Raw string returns | `format_error()` from connection.py | Consistent JSON error format across all tools |

**Key insight:** Nearly all infrastructure exists. The only new computation is: (1) the diff loop comparing normalized values, (2) reverse conversion for display strings, and (3) reason string generation.

## Common Pitfalls

### Pitfall 1: Output Display Name vs Class Name Confusion
**What goes wrong:** Using class names like "Eq8" in user-facing output instead of display names like "EQ Eight".
**Why it happens:** Recipe keys and RS output both use class names. Easy to pass through unchanged.
**How to avoid:** Use `CATALOG[class_name]["display_name"]` for the output JSON device grouping keys. The CONTEXT.md output example shows `"EQ Eight"`, not `"Eq8"`.
**Warning signs:** Output shows cryptic names like "Compressor2" instead of "Compressor".

### Pitfall 2: Parameter Name Mismatch Between Recipe and State
**What goes wrong:** Recipe param name doesn't match RS param name, causing silent misses.
**Why it happens:** Recipe param names were authored to match CATALOG, but RS returns `p.name` from the Ableton LOM which should be identical. However, if there's any discrepancy, the param diff silently skips.
**How to avoid:** Use exact string equality on `p["name"]` from the RS response against recipe param keys. Both should use CATALOG-standard names. No fuzzy matching needed -- they come from the same source (Ableton LOM).
**Warning signs:** `total_suggestions: 0` when the mix clearly doesn't match the recipe.

### Pitfall 3: Quantized Parameters and Threshold
**What goes wrong:** Applying the 0.03 threshold to quantized parameters (like Filter Type, Model) that should be exact matches or skipped.
**Why it happens:** Some recipe params are quantized (integer selectors like EQ filter type). A 0.03 threshold still works numerically (quantized values differ by >= 1.0 in normalized range), but the display output should show the integer value, not a decimal.
**How to avoid:** The 0.03 threshold naturally works for quantized params since their normalized differences are large. For display: if `param_info.get("is_quantized")` is True, round the display value to int.

### Pitfall 4: Missing Device in State (Unloaded)
**What goes wrong:** Trying to access device params that don't exist on the track.
**Why it happens:** Recipe specifies devices not yet loaded on the track.
**How to avoid:** Per locked decision #4, skip silently. Iterate recipe devices, check if `class_name` exists in the track's device list from `get_mix_state`. If not found, continue to next device.

### Pitfall 5: Track Not Found
**What goes wrong:** `track_name` substring matches zero tracks or multiple tracks.
**Why it happens:** User provides ambiguous or incorrect track name.
**How to avoid:** Search all track groups (tracks, return_tracks, master_track). If zero matches, return `format_error`. If multiple matches, use first match (consistent with `check_gain_staging` behavior -- first match wins).

### Pitfall 6: Reverse Log Conversion Division by Zero
**What goes wrong:** `natural_min` is 0 in a log conversion, causing `log(0)`.
**Why it happens:** `natural_to_normalized` already guards against this with `safe_min = max(natural_min, 1e-10)`. The reverse must do the same.
**How to avoid:** Use the same `safe_min` guard in `normalized_to_natural()`.

## Code Examples

### Reverse Conversion Function (to add to convert.py)
```python
# Add to MCP_Server/devices/convert.py
def normalized_to_natural(
    device_class: str, param_name: str, normalized_value: float
) -> float | None:
    """Convert normalized 0.0-1.0 value back to natural units.

    Returns None if device/param not in CATALOG (no conversion possible).
    """
    device_entry = CATALOG.get(device_class)
    if device_entry is None:
        return None

    param_info = None
    for p in device_entry["parameters"]:
        if p["name"] == param_name:
            param_info = p
            break
    if param_info is None:
        return None

    conv = param_info.get("conversion")
    if conv is None:
        # No conversion -- value is in device range [min, max]
        return param_info["min"] + normalized_value * (param_info["max"] - param_info["min"])

    natural_min = conv["natural_min"]
    natural_max = conv["natural_max"]
    conv_type = conv["type"]

    if conv_type == "log":
        safe_min = natural_min if natural_min > 0 else 1e-10
        return safe_min * (natural_max / safe_min) ** normalized_value

    if conv_type in ("linear", "linear_db"):
        return natural_min + normalized_value * (natural_max - natural_min)

    return None
```

### Display Value Formatting
```python
def _format_display(device_class: str, param_name: str, normalized: float) -> str | None:
    """Format normalized value as human-readable natural-unit string."""
    natural = normalized_to_natural(device_class, param_name, normalized)
    if natural is None:
        return None

    # Look up unit from CATALOG
    device_entry = CATALOG.get(device_class)
    param_info = next((p for p in device_entry["parameters"] if p["name"] == param_name), None)

    if param_info and param_info.get("is_quantized"):
        return str(int(round(natural)))

    conv = param_info.get("conversion") if param_info else None
    if conv:
        unit = conv.get("unit", "")
        if unit == "Hz":
            return f"~{natural:.0f} Hz" if natural >= 1 else f"~{natural:.2f} Hz"
        if unit == "dB":
            return f"{natural:.1f} dB"
        if unit == "ms":
            return f"{natural:.0f} ms" if natural >= 1 else f"{natural:.2f} ms"
        if unit == "%":
            return f"{natural:.0f}%"
        return f"{natural:.2f}"

    return f"{natural:.3f}"
```

### Tool Registration (in __init__.py)
```python
# Current line in MCP_Server/tools/__init__.py:
from . import analysis, arrangement, ..., mixing, ...  # noqa: F401
# Change to:
from . import analysis, arrangement, ..., intelligence, mixing, ...  # noqa: F401
```

### Track Finding Logic
```python
def _find_track(mix_state: dict, track_name: str) -> dict | None:
    """Find track by case-insensitive substring match across all track groups."""
    name_lower = track_name.lower()

    # Search regular tracks first, then returns, then master
    for track in mix_state.get("tracks", []):
        if name_lower in track["name"].lower():
            return track
    for track in mix_state.get("return_tracks", []):
        if name_lower in track["name"].lower():
            return track
    master = mix_state.get("master_track")
    if master and name_lower in master["name"].lower():
        return master
    return None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N sequential get_device_parameter calls | Single get_mix_state RS command | Phase 32 | Intelligence tool can snapshot entire session in one call |
| Manual recipe lookup + mental comparison | Automated diff with threshold filtering | Phase 33 (this phase) | Users see actionable parameter-level suggestions |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `tests/` directory (standard discovery) |
| Quick run command | `python -m pytest tests/test_intelligence.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INTEL-01a | Tool returns parameter diffs with reasons | unit | `python -m pytest tests/test_intelligence.py::TestSuggestMixAdjustments::test_returns_diffs_with_reasons -x` | Wave 0 |
| INTEL-01b | Diffs based on comparing state vs recipe | unit | `python -m pytest tests/test_intelligence.py::TestSuggestMixAdjustments::test_diff_computation -x` | Wave 0 |
| INTEL-01c | Read-only -- no parameter changes | unit | `python -m pytest tests/test_intelligence.py::TestSuggestMixAdjustments::test_no_write_commands -x` | Wave 0 |
| INTEL-01d | Threshold filters trivial diffs | unit | `python -m pytest tests/test_intelligence.py::TestSuggestMixAdjustments::test_threshold_filtering -x` | Wave 0 |
| INTEL-01e | Unloaded devices skipped | unit | `python -m pytest tests/test_intelligence.py::TestSuggestMixAdjustments::test_missing_device_skipped -x` | Wave 0 |
| INTEL-01f | Track not found error | unit | `python -m pytest tests/test_intelligence.py::TestSuggestMixAdjustments::test_track_not_found -x` | Wave 0 |
| INTEL-01g | Role inference when role=None | unit | `python -m pytest tests/test_intelligence.py::TestSuggestMixAdjustments::test_role_inference -x` | Wave 0 |
| CONVERT-R | normalized_to_natural reverse conversion | unit | `python -m pytest tests/test_convert.py::TestNormalizedToNatural -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_intelligence.py tests/test_convert.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_intelligence.py` -- covers INTEL-01 (all sub-behaviors)
- [ ] New test class `TestNormalizedToNatural` in `tests/test_convert.py` -- covers reverse conversion

## Sources

### Primary (HIGH confidence)
- `MCP_Server/tools/analysis.py` -- tool pattern, `_infer_role()`, `get_mix_state` usage
- `MCP_Server/devices/convert.py` -- `natural_to_normalized()` conversion formulas (reverse needed)
- `MCP_Server/mixing/catalog.py` -- `get_recipe()` API
- `MCP_Server/devices/catalog.py` -- CATALOG structure, class names, parameter metadata
- `MCP_Server/tools/__init__.py` -- tool registration pattern
- `AbletonMCP_Remote_Script/handlers/devices.py:2745-2791` -- `get_mix_state` RS response structure
- `MCP_Server/mixing/house.py` -- recipe dict structure (device_class -> param_name -> natural_value)

### Secondary (MEDIUM confidence)
- `MCP_Server/tools/mixing.py` -- `format_error` usage, `get_recipe` error handling pattern
- `tests/test_analysis.py` -- test patterns (mock MCP, mock connection, JSON assertions)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all dependencies are existing project modules, no new external deps
- Architecture: HIGH -- follows exact same pattern as analysis.py, all referenced code inspected
- Pitfalls: HIGH -- derived from direct code inspection of conversion formulas, RS response format, and recipe structure

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- no external API changes expected)
