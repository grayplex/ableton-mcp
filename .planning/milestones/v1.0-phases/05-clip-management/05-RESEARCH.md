# Phase 5: Clip Management - Research

**Researched:** 2026-03-14
**Domain:** Ableton Live Python API -- Clip & ClipSlot objects, Session View clip lifecycle
**Confidence:** HIGH

## Summary

Phase 5 extends the existing `ClipHandlers` mixin and `tools/clips.py` MCP tools to cover the full clip lifecycle: create, delete, duplicate, rename, loop/region control, fire, stop, get info, and color. The existing codebase already has `create_clip`, `set_clip_name`, `fire_clip`, and `stop_clip` -- this phase adds `delete_clip`, `duplicate_clip`, `get_clip_info`, `set_clip_color`, and `set_clip_loop` handlers, then enhances existing handlers with richer responses. All work follows established mixin + `@command` decorator + MCP tool patterns from Phases 3 and 4.

The Ableton Live Python API provides all necessary primitives on the `Clip` and `ClipSlot` objects. `ClipSlot.delete_clip()` removes a clip, `ClipSlot.duplicate_clip_to(target_slot)` copies to an arbitrary slot, and `Clip` exposes `looping`, `loop_start`, `loop_end`, `start_marker`, `end_marker`, `color_index`, `is_playing`, `is_triggered`, `is_audio_clip`, `name`, and `length` as get/set properties. The phase is straightforward because it maps API surface directly to wire commands.

**Primary recommendation:** Extend `handlers/clips.py` with new handler methods following the exact pattern of Phase 4's mixer handlers (validation, `_resolve_clip_slot` helper, AI-friendly errors with current values). Extend `tools/clips.py` with matching MCP tool functions. Update `_WRITE_COMMANDS` in `connection.py` for new write commands. Add new get_clip_info as a read command.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Dedicated `get_clip_info` tool (not folded into get_track_info) -- returns full detail: name, length, color, loop_enabled, loop_start, loop_end, start_marker, end_marker, is_playing, is_triggered, is_audio_clip. No MIDI note data. Empty slots return `{has_clip: false, slot_index: N}`.
- `get_track_info` clip listing enhanced with `is_playing` flag (lightweight addition) -- already done in existing code.
- `set_clip_color` added -- uses same 70-color palette as Phase 3's set_track_color.
- Duplicate uses explicit target: `duplicate_clip(track_index, clip_index, target_track_index, target_clip_index)`. Error if target slot already occupied. Response includes new clip details.
- One combined `set_clip_loop` tool with all optional params: enabled, loop_start, loop_end, start_marker, end_marker. Validate relationships. Positions in beats (float). Response echoes ALL current loop/marker values.
- Regular tracks only -- no track_type parameter needed.
- create_clip keeps existing error-on-occupied-slot behavior (no overwrite option).
- delete_clip errors on empty slot.
- fire_clip returns `{fired: true, is_playing: true, clip_name: "..."}`.
- stop_clip returns `{stopped: true, clip_name: "..."}`.
- Error messages include current values for AI self-correction.

### Claude's Discretion
- Whether get_clip_info returns additional properties (e.g., signature_numerator, signature_denominator)
- Internal structure of set_clip_loop validation (order of checks)
- Whether delete_clip returns the deleted clip's name for confirmation

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLIP-01 | Create MIDI clips with specified length in any clip slot | Existing `create_clip` handler already works; enhance response to match new format |
| CLIP-02 | Delete clips from any clip slot | `ClipSlot.delete_clip()` API method; add handler + MCP tool |
| CLIP-03 | Duplicate clips to another slot | `ClipSlot.duplicate_clip_to(target_slot)` API method; add pre-check for occupied target |
| CLIP-04 | Rename clips | Existing `set_clip_name` handler; no changes needed |
| CLIP-05 | Set clip loop enabled/disabled | `Clip.looping` property (get/set boolean); part of combined set_clip_loop handler |
| CLIP-06 | Set clip loop start and end positions | `Clip.loop_start` and `Clip.loop_end` properties (float, beats); part of set_clip_loop |
| CLIP-07 | Set clip start and end markers | `Clip.start_marker` and `Clip.end_marker` properties (float, beats); part of set_clip_loop |
| CLIP-08 | Fire (launch) any clip | Existing `fire_clip` handler; enhance response with clip name and is_playing |
| CLIP-09 | Stop any clip | Existing `stop_clip` handler; enhance response with clip name |
</phase_requirements>

## Standard Stack

### Core (Ableton Live Python API Objects)

| Object | Property/Method | Purpose | Notes |
|--------|----------------|---------|-------|
| `ClipSlot` | `.has_clip` | Check if slot contains a clip | Boolean property |
| `ClipSlot` | `.clip` | Access the Clip object | Returns Clip or raises if empty |
| `ClipSlot` | `.create_clip(length)` | Create empty MIDI clip | Raises if slot non-empty or non-MIDI track |
| `ClipSlot` | `.delete_clip()` | Remove clip from slot | Raises if slot empty |
| `ClipSlot` | `.duplicate_clip_to(target_slot)` | Copy clip to target | Overrides target if non-empty; raises if source empty or track type mismatch |
| `ClipSlot` | `.fire()` | Launch clip (or trigger stop) | Fires clip if present, stops if no clip |
| `ClipSlot` | `.stop()` | Stop slot playback | Always available |
| `Clip` | `.name` | Get/set clip name | String, read/write |
| `Clip` | `.length` | Get clip length in beats | Read-only float |
| `Clip` | `.looping` | Get/set loop enabled | Boolean, read/write |
| `Clip` | `.loop_start` | Get/set loop start | Float in beats (MIDI/warped audio) |
| `Clip` | `.loop_end` | Get/set loop end | Float in beats |
| `Clip` | `.start_marker` | Get/set start marker | Float in beats |
| `Clip` | `.end_marker` | Get/set end marker | Float in beats |
| `Clip` | `.color_index` | Get/set color palette index | Same 0-69 palette as tracks |
| `Clip` | `.is_playing` | Check playback state | Read-only boolean |
| `Clip` | `.is_triggered` | Check triggered state | Read-only boolean |
| `Clip` | `.is_audio_clip` | Check if audio clip | Read-only boolean |
| `Clip` | `.is_midi_clip` | Check if MIDI clip | Read-only boolean |
| `Clip` | `.is_recording` | Check recording state | Read-only boolean |
| `Clip` | `.signature_numerator` | Time signature numerator | Read/write int |
| `Clip` | `.signature_denominator` | Time signature denominator | Read/write int |

### Supporting (Existing Project Infrastructure)

| Component | Location | Purpose |
|-----------|----------|---------|
| `@command` decorator | `registry.py` | Register handlers with `write=True` for state-modifying commands |
| `COLOR_NAMES` / `COLOR_INDEX_TO_NAME` | `handlers/tracks.py` | 70-color palette mapping; reuse for `set_clip_color` |
| `format_error()` | `connection.py` | AI-friendly error formatting |
| `_WRITE_COMMANDS` | `connection.py` | Timeout classification for new write commands |
| `get_ableton_connection().send_command()` | `connection.py` | MCP tool -> Remote Script communication |
| `json.dumps(result, indent=2)` | MCP tool pattern | Standard JSON response format |

## Architecture Patterns

### Recommended Implementation Structure

No new files needed. All changes go into existing files:

```
AbletonMCP_Remote_Script/
  handlers/
    clips.py           # Extend ClipHandlers mixin (add ~6 new methods, enhance 2)
    tracks.py           # (Already has is_playing in clip listings -- verified)
MCP_Server/
  tools/
    clips.py            # Extend with ~5 new MCP tool functions
  connection.py         # Add new commands to _WRITE_COMMANDS
tests/
  test_clips.py         # Extend with tests for new tools
  conftest.py           # Add any new patch target if needed (unlikely -- same module)
```

### Pattern 1: Clip Slot Resolution Helper

**What:** A `_resolve_clip_slot` helper to reduce boilerplate, analogous to `_resolve_track` in tracks.py.
**When to use:** Every handler that needs track_index + clip_index validation.

```python
def _resolve_clip_slot(song, track_index, clip_index):
    """Resolve a clip slot from track and clip indices.

    Returns:
        (clip_slot, track) tuple.

    Raises:
        IndexError: If track or clip index out of range.
    """
    if track_index < 0 or track_index >= len(song.tracks):
        raise IndexError(
            f"Track index {track_index} out of range "
            f"(0-{len(song.tracks) - 1})"
        )
    track = song.tracks[track_index]
    if clip_index < 0 or clip_index >= len(track.clip_slots):
        raise IndexError(
            f"Clip index {clip_index} out of range "
            f"(0-{len(track.clip_slots) - 1})"
        )
    return track.clip_slots[clip_index], track
```

### Pattern 2: Clip Info Collector

**What:** A `_clip_info_dict` helper that builds the standard clip info response.
**When to use:** In `get_clip_info`, `duplicate_clip`, and anywhere a clip response is needed.

```python
def _clip_info_dict(clip):
    """Build standard clip info dictionary."""
    return {
        "name": clip.name,
        "length": clip.length,
        "color": COLOR_INDEX_TO_NAME.get(clip.color_index, f"unknown_{clip.color_index}"),
        "color_index": clip.color_index,
        "loop_enabled": clip.looping,
        "loop_start": clip.loop_start,
        "loop_end": clip.loop_end,
        "start_marker": clip.start_marker,
        "end_marker": clip.end_marker,
        "is_playing": clip.is_playing,
        "is_triggered": clip.is_triggered,
        "is_audio_clip": clip.is_audio_clip,
    }
```

### Pattern 3: Combined Set With Optional Params (set_clip_loop)

**What:** A single handler that accepts multiple optional params and applies only those provided.
**When to use:** The `set_clip_loop` handler.

```python
@command("set_clip_loop", write=True)
def _set_clip_loop(self, params):
    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip

    # Apply enabled if provided
    if "enabled" in params:
        clip.looping = params["enabled"]

    # Apply loop_start if provided (validate before setting)
    if "loop_start" in params:
        # ... validation ...
        clip.loop_start = params["loop_start"]

    # ... similar for loop_end, start_marker, end_marker ...

    # Always echo all current values
    return {
        "loop_enabled": clip.looping,
        "loop_start": clip.loop_start,
        "loop_end": clip.loop_end,
        "start_marker": clip.start_marker,
        "end_marker": clip.end_marker,
    }
```

### Pattern 4: MCP Tool With JSON Response (Phase 4 Pattern)

**What:** MCP tools return `json.dumps(result, indent=2)` for structured data.
**When to use:** All new clip tools that return data (get_clip_info, duplicate_clip, set_clip_loop, set_clip_color).

```python
@mcp.tool()
def get_clip_info(ctx: Context, track_index: int, clip_index: int) -> str:
    """Get detailed information about a clip in the specified track and slot."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_clip_info", {"track_index": track_index, "clip_index": clip_index}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get clip info",
            detail=str(e),
            suggestion="Verify track and clip indices with get_track_info",
        )
```

### Anti-Patterns to Avoid

- **Don't use `Clip.fire()` -- use `ClipSlot.fire()`:** The existing code correctly uses `clip_slot.fire()` which handles both firing a clip and triggering stop. `Clip.fire()` has different semantics (restart/record).
- **Don't skip the occupied-slot check in duplicate_clip:** Even though `duplicate_clip_to` overrides the target, the user decision says to error on occupied target for safety.
- **Don't use `clip_slot.clip` without checking `has_clip` first:** Accessing `.clip` on an empty slot may raise or return None depending on context.
- **Don't set loop_start > loop_end or vice versa:** The API may accept invalid relationships but produce unexpected behavior. Validate before setting.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color name lookup | Custom color mapping for clips | Import `COLOR_NAMES` and `COLOR_INDEX_TO_NAME` from `handlers/tracks.py` | Clips use the exact same 70-color palette as tracks |
| Clip slot resolution | Repeated index validation in every handler | `_resolve_clip_slot()` helper function | Same pattern as `_resolve_track()` -- reduces boilerplate and ensures consistent errors |
| Error formatting | Custom error string building | `format_error(title, detail, suggestion)` from `connection.py` | Established pattern for AI-friendly errors |

## Common Pitfalls

### Pitfall 1: Loop Region Validation Order

**What goes wrong:** Setting `loop_start` to a value > current `loop_end` raises an error from Ableton, even if you intend to also raise `loop_end` in the same call.
**Why it happens:** Ableton validates the relationship at each individual property write.
**How to avoid:** When both `loop_start` and `loop_end` are provided, check the intended final state for validity. If widening the range, set `loop_end` first then `loop_start`. If narrowing, set `loop_start` first then `loop_end`. A safe approach: if new `loop_start` < current `loop_start`, set `loop_start` first; otherwise set `loop_end` first.
**Warning signs:** "loop_start must be before loop_end" errors when the final state would be valid.

### Pitfall 2: duplicate_clip_to Overrides Target Silently

**What goes wrong:** The API's `duplicate_clip_to` overwrites the target slot without warning, destroying the existing clip.
**Why it happens:** This is by design in the Ableton API.
**How to avoid:** User decision says to check `target_slot.has_clip` and error BEFORE calling `duplicate_clip_to`. This is a deliberate safety layer.
**Warning signs:** Lost clips after duplicate operations.

### Pitfall 3: Looping Property vs Loop Start/End Coupling

**What goes wrong:** When `looping` is False, `loop_start` == `start_marker` and `loop_end` == `end_marker` in Ableton's internal state. Setting `looping = True` may reveal that `loop_start`/`loop_end` don't match what was expected.
**Why it happens:** Ableton couples these values when looping is off.
**How to avoid:** When enabling looping AND setting loop points in the same call, enable looping first so that the explicit loop_start/loop_end values can be independently set.
**Warning signs:** Loop points snapping to unexpected positions after enabling looping.

### Pitfall 4: create_clip Only Works on MIDI Tracks

**What goes wrong:** Calling `clip_slot.create_clip(length)` on an audio track raises an exception.
**Why it happens:** Audio clips can only be created by recording or loading audio files. The API only supports creating empty MIDI clips.
**How to avoid:** The existing handler already documents this ("Create a new MIDI clip"). Error messages from the API are descriptive enough. No extra validation needed beyond what Ableton provides.
**Warning signs:** "Cannot create clip on non-MIDI track" errors.

### Pitfall 5: Clip Properties Read After Fire

**What goes wrong:** Reading `is_playing` immediately after `clip_slot.fire()` might return `False` because playback hasn't started yet (quantization delay).
**Why it happens:** `fire()` triggers playback according to the clip's launch quantization setting, which may not be immediate.
**How to avoid:** After `fire()`, report `is_playing` but note that `is_triggered` is the more reliable indicator that the fire command was accepted. The response should include both states.
**Warning signs:** `is_playing: false` even after a successful fire.

### Pitfall 6: stop_clip via ClipSlot.stop() Doesn't Need has_clip Check

**What goes wrong:** Adding an unnecessary `has_clip` check to stop_clip prevents stopping empty slots (which is valid -- it stops the track's slot).
**Why it happens:** Inconsistent with other handlers that require `has_clip`.
**How to avoid:** The existing code correctly calls `clip_slot.stop()` without checking `has_clip`. However, to return the clip name in the response (per user decision), we do need to check `has_clip` for the name, but should still allow the stop operation even on empty slots.
**Warning signs:** "No clip in slot" errors when trying to stop playback.

## Code Examples

### Example 1: delete_clip Handler

```python
# Source: follows existing _set_clip_name pattern
@command("delete_clip", write=True)
def _delete_clip(self, params):
    """Delete a clip from the specified slot."""
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)

    if not clip_slot.has_clip:
        raise Exception(
            f"No clip in slot {clip_index} on track '{track.name}' "
            f"(track {track_index})"
        )

    clip_name = clip_slot.clip.name
    clip_slot.delete_clip()

    return {"deleted": True, "clip_name": clip_name}
```

### Example 2: duplicate_clip Handler

```python
# Source: uses ClipSlot.duplicate_clip_to() API method
@command("duplicate_clip", write=True)
def _duplicate_clip(self, params):
    """Duplicate a clip to a target slot."""
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)
    target_track_index = params.get("target_track_index", 0)
    target_clip_index = params.get("target_clip_index", 0)

    source_slot, source_track = _resolve_clip_slot(
        self._song, track_index, clip_index
    )
    target_slot, target_track = _resolve_clip_slot(
        self._song, target_track_index, target_clip_index
    )

    if not source_slot.has_clip:
        raise Exception("No clip in source slot")

    if target_slot.has_clip:
        raise Exception(
            f"Target slot {target_clip_index} on track "
            f"'{target_track.name}' already has a clip "
            f"('{target_slot.clip.name}'). Delete it first."
        )

    source_slot.duplicate_clip_to(target_slot)

    new_clip = target_slot.clip
    return {
        "name": new_clip.name,
        "length": new_clip.length,
        "target_track_index": target_track_index,
        "target_clip_index": target_clip_index,
    }
```

### Example 3: set_clip_loop Handler (Validation Order)

```python
# Demonstrates safe ordering of loop property writes
@command("set_clip_loop", write=True)
def _set_clip_loop(self, params):
    """Set loop/region properties on a clip."""
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip

    # Apply enabled first (if provided) so loop points can diverge from markers
    if "enabled" in params:
        clip.looping = params["enabled"]

    # Validate and apply loop_start / loop_end with safe ordering
    new_start = params.get("loop_start")
    new_end = params.get("loop_end")

    if new_start is not None and new_end is not None:
        if new_end <= new_start:
            raise ValueError(
                f"loop_end ({new_end}) must be greater than loop_start ({new_start}). "
                f"Current values: loop_start={clip.loop_start}, loop_end={clip.loop_end}"
            )
        # Widen first, then narrow
        if new_end > clip.loop_end:
            clip.loop_end = new_end
            clip.loop_start = new_start
        else:
            clip.loop_start = new_start
            clip.loop_end = new_end
    elif new_start is not None:
        if new_start >= clip.loop_end:
            raise ValueError(
                f"loop_start ({new_start}) must be less than current loop_end ({clip.loop_end}). "
                f"Current values: loop_start={clip.loop_start}, loop_end={clip.loop_end}"
            )
        clip.loop_start = new_start
    elif new_end is not None:
        if new_end <= clip.loop_start:
            raise ValueError(
                f"loop_end ({new_end}) must be greater than current loop_start ({clip.loop_start}). "
                f"Current values: loop_start={clip.loop_start}, loop_end={clip.loop_end}"
            )
        clip.loop_end = new_end

    # Similar for start_marker / end_marker
    new_sm = params.get("start_marker")
    new_em = params.get("end_marker")
    if new_sm is not None and new_em is not None:
        if new_em <= new_sm:
            raise ValueError(
                f"end_marker ({new_em}) must be greater than start_marker ({new_sm}). "
                f"Current values: start_marker={clip.start_marker}, end_marker={clip.end_marker}"
            )
        if new_em > clip.end_marker:
            clip.end_marker = new_em
            clip.start_marker = new_sm
        else:
            clip.start_marker = new_sm
            clip.end_marker = new_em
    elif new_sm is not None:
        if new_sm >= clip.end_marker:
            raise ValueError(
                f"start_marker ({new_sm}) must be less than current end_marker ({clip.end_marker})"
            )
        clip.start_marker = new_sm
    elif new_em is not None:
        if new_em <= clip.start_marker:
            raise ValueError(
                f"end_marker ({new_em}) must be greater than current start_marker ({clip.start_marker})"
            )
        clip.end_marker = new_em

    # Echo ALL current values
    return {
        "loop_enabled": clip.looping,
        "loop_start": clip.loop_start,
        "loop_end": clip.loop_end,
        "start_marker": clip.start_marker,
        "end_marker": clip.end_marker,
    }
```

### Example 4: get_clip_info Handler (Read Command)

```python
# Note: no write=True -- this is a read command
@command("get_clip_info")
def _get_clip_info(self, params):
    """Get detailed info about a clip, or slot status if empty."""
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)

    if not clip_slot.has_clip:
        return {
            "has_clip": False,
            "slot_index": clip_index,
            "track_index": track_index,
            "track_name": track.name,
        }

    clip = clip_slot.clip
    return {
        "has_clip": True,
        "name": clip.name,
        "length": clip.length,
        "color": COLOR_INDEX_TO_NAME.get(clip.color_index, f"unknown_{clip.color_index}"),
        "color_index": clip.color_index,
        "loop_enabled": clip.looping,
        "loop_start": clip.loop_start,
        "loop_end": clip.loop_end,
        "start_marker": clip.start_marker,
        "end_marker": clip.end_marker,
        "is_playing": clip.is_playing,
        "is_triggered": clip.is_triggered,
        "is_audio_clip": clip.is_audio_clip,
    }
```

### Example 5: Enhanced fire_clip Response

```python
@command("fire_clip", write=True)
def _fire_clip(self, params):
    """Fire a clip."""
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)

    if not clip_slot.has_clip:
        raise Exception("No clip in slot")

    clip_name = clip_slot.clip.name
    clip_slot.fire()

    return {
        "fired": True,
        "is_playing": clip_slot.clip.is_playing,
        "clip_name": clip_name,
    }
```

## State of the Art

| Old Approach (Current Code) | New Approach (Phase 5) | Impact |
|-----------------------------|------------------------|--------|
| fire_clip returns `{fired: True}` | Returns `{fired: True, is_playing: True, clip_name: "..."}` | AI knows what clip was fired |
| stop_clip returns `{stopped: True}` | Returns `{stopped: True, clip_name: "..."}` | AI gets confirmation with clip identity |
| No delete/duplicate/loop/info/color handlers | Full clip lifecycle handlers | Complete clip management capability |
| MCP create_clip returns plain text | Returns JSON with clip details | Consistent structured responses |
| Inline index validation in every handler | `_resolve_clip_slot()` helper | DRY, consistent error messages |

## Integration Checklist

### Files to Modify

1. **`AbletonMCP_Remote_Script/handlers/clips.py`** -- Add: `_resolve_clip_slot` helper, `_clip_info_dict` helper, `_delete_clip`, `_duplicate_clip`, `_get_clip_info`, `_set_clip_color`, `_set_clip_loop` handlers. Enhance: `_fire_clip`, `_stop_clip` responses. Import `COLOR_NAMES`, `COLOR_INDEX_TO_NAME` from `handlers/tracks.py`.
2. **`MCP_Server/tools/clips.py`** -- Add: `get_clip_info`, `delete_clip`, `duplicate_clip`, `set_clip_color`, `set_clip_loop` MCP tools. Enhance: `fire_clip`, `stop_clip` to return JSON. Decide: keep or remove `add_notes_to_clip` (Phase 6 scope but already present).
3. **`MCP_Server/connection.py`** -- Add to `_WRITE_COMMANDS`: `delete_clip`, `duplicate_clip`, `set_clip_color`, `set_clip_loop`. Note: `get_clip_info` is a read command, not added here.
4. **`tests/test_clips.py`** -- Add smoke tests for new tools, update existing test expectations for enhanced responses.
5. **`tests/conftest.py`** -- No changes needed (clips.py already in `_GAC_PATCH_TARGETS`).

### Wire Commands Summary

| Command | Type | Params | Response |
|---------|------|--------|----------|
| `get_clip_info` | read | track_index, clip_index | Full clip detail or empty-slot status |
| `delete_clip` | write | track_index, clip_index | `{deleted: true, clip_name: "..."}` |
| `duplicate_clip` | write | track_index, clip_index, target_track_index, target_clip_index | New clip details at target |
| `set_clip_color` | write | track_index, clip_index, color | `{name, color, color_index}` |
| `set_clip_loop` | write | track_index, clip_index, [enabled, loop_start, loop_end, start_marker, end_marker] | All current loop/marker values |
| `fire_clip` (enhanced) | write | track_index, clip_index | `{fired, is_playing, clip_name}` |
| `stop_clip` (enhanced) | write | track_index, clip_index | `{stopped, clip_name}` |

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.25+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/test_clips.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLIP-01 | Create MIDI clip | smoke | `python -m pytest tests/test_clips.py::test_create_clip_calls_send_command -x` | Exists |
| CLIP-02 | Delete clip | smoke | `python -m pytest tests/test_clips.py::test_delete_clip_calls_send_command -x` | Wave 0 |
| CLIP-03 | Duplicate clip | smoke | `python -m pytest tests/test_clips.py::test_duplicate_clip_calls_send_command -x` | Wave 0 |
| CLIP-04 | Rename clip | smoke | `python -m pytest tests/test_clips.py::test_set_clip_name_calls_send_command -x` | Wave 0 |
| CLIP-05 | Set loop enabled | smoke | `python -m pytest tests/test_clips.py::test_set_clip_loop_calls_send_command -x` | Wave 0 |
| CLIP-06 | Set loop start/end | smoke | (covered by CLIP-05 test) | Wave 0 |
| CLIP-07 | Set start/end markers | smoke | (covered by CLIP-05 test) | Wave 0 |
| CLIP-08 | Fire clip | smoke | `python -m pytest tests/test_clips.py::test_fire_clip_returns_success -x` | Exists (needs update) |
| CLIP-09 | Stop clip | smoke | `python -m pytest tests/test_clips.py::test_stop_clip_returns_json -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_clips.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_clips.py::test_clip_tools_registered` -- update expected set with new tools (get_clip_info, delete_clip, duplicate_clip, set_clip_color, set_clip_loop)
- [ ] `tests/test_clips.py::test_delete_clip_calls_send_command` -- covers CLIP-02
- [ ] `tests/test_clips.py::test_duplicate_clip_calls_send_command` -- covers CLIP-03
- [ ] `tests/test_clips.py::test_get_clip_info_returns_json` -- covers get_clip_info
- [ ] `tests/test_clips.py::test_get_clip_info_empty_slot` -- covers empty slot behavior
- [ ] `tests/test_clips.py::test_set_clip_color_calls_send_command` -- covers set_clip_color
- [ ] `tests/test_clips.py::test_set_clip_loop_calls_send_command` -- covers CLIP-05/06/07
- [ ] `tests/test_clips.py::test_stop_clip_returns_json` -- covers CLIP-09
- [ ] `tests/test_clips.py::test_fire_clip_returns_json` -- update existing test for JSON response

## Open Questions

1. **`add_notes_to_clip` tool already in `tools/clips.py`**
   - What we know: This tool and its handler exist from pre-Phase-5 code. It belongs to Phase 6 (MIDI Editing).
   - What's unclear: Should we leave it as-is, or is it a concern during this phase?
   - Recommendation: Leave it untouched. It works and Phase 6 will enhance it. Don't break existing functionality.

2. **Clip signature properties (signature_numerator, signature_denominator)**
   - What we know: These are available on the Clip object per API docs.
   - What's unclear: Whether they're useful enough to include in get_clip_info (Claude's discretion).
   - Recommendation: Include them. They're cheap to read and could be useful for AI music generation context. Low risk, modest value.

3. **stop_clip behavior on empty slot**
   - What we know: `ClipSlot.stop()` works on empty slots (stops track playback at that slot). Current code doesn't check `has_clip`.
   - What's unclear: The user decision says to return `clip_name` in response, but empty slots have no clip name.
   - Recommendation: If `has_clip`, include `clip_name`. If not, return `{stopped: true}` without `clip_name`. Don't prevent the stop operation.

## Sources

### Primary (HIGH confidence)
- Ableton Live API Docs (Live 10.0.1) -- Clip class properties and methods: `looping`, `loop_start`, `loop_end`, `start_marker`, `end_marker`, `color_index`, `is_playing`, `is_triggered`, `is_audio_clip`, `name`, `length`
- Ableton Live API Docs (Live 9.7.0) -- ClipSlot methods: `create_clip`, `delete_clip`, `duplicate_clip_to`, `fire`, `stop`, `has_clip`
- Existing codebase: `handlers/clips.py`, `tools/clips.py`, `handlers/tracks.py`, `handlers/mixer.py`, `tests/test_clips.py`, `tests/test_mixer.py`

### Secondary (MEDIUM confidence)
- [Ableton Live API Documentation (structure-void.com)](https://structure-void.com/PythonLiveAPI_documentation/Live10.0.1.xml) -- Clip/ClipSlot full API surface
- [Ableton Live API Documentation (nsuspray GitHub)](https://nsuspray.github.io/Live_API_Doc/9.7.0.xml) -- Additional API reference
- [Ableton Live API Clip Duplication (Ruben Medrano)](https://rubenmedrano.wordpress.com/2016/11/04/ableton-live-api-how-to-copy-and-paste-clips/) -- duplicate_clip_to usage patterns and ClipSlotCopyHandler alternative

### Tertiary (LOW confidence)
- Loop region validation ordering -- inferred from API property setter behavior, not explicitly documented. Needs validation against actual Ableton instance.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- API surface verified across multiple documentation sources and existing working code
- Architecture: HIGH -- follows established patterns from Phases 3 and 4 exactly
- Pitfalls: MEDIUM -- loop ordering pitfall is inferred from API behavior rather than documented; fire/is_playing timing is based on understanding of quantization but not tested
- Integration: HIGH -- files to modify and patterns to follow are clear from existing codebase

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable -- Ableton API rarely changes between major versions)
