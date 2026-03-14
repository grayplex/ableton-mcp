# Phase 4: Mixing Controls - Research

**Researched:** 2026-03-14
**Domain:** Ableton Live Python API mixer surface control via Remote Script + MCP bridge
**Confidence:** HIGH

## Summary

Phase 4 implements the complete mixer surface for the Ableton MCP bridge: volume, pan, mute, solo, arm, send levels, and master/return channel control. The existing codebase already reads volume and panning via `track.mixer_device.volume.value` and `track.mixer_device.panning.value` in both `get_track_info` and `get_session_info`. This phase adds the write side (setting these values) plus mute/solo/arm toggles and send level control.

The architecture is well-established from Phases 1-3: `@command('name', write=True)` decorator on the Remote Script handler side, `@mcp.tool()` on the MCP Server tool side, and `send_command()` bridging them. The `_resolve_track()` helper and `track_type` parameter pattern from Phase 3 directly reuse for all mixer operations. The `MixerHandlers` stub class and `tools/mixer.py` stub file are already in place -- they just need populating.

The key technical decisions are: (1) all mixer setters use `write=True` since they modify Ableton state, (2) volume/pan/sends use the Ableton `DeviceParameter.value` property which accepts 0.0-1.0 normalized values, (3) mute/solo/arm are direct boolean properties on the Track object, (4) sends are accessed via `track.mixer_device.sends` which is an indexed list parallel to `song.return_tracks`, and (5) dB approximation uses the standard `20 * log10(value)` formula with a floor at negative infinity for value=0.

**Primary recommendation:** Populate the existing `MixerHandlers` mixin in `handlers/mixer.py` and `tools/mixer.py` following the exact `_set_track_color` / `_set_track_name` pattern from Phase 3. Reuse `_resolve_track()` for all operations. Add new mixer commands to `_WRITE_COMMANDS` in `connection.py`. Add `MCP_Server.tools.mixer` to the import chain in `tools/__init__.py` and to conftest patch targets.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Volume representation: Input 0.0-1.0 normalized only (no dB input). Pan: -1.0 (full left) to 1.0 (full right), 0 = center. Send levels: same 0.0-1.0 normalized range as volume. Validation: error on out-of-range values (no clamping) -- error includes current value for AI self-correction. Response includes dB approximation alongside normalized value (for volume AND sends). dB also added to get_track_info and get_all_tracks responses (Phase 3 enhancement).
- Mute/solo/arm style: Explicit set only -- no toggle (set_track_mute, set_track_solo, set_track_arm as booleans). Separate tools per operation -- not combined. Solo supports optional 'exclusive' parameter (unsolos all other tracks when soloing). Arm errors with explanation on tracks that can't be armed (e.g., group tracks). Mute and solo work on return tracks too (not just regular tracks). Master track excluded from mute/solo (consistent with Phase 3).
- Send level addressing: Sends identified by return track index (not name, not send slot index). Send levels use 0.0-1.0 normalized, same as volume. Send responses include dB approximation.
- Response content: Echo actual stored value from Ableton (not the requested value) -- accounts for internal quantization. Master track responses: same structure as regular tracks, but no track_index field. Mute/solo/arm responses: just the changed state (no mini mixer snapshot). Error responses include current value alongside valid range.
- Tool surface design: Unified tools with track_type parameter -- set_track_volume, set_track_pan, etc. all accept track_type='track'/'return'/'master'. Matches Phase 3 pattern (set_track_name, set_track_color use track_type). No dedicated set_master_volume / set_return_volume tools.

### Claude's Discretion
- dB conversion formula (standard 20*log10 vs Ableton-matched curve)
- Whether sends are read via expanded get_track_info or a separate get_send_levels tool
- Send response: whether to include return track name for confirmation
- Send target scope: returns-only or also master
- Pan label in responses (e.g., "center", "50% left")
- Track name inclusion in every mixer response

### Deferred Ideas (OUT OF SCOPE)
- Crossfader control (A/B assignment per track) -- niche, potential future phase
- Input monitoring modes (In/Auto/Off) -- Phase 10 (Routing) or separate
- Cue/preview volume for headphone monitoring -- potential future phase

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MIX-01 | User can set track volume (0.0-1.0 normalized) | `track.mixer_device.volume.value = val` -- DeviceParameter accepts 0.0-1.0, already read in get_track_info |
| MIX-02 | User can set track pan (-1.0 to 1.0) | `track.mixer_device.panning.value = val` -- DeviceParameter, already read in get_track_info |
| MIX-03 | User can mute/unmute any track | `track.mute = bool` -- direct boolean property, not on master track |
| MIX-04 | User can solo/unsolo any track | `track.solo = bool` -- direct boolean property, bypasses exclusive solo logic by default |
| MIX-05 | User can arm/disarm any track for recording | `track.arm = bool` -- requires `track.can_be_armed` guard, not on return/master |
| MIX-06 | User can set send levels for any track to any return | `track.mixer_device.sends[return_index].value = val` -- sends list parallels return_tracks |
| MIX-07 | User can set master track volume | Same as MIX-01 with `track_type='master'` -- `song.master_track.mixer_device.volume.value` |
| MIX-08 | User can set return track volume and pan | Same as MIX-01/MIX-02 with `track_type='return'` -- `song.return_tracks[i].mixer_device.volume/panning` |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Ableton Live Python API (Track, MixerDevice, DeviceParameter) | Live 12 / Python 3.11 | Mixer property read/write | Only API for Remote Script mixer control |
| FastMCP | >=1.3.0 | MCP tool definitions | Already established in project (Phase 1-2) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math (stdlib) | Python 3.11 | `math.log10` for dB conversion | dB approximation in responses |
| pytest + pytest-asyncio | >=8.3 / >=0.25 | Domain smoke tests | Testing tool registration and mocked responses |
| ruff | >=0.15.6 | Linting | Pre-commit quality gate |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Standard 20*log10 formula | Ableton-matched piecewise curve | Piecewise curve is more accurate below -18dB but complex and undocumented; standard formula is good enough for AI info display |
| Sends in get_track_info | Separate get_send_levels tool | Expanding get_track_info is simpler and reduces API calls for the AI |

**Installation:**
No new packages needed. `math` is stdlib. All dependencies already installed from Phase 1-2.

## Architecture Patterns

### Recommended Project Structure
```
AbletonMCP_Remote_Script/
  handlers/
    mixer.py         # Populate MixerHandlers mixin (6 command handlers)
    tracks.py         # Enhance _get_track_info to include dB + sends

MCP_Server/
  tools/
    mixer.py          # Populate mixer MCP tools (6 tools)
    __init__.py       # Add mixer import
  connection.py       # Add mixer commands to _WRITE_COMMANDS

tests/
  conftest.py         # Add mixer patch target
  test_mixer.py       # New: mixer domain smoke tests
```

### Pattern 1: Mixer Handler (Remote Script side)
**What:** Each mixer setter follows the _set_track_color / _set_track_name pattern exactly.
**When to use:** Every mixer write operation.
**Example:**
```python
# Source: Established pattern from handlers/tracks.py _set_track_color
from AbletonMCP_Remote_Script.registry import command
from AbletonMCP_Remote_Script.handlers.tracks import _resolve_track

@command("set_track_volume", write=True)
def _set_track_volume(self, params):
    """Set volume of a track (0.0-1.0 normalized)."""
    track_index = params.get("track_index", 0)
    volume = params.get("volume")
    track_type = params.get("track_type", "track")
    try:
        track = _resolve_track(self._song, track_type, track_index)
        # Validate range
        if volume < 0.0 or volume > 1.0:
            current = track.mixer_device.volume.value
            raise ValueError(
                f"Volume {volume} out of range (0.0-1.0). "
                f"Current value: {current}"
            )
        track.mixer_device.volume.value = volume
        # Echo actual stored value
        actual = track.mixer_device.volume.value
        result = {
            "volume": actual,
            "volume_db": _to_db(actual),
            "name": track.name,
            "type": track_type,
        }
        if track_type != "master":
            result["index"] = track_index
        return result
    except Exception as e:
        self.log_message(f"Error setting track volume: {e}")
        raise
```

### Pattern 2: MCP Tool (Server side)
**What:** Each MCP tool wraps send_command with format_error fallback.
**When to use:** Every tool in tools/mixer.py.
**Example:**
```python
# Source: Established pattern from tools/tracks.py set_track_color
import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp

@mcp.tool()
def set_track_volume(
    ctx: Context, track_index: int, volume: float, track_type: str = "track"
) -> str:
    """Set the volume of a track.

    Parameters:
    - track_index: Index of the track
    - volume: Volume level from 0.0 (silence) to 1.0 (max). Response includes dB approximation.
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_volume",
            {"track_index": track_index, "volume": volume, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set track volume",
            detail=str(e),
            suggestion="Volume must be 0.0-1.0. Check track_index with get_all_tracks.",
        )
```

### Pattern 3: dB Conversion Helper
**What:** Simple helper function for normalized volume to dB approximation.
**When to use:** All volume and send responses.
**Example:**
```python
import math

def _to_db(value: float) -> str:
    """Convert normalized 0.0-1.0 value to dB approximation string.

    Uses standard formula: dB = 20 * log10(value).
    Returns "-inf dB" for value 0, rounded to 1 decimal otherwise.

    Note: This is an approximation. Ableton's internal fader curve
    is slightly different (piecewise logarithmic) but the standard
    formula is accurate within ~1dB for most of the range.
    """
    if value <= 0.0:
        return "-inf dB"
    db = 20.0 * math.log10(value)
    return f"{db:.1f} dB"
```

### Pattern 4: Exclusive Solo
**What:** When `exclusive=True`, unsolo all other tracks before soloing the target.
**When to use:** set_track_solo with exclusive parameter.
**Example:**
```python
@command("set_track_solo", write=True)
def _set_track_solo(self, params):
    track_index = params.get("track_index", 0)
    solo = params.get("solo", False)
    track_type = params.get("track_type", "track")
    exclusive = params.get("exclusive", False)
    try:
        track = _resolve_track(self._song, track_type, track_index)
        if track_type == "master":
            raise ValueError("Master track cannot be soloed")
        if exclusive and solo:
            # Unsolo all regular tracks
            for t in self._song.tracks:
                if t.solo:
                    t.solo = False
            # Unsolo all return tracks
            for t in self._song.return_tracks:
                if t.solo:
                    t.solo = False
        track.solo = solo
        result = {"solo": track.solo, "name": track.name, "type": track_type}
        if track_type != "master":
            result["index"] = track_index
        return result
    except Exception as e:
        self.log_message(f"Error setting track solo: {e}")
        raise
```

### Pattern 5: Send Level by Return Track Index
**What:** Access sends via mixer_device.sends[return_index].
**When to use:** set_send_level handler.
**Example:**
```python
@command("set_send_level", write=True)
def _set_send_level(self, params):
    track_index = params.get("track_index", 0)
    track_type = params.get("track_type", "track")
    return_index = params.get("return_index", 0)
    level = params.get("level")
    try:
        track = _resolve_track(self._song, track_type, track_index)
        sends = track.mixer_device.sends
        if return_index < 0 or return_index >= len(sends):
            raise IndexError(
                f"Return index {return_index} out of range "
                f"(0-{len(sends) - 1}). "
                f"This session has {len(self._song.return_tracks)} return tracks."
            )
        if level < 0.0 or level > 1.0:
            current = sends[return_index].value
            raise ValueError(
                f"Send level {level} out of range (0.0-1.0). "
                f"Current value: {current}"
            )
        sends[return_index].value = level
        actual = sends[return_index].value
        # Include return track name for confirmation
        return_name = self._song.return_tracks[return_index].name
        result = {
            "send_level": actual,
            "send_db": _to_db(actual),
            "return_index": return_index,
            "return_name": return_name,
            "name": track.name,
            "type": track_type,
        }
        if track_type != "master":
            result["index"] = track_index
        return result
    except Exception as e:
        self.log_message(f"Error setting send level: {e}")
        raise
```

### Anti-Patterns to Avoid
- **Toggle instead of explicit set:** Never use `track.mute = not track.mute`. The user decided on explicit boolean set (set_track_mute with `mute: bool`). Toggles cause race conditions with concurrent calls.
- **Clamping out-of-range values:** Never silently clamp. The user decided on error-with-current-value so the AI can self-correct.
- **Returning requested value instead of actual:** Always read back `track.mixer_device.volume.value` after setting. Ableton may quantize internally.
- **Forgetting write=True:** All mixer setters modify Ableton state and must use `@command("name", write=True)` to run on Ableton's main thread.
- **Not guarding master track for mute/solo:** Master track does not have mute or solo properties. Always check `track_type != "master"` or catch AttributeError.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Track resolution by type/index | Custom lookup logic | `_resolve_track(song, track_type, track_index)` from tracks.py | Already handles all edge cases, validated in Phase 3 |
| dB display-accurate conversion | Piecewise curve matching Ableton's fader exactly | `20 * log10(value)` standard formula | Ableton's curve is undocumented; standard formula is within ~1dB for display purposes |
| Exclusive solo logic | Custom solo management system | Simple loop unsolo + set solo | Ableton handles the audio routing; we just set booleans |
| Error formatting | Custom error strings | `format_error(title, detail, suggestion)` from connection.py | Consistent AI-friendly format established in Phase 1 |

**Key insight:** The mixer domain is purely property read/write on well-defined Ableton API objects. There are no complex operations -- just validate inputs, set properties, read back actual values, and format responses.

## Common Pitfalls

### Pitfall 1: Master Track Has No mute/solo Properties
**What goes wrong:** `track.mute = True` raises AttributeError on master track.
**Why it happens:** Ableton's LOM explicitly excludes mute and solo from the master track (documented as "[not in master track]").
**How to avoid:** Check `track_type == "master"` and raise a descriptive ValueError before attempting to set mute/solo. The existing `get_track_info` handler already uses `if track_type != "master"` guard for this.
**Warning signs:** Test passes on regular tracks but crashes on `track_type="master"`.

### Pitfall 2: Return/Master Tracks Cannot Be Armed
**What goes wrong:** `track.arm = True` raises error on return and master tracks.
**Why it happens:** Ableton's `can_be_armed` returns `False` for return and master tracks. Group tracks also cannot be armed.
**How to avoid:** Always check `hasattr(track, 'can_be_armed') and track.can_be_armed` before setting arm. The user decided: "Arm errors with explanation on tracks that can't be armed."
**Warning signs:** Code works on MIDI/audio tracks but fails on returns/groups.

### Pitfall 3: Sends List Length Depends on Return Track Count
**What goes wrong:** `mixer_device.sends[return_index]` raises IndexError if return_index >= number of return tracks.
**Why it happens:** The sends list on mixer_device has exactly one entry per return track. If there are 2 return tracks, sends has indices 0 and 1. Creating/deleting return tracks changes the sends list length.
**How to avoid:** Validate `return_index < len(track.mixer_device.sends)` and provide a helpful error including the number of return tracks.
**Warning signs:** Tests pass with 2 return tracks but fail with 0 or 1.

### Pitfall 4: Panning Value Range Is -1.0 to 1.0 (Not 0.0 to 1.0)
**What goes wrong:** Setting pan to 0.8 expecting "80% right" but the DeviceParameter may use a different range internally.
**Why it happens:** Ableton's panning DeviceParameter uses -1.0 (full left) to 1.0 (full right), with 0 as center. This is different from volume which uses 0.0 to 1.0.
**How to avoid:** Validate pan is within -1.0 to 1.0 range. Document clearly in tool description.
**Warning signs:** Pan values work for center (0) but produce unexpected results for extremes.

### Pitfall 5: _WRITE_COMMANDS in connection.py Must Be Updated
**What goes wrong:** Mixer commands get the 10-second read timeout instead of 15-second write timeout.
**Why it happens:** `_WRITE_COMMANDS` in `connection.py` is a hardcoded frozenset used for timeout selection. New write commands must be added to it.
**How to avoid:** Add all 6 mixer commands to `_WRITE_COMMANDS`: set_track_volume, set_track_pan, set_track_mute, set_track_solo, set_track_arm, set_send_level.
**Warning signs:** Commands work but occasionally timeout under load.

### Pitfall 6: tools/__init__.py Import and conftest.py Patch Target
**What goes wrong:** Mixer tools not registered, or tests don't mock the connection properly.
**Why it happens:** `MCP_Server/tools/__init__.py` currently has `mixer` commented out. `conftest.py` patch targets list does not include `MCP_Server.tools.mixer.get_ableton_connection`.
**How to avoid:** Uncomment/add mixer import in `tools/__init__.py` and add the patch target to `_GAC_PATCH_TARGETS` in `conftest.py`.
**Warning signs:** `test_mixer_tools_registered` fails; mocked tests hit real connection.

## Code Examples

Verified patterns from existing codebase:

### Reading Volume/Pan (Already Implemented)
```python
# Source: AbletonMCP_Remote_Script/handlers/tracks.py:487-488
"volume": track.mixer_device.volume.value,
"panning": track.mixer_device.panning.value,
```

### Setting a DeviceParameter Value
```python
# Source: Ableton Live LOM documentation (cycling74.com/max8/vignettes/live_object_model)
# DeviceParameter.value is read/write for volume, panning, sends
track.mixer_device.volume.value = 0.75  # Set normalized volume
track.mixer_device.panning.value = -0.5  # Set pan 50% left
```

### Track Boolean Properties (mute, solo, arm)
```python
# Source: Ableton Live LOM documentation
track.mute = True   # Mute the track (boolean, get/set)
track.solo = True   # Solo the track (boolean, get/set, bypasses exclusive)
track.arm = True    # Arm for recording (boolean, requires can_be_armed)
```

### Accessing Sends
```python
# Source: Ableton Live LOM - mixer_device.sends is list of DeviceParameter
sends = track.mixer_device.sends  # List parallel to song.return_tracks
sends[0].value = 0.5  # Set send level to first return track
actual = sends[0].value  # Read back actual stored value
```

### _resolve_track Pattern (Already Implemented)
```python
# Source: AbletonMCP_Remote_Script/handlers/tracks.py:137-167
track = _resolve_track(self._song, track_type, track_index)
# Returns: song.master_track, song.return_tracks[i], or song.tracks[i]
```

### Track Type Guard for Master (Already Implemented)
```python
# Source: AbletonMCP_Remote_Script/handlers/tracks.py:491-493
if track_type != "master":
    result["mute"] = track.mute
    result["solo"] = track.solo
```

### Can Be Armed Guard (Already Implemented)
```python
# Source: AbletonMCP_Remote_Script/handlers/tracks.py:501-502
if hasattr(track, "can_be_armed") and track.can_be_armed:
    result["arm"] = track.arm
```

### MCP Tool Pattern (Already Implemented)
```python
# Source: MCP_Server/tools/tracks.py:181-201 (set_track_color)
@mcp.tool()
def set_track_color(ctx: Context, track_index: int, color: str, track_type: str = "track") -> str:
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_color",
            {"track_index": track_index, "color": color, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(...)
```

## Discretion Recommendations

Based on research, here are recommendations for Claude's discretion areas:

### dB Conversion Formula: Use Standard 20*log10
**Recommendation:** Standard formula `20 * log10(value)`.
**Rationale:** Ableton's piecewise curve is undocumented and would require reverse-engineering. The standard formula is within ~1dB for the practical range (values 0.1-1.0). At very low levels (<0.1) it diverges more, but this is informational display only -- the normalized value is the source of truth. An AI needs approximate dB context, not exact fader-position accuracy.

### Sends in get_track_info: Expand Existing Handler
**Recommendation:** Add sends to `_get_track_info` response (not a separate tool).
**Rationale:** Reduces API calls for the AI. When the AI inspects a track, it naturally wants to see send levels alongside volume/pan. The sends data is small (one entry per return track). Include send data only when return tracks exist to avoid empty arrays.

### Send Response: Include Return Track Name
**Recommendation:** Include `return_name` in set_send_level response.
**Rationale:** Confirmation that the send went to the right destination. The AI often needs to correlate return indices with names (e.g., "Reverb" vs "Delay"). Minimal cost -- just one extra property access.

### Send Target Scope: Returns Only
**Recommendation:** Sends only target return tracks (not master).
**Rationale:** In Ableton's LOM, `mixer_device.sends` maps 1:1 to `return_tracks`. There is no send to master -- master receives the mix bus output directly. This is not a limitation of the tool but a reflection of how Ableton's mixer works.

### Pan Label: Include Human-Readable Label
**Recommendation:** Include a `pan_label` like "center", "50% left", "100% right" in responses.
**Rationale:** Makes responses immediately understandable. The AI can relay "Pan: 50% left" rather than "Pan: -0.5" to users. Easy to compute from the value.

### Track Name: Include in Every Mixer Response
**Recommendation:** Include `name` in every mixer response.
**Rationale:** Phase 3 pattern already includes `name` in set_track_color and set_track_name responses. Consistency. The AI confirming "Set volume on 'Bass' to 0.75" is more useful than "Set volume on track 0 to 0.75".

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python 2 Remote Scripts | Python 3.11 Remote Scripts | Ableton Live 11 / Live 12 | All handlers use Python 3 syntax |
| Direct property access on socket thread | `@command(write=True)` main-thread scheduling | Phase 1-2 of this project | Write operations are thread-safe |
| Single monolithic handler file | Mixin class pattern with domain modules | Phase 2 of this project | MixerHandlers is a clean mixin |

**Deprecated/outdated:**
- Python 2 Remote Script API: Removed in Phase 1. Live 12 uses Python 3.11.
- If/elif command dispatch: Replaced by dict-based registry in Phase 1.

## Open Questions

1. **Exact Ableton panning DeviceParameter range**
   - What we know: LOM docs say panning is a DeviceParameter. The existing code reads `track.mixer_device.panning.value` and it appears to work. Forum posts confirm -1.0 to 1.0 range.
   - What's unclear: Whether Ableton's internal DeviceParameter for panning truly uses -1.0 to 1.0 or 0.0 to 1.0 mapped to full-left to full-right. The existing get_track_info already reads it.
   - Recommendation: Test empirically by reading a track with pan set fully left in Ableton UI and checking the value. If it returns 0.0 for full-left, the range is 0.0-1.0 (not -1.0 to 1.0) and validation needs adjustment. LOW confidence on exact range -- needs empirical verification during implementation.

2. **Master track sends list**
   - What we know: Regular and return tracks have mixer_device.sends. The sends list length matches return_tracks count.
   - What's unclear: Whether master track's mixer_device has a sends property. If it does, it likely has zero entries (master doesn't send to returns).
   - Recommendation: Guard with `hasattr(track.mixer_device, 'sends')` or catch the exception. For set_send_level, simply don't allow track_type="master" since master doesn't send to returns.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ / pytest-asyncio 0.25+ |
| Config file | pytest.ini or pyproject.toml (existing) |
| Quick run command | `python -m pytest tests/test_mixer.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MIX-01 | set_track_volume sends correct wire command | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_volume -x` | Wave 0 |
| MIX-02 | set_track_pan sends correct wire command | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_pan -x` | Wave 0 |
| MIX-03 | set_track_mute sends correct wire command | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_mute -x` | Wave 0 |
| MIX-04 | set_track_solo sends correct wire command | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_solo -x` | Wave 0 |
| MIX-05 | set_track_arm sends correct wire command | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_arm -x` | Wave 0 |
| MIX-06 | set_send_level sends correct wire command | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_send_level -x` | Wave 0 |
| MIX-07 | set_track_volume with track_type=master | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_volume_master -x` | Wave 0 |
| MIX-08 | set_track_volume/pan with track_type=return | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_volume_return -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_mixer.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_mixer.py` -- covers MIX-01 through MIX-08 (new file)
- [ ] `tests/conftest.py` -- add `MCP_Server.tools.mixer.get_ableton_connection` to `_GAC_PATCH_TARGETS`

## Integration Checklist

Files that need modification (summary for planner):

| File | Change | Why |
|------|--------|-----|
| `AbletonMCP_Remote_Script/handlers/mixer.py` | Populate MixerHandlers with 6 command handlers | Core mixer logic |
| `MCP_Server/tools/mixer.py` | Populate with 6 MCP tools | Tool definitions |
| `MCP_Server/tools/__init__.py` | Uncomment/add `mixer` import | Tool registration |
| `MCP_Server/connection.py` | Add 6 commands to `_WRITE_COMMANDS` | Proper timeout |
| `tests/conftest.py` | Add mixer patch target | Test isolation |
| `tests/test_mixer.py` | New file: smoke tests | Validation |
| `AbletonMCP_Remote_Script/handlers/tracks.py` | Enhance `_get_track_info` with dB + sends | Phase 3 enhancement per user decision |

## Sources

### Primary (HIGH confidence)
- Existing codebase: `handlers/tracks.py`, `tools/tracks.py`, `registry.py`, `connection.py` -- patterns fully verified by reading source
- [Cycling74 LOM documentation](https://docs.cycling74.com/max8/vignettes/live_object_model) -- Track.mute, Track.solo, Track.arm, Track.can_be_armed properties confirmed
- [Ableton Reference Manual - Mixing](https://www.ableton.com/en/manual/mixing/) -- solo/mute/return track behavior confirmed

### Secondary (MEDIUM confidence)
- [Structure Void Live API Documentation](https://structure-void.com/PythonLiveAPI_documentation/Live10.0.1.xml) -- MixerDevice.sends, DeviceParameter.value
- [AbletonLive-API-Stub](https://github.com/cylab/AbletonLive-API-Stub/blob/master/Live.xml) -- Track, MixerDevice class structure

### Tertiary (LOW confidence)
- [Cycling74 Forum - Volume Fader Curve](https://cycling74.com/forums/getting-curve-of-abletons-track-volume-slider) -- dB conversion complexity, confirms piecewise curve
- Panning range: -1.0 to 1.0 reported in forums but needs empirical verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- existing codebase patterns are fully documented and verified
- Architecture: HIGH -- follows exact Phase 3 patterns, no new patterns needed
- Pitfalls: HIGH -- master track guards and can_be_armed checks already implemented in get_track_info
- Ableton API properties: MEDIUM -- LOM docs confirm mute/solo/arm/volume/panning/sends exist as read/write, but exact panning range needs verification
- dB conversion: MEDIUM -- standard formula is well-known, Ableton's fader curve is different but undocumented; standard is good enough for display

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable -- Ableton API changes only with major versions)
