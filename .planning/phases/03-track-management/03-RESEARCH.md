# Phase 3: Track Management - Research

**Researched:** 2026-03-14
**Domain:** Ableton Live Python API track management via Remote Script + MCP bridge
**Confidence:** HIGH

## Summary

Phase 3 extends the existing track handler mixin (`TrackHandlers` in `AbletonMCP_Remote_Script/handlers/tracks.py`) and track tools module (`MCP_Server/tools/tracks.py`) with full CRUD operations for all track types (MIDI, audio, return, group), plus color management, group fold control, and comprehensive track info. The Ableton Live Python API (`Song` class) provides all needed methods: `create_midi_track(index)`, `create_audio_track(index)`, `create_return_track()`, `delete_track(index)`, `delete_return_track(index)`, `duplicate_track(index)`, plus `Track` properties `color_index` (0-69), `name`, `is_foldable`, `fold_state`, `is_grouped`, `group_track`.

The architecture is well-established from Phase 1-2: `@command` decorator on Remote Script side, `@mcp.tool()` on MCP Server side, `send_command()` bridge between them. The main complexity lies in: (1) the color name-to-index mapping (70 colors, user decision says friendly names only), (2) group track creation with track reindexing, and (3) making `get_track_info` work across regular tracks, return tracks, and master track with type-appropriate fields.

**Primary recommendation:** Extend the existing `TrackHandlers` mixin and `tools/tracks.py` following the exact patterns from Phase 1-2. Use a `COLOR_NAMES` dict in the Remote Script for name-to-index mapping, and address return/master tracks via a `track_type` parameter on `get_track_info`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Track color format: Friendly color names only -- no raw index exposure in the API. Full palette: name all ~70 Ableton colors including variants (light red, dark red, salmon, etc.). Invalid color name returns error with list of valid names -- AI can self-correct.
- Group track creation: Both modes -- empty group (default) and grouping existing tracks (optional track_indices parameter). Grouping moves tracks into the group. Response includes new group track index plus new indices of all grouped tracks. Add fold control: set_group_fold(track_index, folded: bool) and include fold state in get_track_info.
- Track info depth: get_track_info works on ALL track types: regular, return, and master (each returns type-appropriate fields). Routing info deferred to Phase 10. Send levels deferred to Phase 4. Current fields: name, type, mute, solo, arm, volume, pan, devices, clips, color -- add group fold state.
- Delete and duplicate scope: delete_track works on all deletable track types (regular + return). Master track is never deletable. delete_track returns info about what was deleted (name, type, index). duplicate_track accepts optional new_name parameter. If omitted, uses Ableton's default naming. duplicate_track returns new track's index, name, and type.

### Claude's Discretion
- Track addressing scheme: single tool with type parameter vs separate tools vs unified index space
- get_track_info read format for color (name only vs name + index)
- Response format consistency across all create_* tools
- Whether to add a lightweight get_all_tracks tool or rely on get_session_info

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TRCK-01 | User can create MIDI tracks at specified index | `song.create_midi_track(index)` -- already implemented, extend response format |
| TRCK-02 | User can create audio tracks at specified index | `song.create_audio_track(index)` -- same signature as MIDI, parallel implementation |
| TRCK-03 | User can create return tracks | `song.create_return_track()` -- no index param, always appends to end |
| TRCK-04 | User can create group tracks | No direct `song.create_group_track()` -- use `create_midi_track` then move tracks, or leverage undocumented approaches. See Group Track Complexity section |
| TRCK-05 | User can delete any track by index | `song.delete_track(index)` for regular tracks, `song.delete_return_track(index)` for returns |
| TRCK-06 | User can duplicate any track by index | `song.duplicate_track(index)` -- duplicate appears at index+1 |
| TRCK-07 | User can rename any track | `track.name = value` -- already implemented as set_track_name |
| TRCK-08 | User can set track color | `track.color_index = value` (0-69) -- wrap with friendly name lookup |
| TRCK-09 | User can get detailed info about any track | Extend existing `get_track_info` to cover return/master tracks, add color, type, fold state |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Ableton Live Python API (Song, Track) | Live 12 / Python 3.11 | Track CRUD operations | Only API available for Remote Script track management |
| FastMCP | >=1.3.0 | MCP tool definitions | Already established in project (Phase 1-2) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest + pytest-asyncio | >=8.3 / >=0.25 | Domain smoke tests | Testing tool registration and mocked responses |
| ruff | >=0.15.6 | Linting | Pre-commit quality gate |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Friendly color names | Raw color_index pass-through | User decision: names only, no raw indices |
| track_type parameter | Unified index space | Unified index would be simpler but less explicit for AI |

**Installation:**
No new packages needed. All dependencies already installed from Phase 1-2.

## Architecture Patterns

### Recommended Project Structure
```
AbletonMCP_Remote_Script/
  handlers/
    tracks.py          # Extend TrackHandlers mixin with new @command methods
MCP_Server/
  tools/
    tracks.py          # Extend with new @mcp.tool() definitions
  connection.py        # Add new write commands to _WRITE_COMMANDS set
tests/
  test_tracks.py       # Extend with smoke tests for new tools
```

### Pattern 1: Handler Mixin + @command Decorator (Remote Script Side)
**What:** Each handler method is a method on the `TrackHandlers` mixin class, decorated with `@command("wire_name", write=True)` for state-modifying operations.
**When to use:** Every new Remote Script handler.
**Example:**
```python
# Source: AbletonMCP_Remote_Script/handlers/tracks.py (existing pattern)
from AbletonMCP_Remote_Script.registry import command

class TrackHandlers:
    @command("create_audio_track", write=True)
    def _create_audio_track(self, params):
        index = params.get("index", -1)
        self._song.create_audio_track(index)
        new_track_index = len(self._song.tracks) - 1 if index == -1 else index
        new_track = self._song.tracks[new_track_index]
        return {
            "index": new_track_index,
            "name": new_track.name,
            "type": "audio",
        }
```

### Pattern 2: MCP Tool + send_command Bridge (Server Side)
**What:** Each MCP tool function calls `get_ableton_connection().send_command("wire_name", params)` and returns formatted result.
**When to use:** Every new MCP tool.
**Example:**
```python
# Source: MCP_Server/tools/tracks.py (existing pattern)
from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp

@mcp.tool()
def create_audio_track(ctx: Context, index: int = -1) -> str:
    """Create a new audio track in the Ableton session.

    Parameters:
    - index: Position to insert the track (-1 for end)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_audio_track", {"index": index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create audio track",
            detail=str(e),
            suggestion="Check track count with get_session_info",
        )
```

### Pattern 3: AI-Friendly Error Responses
**What:** Use `format_error(message, detail, suggestion)` consistently. For invalid color names, include the valid list in the error.
**When to use:** Every error path in MCP tools AND in Remote Script handlers where the error message matters.
**Example:**
```python
# Remote Script side -- color validation
valid_names = ", ".join(sorted(COLOR_NAMES.keys()))
raise ValueError(f"Unknown color '{color_name}'. Valid colors: {valid_names}")
```

### Pattern 4: Track Type Addressing (Discretion Decision)
**What:** Use a `track_type` parameter ("track", "return", "master") to address different track collections, with unified `track_index` within each collection.
**When to use:** For `get_track_info`, `delete_track`, and any operation that needs to work across track types.
**Why this approach:** The Ableton API separates tracks into three distinct collections (`song.tracks`, `song.return_tracks`, `song.master_track`). A unified index space would require mapping logic and be fragile. Explicit type parameter is clearer for AI consumption.
**Example:**
```python
@command("get_track_info")
def _get_track_info(self, params):
    track_type = params.get("track_type", "track")
    track_index = params.get("track_index", 0)

    if track_type == "master":
        track = self._song.master_track
    elif track_type == "return":
        track = self._song.return_tracks[track_index]
    else:
        track = self._song.tracks[track_index]
    # ... build response with type-appropriate fields
```

### Anti-Patterns to Avoid
- **Exposing raw color_index in API responses:** User decision says friendly names only. Always translate index to name before returning.
- **Forgetting to add commands to _WRITE_COMMANDS in connection.py:** All state-modifying commands need timeout classification. Without this, they get the 10s READ timeout instead of 15s WRITE timeout.
- **Returning stale indices after group operations:** Group track creation reindexes everything. Always return the new indices.
- **Using track.arm on return/master tracks:** Return and master tracks cannot be armed. Guard with `hasattr(track, 'arm')` or check track type.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color name mapping | Custom color name guessing/fuzzy matching | Static dict mapping 70 color names to indices 0-69 | Exact match is what the user wants; invalid names return the full list so AI can self-correct |
| Track type detection | Introspecting `has_audio_input`/`has_midi_input` | Check `track.has_midi_input` and `track.has_audio_input` directly, plus `track.is_foldable` for groups | Ableton API provides these booleans natively |
| Thread scheduling for write commands | Custom threading logic | Existing `_dispatch_write_command` via `schedule_message` queue pattern | Already handles main thread dispatch; just use `@command(write=True)` |
| Group track fold state | Custom UI toggle | `track.fold_state` property (1=folded, 0=unfolded) | Direct API property |

**Key insight:** The Ableton API already exposes nearly everything needed as simple properties and method calls. The complexity is in the mapping/translation layer (color names, track type addressing), not the underlying operations.

## Common Pitfalls

### Pitfall 1: Track Index Shift After Creation/Deletion
**What goes wrong:** Creating or deleting a track shifts the indices of all subsequent tracks. AI sends stale indices.
**Why it happens:** Ableton uses a positional list, not stable IDs. Insert at index 2 and everything at index 2+ shifts right.
**How to avoid:** Always return the new track's index in creation responses. For group track creation with existing tracks, return ALL new indices for the grouped tracks.
**Warning signs:** "Track index out of range" errors after creating/deleting tracks.

### Pitfall 2: Return Tracks vs Regular Tracks Indexing
**What goes wrong:** `song.tracks` and `song.return_tracks` are separate lists with separate index spaces. Passing a regular track index to `delete_return_track` deletes the wrong thing.
**Why it happens:** Ableton API has separate collections. `song.delete_track(index)` only works on regular tracks. Return tracks need `song.delete_return_track(index)`.
**How to avoid:** Use explicit `track_type` parameter to select the right collection. Never mix index spaces.
**Warning signs:** Wrong track gets deleted; "index out of range" on return tracks.

### Pitfall 3: Master Track Has No Index
**What goes wrong:** Trying to create, delete, or duplicate the master track, which is a singleton.
**Why it happens:** Master track is `song.master_track` (single object), not part of any indexed list.
**How to avoid:** Guard against delete/duplicate on master. `get_track_info` for master needs no index, just `track_type="master"`.
**Warning signs:** AttributeError when trying to index master track.

### Pitfall 4: Group Track Creation Has No Direct API
**What goes wrong:** Expecting a `song.create_group_track()` method to exist.
**Why it happens:** Ableton's Python API does not have a direct `create_group_track` method. Groups are created by selecting tracks and using the UI grouping action.
**How to avoid:** Two approaches: (1) Create an empty MIDI track and set `is_foldable` -- BUT `is_foldable` is read-only. (2) Use the `Application.View` to trigger grouping via `song.begin_undo_step()` and programmatic selection. See Group Track Complexity section below.
**Warning signs:** AttributeError on `create_group_track`.

### Pitfall 5: color_index vs color Property
**What goes wrong:** Using `track.color` (RGB integer) instead of `track.color_index` (0-69 palette index).
**Why it happens:** Both exist. `color` is an RGB integer, `color_index` is the palette position.
**How to avoid:** Use `color_index` exclusively since the user wants palette-based naming. Map names to indices 0-69.
**Warning signs:** Setting `track.color` to an index integer results in near-black colors.

### Pitfall 6: Not Registering New Write Commands in connection.py
**What goes wrong:** New write commands get the default READ timeout (10s) instead of WRITE timeout (15s).
**Why it happens:** `_WRITE_COMMANDS` frozenset in connection.py must be manually updated.
**How to avoid:** Add every new write command name to the `_WRITE_COMMANDS` frozenset.
**Warning signs:** Timeout errors on operations that should succeed.

## Group Track Complexity

**Critical finding:** The Ableton Live Python API does NOT have a `song.create_group_track()` method. Group tracks in Ableton are created by:

1. **Selecting tracks, then grouping them** -- This is the standard UI approach. In the Python API, this can be done via: select the tracks, then call an undocumented/internal approach, or
2. **Using `song.begin_undo_step()` with track manipulation** -- Some Remote Scripts use a combination of track selection and internal calls.

**Recommended approach for empty group:**
Create a regular track and rely on the fact that after adding child tracks to it, it becomes foldable. However, the simplest reliable approach is:
- Create a MIDI track at the desired position (this becomes the "group header")
- If `track_indices` are provided, move those tracks to be children of this group

**Alternative verified approach from AbletonOSC and similar projects:**
The most reliable method used in production Remote Scripts is to select the desired tracks programmatically and then trigger Live's native "Group Tracks" command. This involves:
```python
# Select tracks to group
for i, track_index in enumerate(track_indices):
    track = self._song.tracks[track_index]
    if i == 0:
        self._song.view.selected_track = track
    # Multi-select is tricky in the API
```

**Practical recommendation:** For the empty group case, we may need to create a single track that acts as a group header. For grouping existing tracks, we should research whether `self._song.view` selection + a grouping command is available. If not, document this as a limitation and implement only the empty group case, noting that the "group existing tracks" feature requires further investigation during implementation.

**Confidence:** LOW for group track creation implementation details. The exact mechanism needs validation against a running Ableton instance.

## Code Examples

Verified patterns from official sources and existing codebase:

### Creating an Audio Track (Remote Script)
```python
# Source: Existing create_midi_track pattern + Ableton API docs
@command("create_audio_track", write=True)
def _create_audio_track(self, params):
    """Create a new audio track at the specified index."""
    index = params.get("index", -1)
    self._song.create_audio_track(index)
    new_track_index = len(self._song.tracks) - 1 if index == -1 else index
    new_track = self._song.tracks[new_track_index]
    return {
        "index": new_track_index,
        "name": new_track.name,
        "type": "audio",
    }
```

### Creating a Return Track (Remote Script)
```python
# Source: Ableton API docs (ricardomatias.net/ableton-live)
@command("create_return_track", write=True)
def _create_return_track(self, params):
    """Create a new return track. Always appended to end."""
    self._song.create_return_track()
    new_index = len(self._song.return_tracks) - 1
    new_track = self._song.return_tracks[new_index]
    return {
        "index": new_index,
        "name": new_track.name,
        "type": "return",
    }
```

### Deleting a Track (Remote Script)
```python
# Source: Ableton API docs
@command("delete_track", write=True)
def _delete_track(self, params):
    """Delete a track by index. Supports regular and return tracks."""
    track_type = params.get("track_type", "track")
    track_index = params.get("track_index", 0)

    if track_type == "return":
        if track_index < 0 or track_index >= len(self._song.return_tracks):
            raise IndexError("Return track index out of range")
        track = self._song.return_tracks[track_index]
        info = {"name": track.name, "type": "return", "index": track_index}
        self._song.delete_return_track(track_index)
    elif track_type == "master":
        raise ValueError("Cannot delete the master track")
    else:
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        info = {"name": track.name, "type": "track", "index": track_index}
        self._song.delete_track(track_index)

    return {"deleted": info}
```

### Setting Track Color (Remote Script)
```python
# Source: Ableton API (track.color_index) + user decision (friendly names)
COLOR_NAMES = {
    "dark_red": 0, "red": 1, "orange": 2, "light_orange": 3,
    # ... full 70-color mapping
    "gray": 69,
}

# Reverse lookup for reading
COLOR_INDEX_TO_NAME = {v: k for k, v in COLOR_NAMES.items()}

@command("set_track_color", write=True)
def _set_track_color(self, params):
    """Set track color by friendly name."""
    track_index = params.get("track_index", 0)
    color_name = params.get("color", "")

    if color_name not in COLOR_NAMES:
        valid = ", ".join(sorted(COLOR_NAMES.keys()))
        raise ValueError(f"Unknown color '{color_name}'. Valid colors: {valid}")

    track = self._song.tracks[track_index]
    track.color_index = COLOR_NAMES[color_name]
    return {
        "index": track_index,
        "name": track.name,
        "color": color_name,
    }
```

### Duplicating a Track (Remote Script)
```python
# Source: Ableton API docs
@command("duplicate_track", write=True)
def _duplicate_track(self, params):
    """Duplicate a track. Optionally rename the copy."""
    track_index = params.get("track_index", 0)
    new_name = params.get("new_name", None)

    if track_index < 0 or track_index >= len(self._song.tracks):
        raise IndexError("Track index out of range")

    self._song.duplicate_track(track_index)

    # Duplicate appears at track_index + 1
    new_track = self._song.tracks[track_index + 1]
    if new_name:
        new_track.name = new_name

    return {
        "index": track_index + 1,
        "name": new_track.name,
        "type": "midi" if new_track.has_midi_input else "audio",
    }
```

### MCP Tool Pattern (Server Side)
```python
# Source: Existing tools/tracks.py pattern
@mcp.tool()
def delete_track(ctx: Context, track_index: int, track_type: str = "track") -> str:
    """Delete a track from the Ableton session.

    Parameters:
    - track_index: Index of the track to delete
    - track_type: Type of track - "track" (default) or "return". Master cannot be deleted.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "delete_track",
            {"track_index": track_index, "track_type": track_type},
        )
        deleted = result.get("deleted", {})
        return json.dumps({"deleted": deleted}, indent=2)
    except Exception as e:
        return format_error(
            "Failed to delete track",
            detail=str(e),
            suggestion="Verify track_index with get_session_info. Master track cannot be deleted.",
        )
```

## Ableton Live Track API Reference

### Song Methods (Confidence: HIGH)
| Method | Parameters | Notes |
|--------|-----------|-------|
| `song.create_midi_track(index)` | `index: int` (-1 for end, 0..len(tracks)) | Already implemented |
| `song.create_audio_track(index)` | `index: int` (-1 for end, 0..len(tracks)) | Same pattern as MIDI |
| `song.create_return_track()` | None | Always appends to end |
| `song.delete_track(index)` | `index: int` | Regular tracks only |
| `song.delete_return_track(index)` | `index: int` | Return tracks only |
| `song.duplicate_track(index)` | `index: int` | Copy appears at index+1 |

Source: [Ableton Live API - Song class](https://ricardomatias.net/ableton-live/classes/Song.html)

### Track Properties (Confidence: HIGH)
| Property | Type | Access | Notes |
|----------|------|--------|-------|
| `track.name` | str | R/W | Display name |
| `track.color` | int | R/W | RGB integer value |
| `track.color_index` | int | R/W | Palette index 0-69 |
| `track.mute` | bool | R/W | Mute state |
| `track.solo` | bool | R/W | Solo state |
| `track.arm` | bool | R/W | Arm for recording (not on return/master) |
| `track.is_foldable` | bool | R | True if track is a group |
| `track.is_grouped` | bool | R | True if track is inside a group |
| `track.fold_state` | int | R/W | 0=unfolded, 1=folded (only if is_foldable) |
| `track.group_track` | Track | R | Parent group track (if is_grouped) |
| `track.has_audio_input` | bool | R | True for audio tracks |
| `track.has_midi_input` | bool | R | True for MIDI tracks |
| `track.can_be_armed` | bool | R | Whether track supports arming |
| `track.mixer_device.volume.value` | float | R | Current volume |
| `track.mixer_device.panning.value` | float | R | Current pan |
| `track.devices` | list | R | Device chain |
| `track.clip_slots` | list | R | Clip slot list |

Source: [AbletonOSC track handler](https://github.com/ideoforms/AbletonOSC), verified against existing codebase patterns

### Track Collections (Confidence: HIGH)
| Collection | Access | Contains |
|------------|--------|----------|
| `song.tracks` | list | Regular tracks (MIDI, audio, group) |
| `song.return_tracks` | list | Return/aux tracks |
| `song.master_track` | single | Master track (singleton) |

### Color Palette (Confidence: HIGH)
- 70 colors total, indexed 0-69
- Arranged in a 14x5 grid in Ableton's UI (top-left = 0, reading left-to-right, top-to-bottom)
- Names are not official from Ableton -- they must be defined by us
- Reference: [AbletonAutoColor](https://github.com/CoryWBoris/AbletonAutoColor), [ableton-colors](https://github.com/danhemerlein/ableton-colors)

## Discretion Recommendations

### Track Addressing Scheme
**Recommendation:** Use a `track_type` parameter with values `"track"`, `"return"`, `"master"` alongside `track_index`. This mirrors the Ableton API's own structure (`song.tracks[i]`, `song.return_tracks[i]`, `song.master_track`) and is most explicit for AI consumers.

### Color Read Format
**Recommendation:** Return both `color` (name) and `color_index` (integer) in `get_track_info` responses. The name is for AI readability, the index is for debugging. This does not violate the "no raw index in the API" rule since the SET operations only accept names.

### Response Format Consistency
**Recommendation:** All `create_*` tools return JSON with `{ "index", "name", "type" }`. All mutation tools return JSON with the affected track's current state. This gives the AI enough context to continue without extra calls.

### get_all_tracks Tool
**Recommendation:** Add a lightweight `get_all_tracks` tool that returns a summary list (index, name, type, color) for all regular + return tracks. This avoids N+1 calls when AI needs an overview. It is lighter than `get_session_info` and avoids dumping full clip/device data.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python 2 Remote Scripts | Python 3.11 (Live 12) | Live 11 (2021) | Modern syntax, type hints |
| JSON completeness parsing | Length-prefix framing (Phase 1) | Phase 1 | Reliable message boundaries |
| if/elif dispatch | Dict-based registry (Phase 1) | Phase 1 | @command decorator auto-registration |

**Deprecated/outdated:**
- `track.color` (RGB integer): While still functional, `color_index` is the standard approach for palette-based coloring.
- Manual thread management for write commands: `@command(write=True)` handles this via the registry.

## Open Questions

1. **Group Track Creation Mechanism**
   - What we know: No `song.create_group_track()` method exists in the API. Groups are created via track selection + UI grouping command.
   - What's unclear: Whether there is a programmatic way to group tracks without UI interaction in the Remote Script context. Some approaches use `Application.View` or internal methods.
   - Recommendation: Implement empty group creation by creating a MIDI track (simplest). For grouping existing tracks, attempt using track selection + the internal grouping command. If that fails during implementation, document the limitation and offer only empty group creation. Flag for testing against live Ableton.
   - Confidence: LOW

2. **Exact Color Name Mapping**
   - What we know: 70 colors (0-69) in a 14x5 grid. Community projects have RGB values but not standardized names.
   - What's unclear: What exact names to use for all 70 colors, especially variants (is index 1 "red" or "bright_red"?).
   - Recommendation: Define our own color name mapping based on visual inspection of Ableton's palette. Use descriptive, unique names. Include reference to the indexed palette image from AbletonAutoColor.
   - Confidence: MEDIUM (names are our choice, but we need to match the visual palette accurately)

3. **duplicate_track on Return Tracks**
   - What we know: `song.duplicate_track(index)` exists. It's unclear if it works on return tracks.
   - What's unclear: Whether `duplicate_track` handles return tracks or only regular tracks.
   - Recommendation: Test during implementation. If it doesn't support return tracks, only enable duplication for regular tracks and document the limitation.
   - Confidence: MEDIUM

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3 + pytest-asyncio 0.25 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_tracks.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRCK-01 | Create MIDI track via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_create_midi_track_calls_send_command -x` | Exists |
| TRCK-02 | Create audio track via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_create_audio_track -x` | Wave 0 |
| TRCK-03 | Create return track via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_create_return_track -x` | Wave 0 |
| TRCK-04 | Create group track via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_create_group_track -x` | Wave 0 |
| TRCK-05 | Delete track via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_delete_track -x` | Wave 0 |
| TRCK-06 | Duplicate track via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_duplicate_track -x` | Wave 0 |
| TRCK-07 | Rename track via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_set_track_name -x` | Partial (exists as test_track_tools_registered) |
| TRCK-08 | Set track color via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_set_track_color -x` | Wave 0 |
| TRCK-09 | Get track info (all types) via MCP tool | smoke | `uv run pytest tests/test_tracks.py::test_get_track_info_returns_data -x` | Exists (needs extension) |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_tracks.py -x`
- **Per wave merge:** `uv run pytest tests/ -x && uv run ruff check .`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_tracks.py::test_create_audio_track` -- covers TRCK-02
- [ ] `tests/test_tracks.py::test_create_return_track` -- covers TRCK-03
- [ ] `tests/test_tracks.py::test_create_group_track` -- covers TRCK-04
- [ ] `tests/test_tracks.py::test_delete_track` -- covers TRCK-05
- [ ] `tests/test_tracks.py::test_duplicate_track` -- covers TRCK-06
- [ ] `tests/test_tracks.py::test_set_track_color` -- covers TRCK-08
- [ ] `tests/test_tracks.py::test_get_track_info_all_types` -- covers TRCK-09 for return/master
- [ ] Update `_GAC_PATCH_TARGETS` in `tests/conftest.py` if new tool modules are added (likely not needed since all tools stay in tools/tracks.py)

## Connection.py Updates Required

The `_WRITE_COMMANDS` frozenset in `MCP_Server/connection.py` must be updated with all new write commands:

```python
_WRITE_COMMANDS = frozenset([
    # ... existing ...
    "create_audio_track",
    "create_return_track",
    "create_group_track",
    "delete_track",
    "duplicate_track",
    "set_track_color",
    "set_group_fold",
    # create_midi_track and set_track_name already present
])
```

## Sources

### Primary (HIGH confidence)
- [Ableton Live API - Song class](https://ricardomatias.net/ableton-live/classes/Song.html) - method signatures for create/delete/duplicate track
- [AbletonOSC README](https://github.com/ideoforms/AbletonOSC/blob/master/README.md) - comprehensive track property list, verified API paths
- [AbletonOSC source](https://github.com/ideoforms/AbletonOSC/tree/master/abletonosc) - actual Python API call patterns
- Existing codebase (`handlers/tracks.py`, `tools/tracks.py`, `registry.py`, `connection.py`) - established patterns

### Secondary (MEDIUM confidence)
- [AbletonAutoColor](https://github.com/CoryWBoris/AbletonAutoColor) - color_index range 0-69, palette grid layout
- [ableton-colors](https://github.com/danhemerlein/ableton-colors) - color RGB values for palette
- [Ableton Live API XML docs](https://nsuspray.github.io/Live_API_Doc/) - API method listings

### Tertiary (LOW confidence)
- Group track creation via programmatic selection -- no authoritative source confirms this works reliably in Remote Script context
- Exact color names for all 70 indices -- community-defined, no official naming

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Same stack as Phase 1-2, no new dependencies
- Architecture: HIGH - Extending proven patterns (mixin + @command + @mcp.tool)
- Pitfalls: HIGH - Well-documented API limitations, verified across multiple sources
- Group track creation: LOW - No direct API method, needs implementation-time validation
- Color mapping: MEDIUM - Index range verified, names are our design choice

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable API, Ableton Live 12 mature)
