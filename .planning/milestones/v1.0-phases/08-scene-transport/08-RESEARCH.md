# Phase 8: Scene & Transport - Research

**Researched:** 2026-03-14
**Domain:** Ableton Live Python API -- Scene management and Transport control
**Confidence:** HIGH

## Summary

Phase 8 completes the scene management and transport control domains. Three transport commands already exist (start_playback, stop_playback, set_tempo) and need no reimplementation -- this phase adds the remaining 11 commands across scenes and transport. The Ableton Live Python API (Song class and Scene class) provides direct, well-documented methods for every requirement: `create_scene(index)`, `delete_scene(index)`, `scene.fire()`, `scene.name`, `continue_playing()`, `stop_all_clips()`, `undo()`, `redo()`, plus properties for `loop`, `loop_start`, `loop_length`, `current_song_time`, `signature_numerator`, and `signature_denominator`.

The existing codebase has empty placeholder stubs (`SceneHandlers` mixin class, `MCP_Server/tools/scenes.py` stub) ready for implementation. All patterns are well-established from Phases 3-7: `@command` decorator registration, mixin class handlers, conditional dict building for optional params, `json.dumps(result, indent=2)` structured responses, and patch-at-import-site test fixtures. No new libraries, architectural changes, or infrastructure work is needed.

**Primary recommendation:** Follow the exact patterns from clips.py/mixer.py for handler implementation, and clips.py/transport.py for MCP tool implementation. The API surface is straightforward -- every requirement maps 1:1 to a Song/Scene class method or property.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- create_scene takes an optional name parameter -- auto-names like Ableton (Scene N) if not provided
- Scene creation returns structured JSON response (consistent with track/clip creation patterns)
- Dedicated get_transport_state tool that returns full state: is_playing, tempo, time_signature, position, loop_enabled, loop_start, loop_length
- get_playback_position returns position only -- not playing status or tempo (lightweight check)
- Loop region (set_loop_region) specified in beats (float) -- consistent with Phase 5 clip loop params
- Playback position reported in beats (float)
- Undo and redo classified as write commands (main thread scheduling, 15s timeout)
- Warn after 3+ consecutive undo calls -- return advisory message in response

### Claude's Discretion
- Fire scene quantization -- whether to expose quantization param or fire immediately
- Scene delete behavior when scene is playing -- handle gracefully based on API behavior
- Transport command response richness (beyond get_transport_state)
- stop_all_clips behavior (clips only vs clips + transport) -- match Ableton native behavior
- set_tempo validation range (20-999 BPM) -- follow existing Phase 4 validation patterns
- set_time_signature validation -- accept what Ableton supports
- Whether to add a "panic" tool (combined stop all + stop transport + reset position)
- Playback position format details (raw beats, or also bars.beats)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCNE-01 | User can create scenes | `Song.create_scene(index)` returns Scene; index=-1 appends at end. Handler sets name after creation if provided. |
| SCNE-02 | User can name scenes | `Scene.name` is get/set property. Set directly after create or via separate command. |
| SCNE-03 | User can fire (launch) scenes | `Scene.fire(force_legato=False, can_select_scene_on_launch=True)` fires all clip slots in scene. |
| SCNE-04 | User can delete scenes | `Song.delete_scene(index)` removes scene. Raises exception if index invalid. |
| TRNS-01 | User can start playback | Already implemented: `Song.start_playing()` in existing TransportHandlers. |
| TRNS-02 | User can stop playback | Already implemented: `Song.stop_playing()` in existing TransportHandlers. |
| TRNS-03 | User can continue playback from current position | `Song.continue_playing()` resumes from current position (unlike start_playing which goes to start marker). |
| TRNS-04 | User can stop all clips | `Song.stop_all_clips(Quantized=True)` stops all playing clips but continues Song playback. |
| TRNS-05 | User can set tempo | Already implemented: `Song.tempo` property in existing TransportHandlers. Needs validation enhancement (20-999 BPM). |
| TRNS-06 | User can set time signature | `Song.signature_numerator` and `Song.signature_denominator` are get/set properties. |
| TRNS-07 | User can set loop region | `Song.loop` (bool), `Song.loop_start` (beats), `Song.loop_length` (beats) are all get/set properties. |
| TRNS-08 | User can get current playback position | `Song.current_song_time` is get/set property returning position in beats. |
| TRNS-09 | User can undo last action | `Song.undo()` undoes last action. `Song.can_undo` checks availability. |
| TRNS-10 | User can redo last undone action | `Song.redo()` redoes last undone action. `Song.can_redo` checks availability. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Ableton Live Python API (Song) | Live 12 / Python 3.11 | Scene creation/deletion, transport control, loop, undo/redo | Direct API -- no alternatives exist within Remote Script context |
| Ableton Live Python API (Scene) | Live 12 / Python 3.11 | Scene properties (name, color, fire) | Scene objects accessed via `self._song.scenes[index]` |
| MCP SDK (FastMCP) | >=1.3.0 | Tool registration for scene/transport MCP tools | Already in project dependencies |

### Supporting
No additional libraries needed. All functionality is provided by the Ableton Live API and existing project infrastructure.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct Song API | AbletonOSC wrapper | Adds OSC dependency, unnecessary -- we already have direct Python access |

## Architecture Patterns

### Recommended Project Structure
```
AbletonMCP_Remote_Script/
  handlers/
    scenes.py          # SceneHandlers mixin (currently empty placeholder)
    transport.py       # TransportHandlers mixin (extend with new commands)
MCP_Server/
  tools/
    scenes.py          # Scene MCP tools (currently empty stub)
    transport.py       # Transport MCP tools (extend with new tools)
  connection.py        # Add new commands to _WRITE_COMMANDS frozenset
tests/
  test_scenes.py       # New: scene domain smoke tests
  test_transport.py    # Extend: new transport tool smoke tests
  conftest.py          # Add scenes.py to patch targets
```

### Pattern 1: Handler Mixin with @command Decorator
**What:** Each domain has a mixin class with methods decorated by `@command(name, write=True|False)`.
**When to use:** Every new handler method.
**Example:**
```python
# Source: Established pattern from clips.py, mixer.py, transport.py
from AbletonMCP_Remote_Script.registry import command

class SceneHandlers:
    @command("create_scene", write=True)
    def _create_scene(self, params):
        index = params.get("index", -1)
        name = params.get("name", None)
        try:
            scene = self._song.create_scene(index)
            if name:
                scene.name = name
            actual_index = list(self._song.scenes).index(scene)
            return {
                "index": actual_index,
                "name": scene.name,
            }
        except Exception as e:
            self.log_message(f"Error creating scene: {e}")
            raise
```

### Pattern 2: MCP Tool with JSON Response
**What:** `@mcp.tool()` decorated function that calls `send_command` and returns `json.dumps(result, indent=2)`.
**When to use:** All new MCP tools (Phase 5+ convention).
**Example:**
```python
# Source: Established pattern from clips.py, notes.py
import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp

@mcp.tool()
def create_scene(ctx: Context, index: int = -1, name: str | None = None) -> str:
    """Create a new scene at the given index..."""
    try:
        ableton = get_ableton_connection()
        params = {"index": index}
        if name is not None:
            params["name"] = name
        result = ableton.send_command("create_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error("Failed to create scene", detail=str(e), ...)
```

### Pattern 3: Conditional Dict Building for Optional Params
**What:** Only include non-None values in the params dict sent to `send_command`.
**When to use:** set_loop_region, set_time_signature, get_transport_state, any tool with optional params.
**Example:**
```python
# Source: Established pattern from set_clip_loop in clips.py
params: dict = {}
if enabled is not None:
    params["enabled"] = enabled
if loop_start is not None:
    params["loop_start"] = loop_start
```

### Pattern 4: Validation with Current Value in Error
**What:** Validation errors include the current stored value for AI self-correction.
**When to use:** set_tempo range validation, time signature validation.
**Example:**
```python
# Source: Established pattern from mixer.py set_track_volume
if not (20.0 <= tempo <= 999.0):
    current = self._song.tempo
    raise ValueError(
        f"Tempo {tempo} out of range (20-999 BPM). Current value: {current}"
    )
```

### Anti-Patterns to Avoid
- **Importing Scene from Live module at module level:** Import inside method bodies for test compatibility (Phase 6 pattern).
- **Using `self._song.scenes.index(scene)` for scene index lookup:** The `scenes` property returns a tuple/list, but `create_scene` returns the new Scene object directly -- find its index from the scenes list after creation.
- **Modifying existing start_playback/stop_playback/set_tempo implementations:** These work. Add new commands alongside them, not by rewriting.
- **Toggle-style undo:** Always call `song.undo()` directly, never toggle. Check `can_undo`/`can_redo` before calling.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Scene creation | Manual clip slot manipulation | `Song.create_scene(index)` | API handles slot allocation, returns Scene object |
| Stop all clips | Iterating tracks and stopping each clip | `Song.stop_all_clips()` | API method is atomic, respects quantization |
| Undo/Redo | Custom action history | `Song.undo()` / `Song.redo()` | Ableton manages its own undo stack |
| Playback position formatting | Custom bars.beats parser | `Song.current_song_time` (beats float) | Raw beats is sufficient for AI consumption |
| Loop region | Custom loop toggle logic | `Song.loop`, `Song.loop_start`, `Song.loop_length` | Direct properties, no orchestration needed |

**Key insight:** Every requirement in this phase maps directly to a single Song or Scene property/method. There is no complex orchestration -- just wrapper handlers around API calls.

## Common Pitfalls

### Pitfall 1: create_scene Returns Scene Object, Not Index
**What goes wrong:** Assuming `create_scene(index)` returns the index of the new scene.
**Why it happens:** Unlike `create_midi_track` which modifies the tracks list in-place, `create_scene` returns a Scene object.
**How to avoid:** After creation, find the scene's index: `actual_index = list(self._song.scenes).index(scene)` or use the requested index (if not -1, it will be at that position; if -1, it will be `len(scenes) - 1`).
**Warning signs:** Tests receiving Scene objects when they expect integers.

### Pitfall 2: start_playing() vs continue_playing() Semantics
**What goes wrong:** Users expect `continue_playback` to resume from pause position but it behaves like `start_playing`.
**Why it happens:** `start_playing()` always starts from the start marker. `continue_playing()` resumes from `current_song_time`. Using the wrong one breaks user expectations.
**How to avoid:** Map `continue_playback` tool to `Song.continue_playing()`, not to `Song.start_playing()`. Document the distinction clearly in tool descriptions.
**Warning signs:** Playback always jumping to beat 0 when user expects resume.

### Pitfall 3: stop_all_clips Does NOT Stop Transport
**What goes wrong:** User calls `stop_all_clips` expecting everything to stop, but the Song continues playing (silent).
**Why it happens:** API docs: "Stop all playing Clips (if any) but continue playing the Song." This is Ableton's native behavior.
**How to avoid:** Document this in the tool description. If the user wants full stop, they need `stop_all_clips` + `stop_playback`. Consider implementing a "panic" convenience tool.
**Warning signs:** User confusion about silence but non-zero current_song_time.

### Pitfall 4: current_song_time Documentation Says "ms" but Returns Beats
**What goes wrong:** The API XML doc says "Get/Set access to the songs current playing position in ms" but in practice it returns beats.
**Why it happens:** Stale/inaccurate API documentation. Multiple sources (AbletonOSC, community) confirm the value is in beats.
**How to avoid:** Treat as beats (float). Cross-verified with AbletonOSC which labels it as beat-based. The CONTEXT.md decision already specifies beats.
**Warning signs:** Extremely large numbers would suggest ms; normal values (0-1000) indicate beats.

### Pitfall 5: Undo/Redo May Throw if Nothing to Undo
**What goes wrong:** Calling `undo()` when `can_undo` is False may raise an exception.
**Why it happens:** The API doesn't silently no-op on empty undo stack.
**How to avoid:** Check `self._song.can_undo` / `self._song.can_redo` before calling. Return informative message if nothing to undo/redo.
**Warning signs:** Unexpected exceptions in undo handler.

### Pitfall 6: Scene Delete When Only One Scene Exists
**What goes wrong:** Deleting the last scene raises an exception -- Ableton requires at least one scene.
**Why it happens:** Ableton's Session View always has at least one scene row.
**How to avoid:** Check `len(self._song.scenes) > 1` before delete. Return clear error: "Cannot delete the last scene."
**Warning signs:** "limitation error" or similar from API.

### Pitfall 7: Time Signature Denominator Must Be Power of 2
**What goes wrong:** Setting denominator to arbitrary values (e.g., 3, 5) fails.
**Why it happens:** Musical time signatures only use power-of-2 denominators (1, 2, 4, 8, 16).
**How to avoid:** Validate that denominator is in {1, 2, 4, 8, 16} before setting.
**Warning signs:** Silent failure or exception from Ableton.

### Pitfall 8: connection.py _WRITE_COMMANDS Not Updated
**What goes wrong:** New write commands use READ timeout (10s) instead of WRITE timeout (15s).
**Why it happens:** Forgetting to add new command names to `_WRITE_COMMANDS` frozenset in `connection.py`.
**How to avoid:** Add ALL new write commands to `_WRITE_COMMANDS` in `connection.py`. This is a checklist item.
**Warning signs:** Timeouts on operations that should be fast.

## Code Examples

Verified patterns from the Ableton Live Python API and existing codebase:

### Scene Creation with Optional Name
```python
# Source: Ableton Live API docs (create_scene returns Scene)
# Pattern: tracks.py create_midi_track
@command("create_scene", write=True)
def _create_scene(self, params):
    index = params.get("index", -1)
    name = params.get("name", None)
    try:
        scene = self._song.create_scene(index)
        actual_index = len(self._song.scenes) - 1 if index == -1 else index
        if name:
            scene.name = name
        return {
            "index": actual_index,
            "name": scene.name,
        }
    except Exception as e:
        self.log_message(f"Error creating scene: {e}")
        raise
```

### Scene Fire with Quantization Decision
```python
# Source: Ableton Live API docs
# Scene.fire(force_legato=False, can_select_scene_on_launch=True)
# Recommendation: fire immediately (no quantization param exposed)
@command("fire_scene", write=True)
def _fire_scene(self, params):
    scene_index = params.get("scene_index", 0)
    try:
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            raise IndexError(
                f"Scene index {scene_index} out of range "
                f"(0-{len(self._song.scenes) - 1})"
            )
        scene = self._song.scenes[scene_index]
        scene.fire()
        return {
            "fired": True,
            "index": scene_index,
            "name": scene.name,
        }
    except Exception as e:
        self.log_message(f"Error firing scene: {e}")
        raise
```

### get_transport_state (Composite Read)
```python
# Source: base.py get_session_info pattern + CONTEXT.md decision
@command("get_transport_state")
def _get_transport_state(self, params=None):
    try:
        return {
            "is_playing": self._song.is_playing,
            "tempo": self._song.tempo,
            "time_signature": {
                "numerator": self._song.signature_numerator,
                "denominator": self._song.signature_denominator,
            },
            "position": self._song.current_song_time,
            "loop_enabled": self._song.loop,
            "loop_start": self._song.loop_start,
            "loop_length": self._song.loop_length,
        }
    except Exception as e:
        self.log_message(f"Error getting transport state: {e}")
        raise
```

### set_loop_region with Conditional Params
```python
# Source: set_clip_loop pattern from clips.py
@command("set_loop_region", write=True)
def _set_loop_region(self, params):
    try:
        if "enabled" in params:
            self._song.loop = params["enabled"]
        if "start" in params:
            self._song.loop_start = params["start"]
        if "length" in params:
            self._song.loop_length = params["length"]
        return {
            "loop_enabled": self._song.loop,
            "loop_start": self._song.loop_start,
            "loop_length": self._song.loop_length,
        }
    except Exception as e:
        self.log_message(f"Error setting loop region: {e}")
        raise
```

### Undo with can_undo Check and Consecutive Warning
```python
# Source: CONTEXT.md decision (warn after 3+ consecutive undo calls)
@command("undo", write=True)
def _undo(self, params=None):
    try:
        if not self._song.can_undo:
            return {"undone": False, "message": "Nothing to undo"}
        self._song.undo()
        return {"undone": True}
    except Exception as e:
        self.log_message(f"Error performing undo: {e}")
        raise
```

### stop_all_clips (Ableton Native Behavior)
```python
# Source: Ableton API docs
# stop_all_clips(Quantized=True) - stops clips but Song continues
@command("stop_all_clips", write=True)
def _stop_all_clips(self, params=None):
    try:
        self._song.stop_all_clips()
        return {
            "stopped": True,
            "transport_playing": self._song.is_playing,
        }
    except Exception as e:
        self.log_message(f"Error stopping all clips: {e}")
        raise
```

## Ableton Live API Reference

### Song Class Methods (Scene Management)

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `create_scene` | `(index: int) -> Scene` | Scene object | Create scene at index. -1 = append at end. Raises on invalid index. |
| `delete_scene` | `(index: int) -> None` | None | Delete scene at index. Raises if index invalid. |
| `duplicate_scene` | `(index: int) -> None` | None | Duplicate scene, selects new one. |

### Song Class Methods (Transport)

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `start_playing` | `() -> None` | None | Start from start marker |
| `stop_playing` | `() -> None` | None | Stop playback |
| `continue_playing` | `() -> None` | None | Resume from current position |
| `stop_all_clips` | `(Quantized=True) -> None` | None | Stop clips, Song keeps playing |
| `undo` | `() -> None` | None | Undo last action |
| `redo` | `() -> None` | None | Redo last undone action |

### Song Class Properties

| Property | Type | Access | Description |
|----------|------|--------|-------------|
| `scenes` | list[Scene] | Read | All scenes in the Session |
| `is_playing` | bool | Read | Whether Song is currently playing |
| `tempo` | float | Read/Write | Global tempo (BPM) |
| `signature_numerator` | int | Read/Write | Time signature numerator |
| `signature_denominator` | int | Read/Write | Time signature denominator |
| `loop` | bool | Read/Write | Loop enabled/disabled |
| `loop_start` | float | Read/Write | Loop start position in beats |
| `loop_length` | float | Read/Write | Loop length in beats |
| `current_song_time` | float | Read/Write | Current playback position in beats |
| `can_undo` | bool | Read | Whether undo is available |
| `can_redo` | bool | Read | Whether redo is available |

### Scene Class Properties and Methods

| Property/Method | Type | Access | Description |
|-----------------|------|--------|-------------|
| `name` | str | Read/Write | Scene name. May contain "BPM" substring for tempo changes. |
| `color` | int | Read/Write | Scene color (RGB) |
| `color_index` | int | Read/Write | Scene color index from palette |
| `is_empty` | bool | Read | True if all clip slots empty |
| `is_triggered` | bool | Read | Scene's trigger state |
| `clip_slots` | list | Read | ClipSlots in this scene |
| `tempo` | float | Read/Write | Per-scene tempo override. Returns -1 if no tempo property. |
| `fire()` | method | -- | `fire(force_legato=False, can_select_scene_on_launch=True)` fires all clip slots |
| `fire_as_selected()` | method | -- | Fire and select next scene |
| `set_fire_button_state()` | method | -- | Set fire button state directly |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| If/elif dispatch chain | Dict-based @command registry | Phase 1 (this project) | New handlers use @command decorator only |
| Plain text tool responses | json.dumps structured responses | Phase 5 (this project) | All new tools MUST return JSON |
| No validation on set_tempo | Range validation with current value | Phase 4 pattern | Apply same pattern to enhanced set_tempo |

**Already existing (DO NOT reimplement):**
- `start_playback` -- TransportHandlers._start_playback (wire command: "start_playback")
- `stop_playback` -- TransportHandlers._stop_playback (wire command: "stop_playback")
- `set_tempo` -- TransportHandlers._set_tempo (wire command: "set_tempo") -- needs validation enhancement

## Integration Checklist

These files MUST be updated for full integration:

| File | Change | Why |
|------|--------|-----|
| `AbletonMCP_Remote_Script/handlers/scenes.py` | Implement SceneHandlers methods | Core handler logic |
| `AbletonMCP_Remote_Script/handlers/transport.py` | Add continue_playing, stop_all_clips, set_time_signature, set_loop_region, get_playback_position, get_transport_state, undo, redo | Extend existing mixin |
| `MCP_Server/tools/scenes.py` | Add create_scene, set_scene_name, fire_scene, delete_scene tools | MCP tool exposure |
| `MCP_Server/tools/transport.py` | Add continue_playback, stop_all_clips, set_time_signature, set_loop_region, get_playback_position, get_transport_state, undo, redo tools | MCP tool exposure |
| `MCP_Server/tools/__init__.py` | Uncomment/add `scenes` import | Tool registration |
| `MCP_Server/connection.py` | Add new commands to `_WRITE_COMMANDS` frozenset | Correct timeout routing |
| `tests/conftest.py` | Add `MCP_Server.tools.scenes.get_ableton_connection` to `_GAC_PATCH_TARGETS` | Test fixture patching |
| `tests/test_scenes.py` | New file -- scene tool smoke tests | Validation |
| `tests/test_transport.py` | Add tests for new transport tools | Validation |

## Discretion Recommendations

Based on research findings:

| Decision Area | Recommendation | Rationale |
|---------------|----------------|-----------|
| Fire scene quantization | Do NOT expose quantization param; fire immediately | Simplicity. `Scene.fire()` defaults are sensible. Quantization is niche. |
| Scene delete when playing | Let it fail naturally; catch and return clear error | API will raise if invalid. No special pre-handling needed. |
| stop_all_clips behavior | Clips only (match Ableton native: Song keeps playing) | API doc: "Stop all playing Clips but continue playing the Song." |
| set_tempo validation | 20-999 BPM range, matching existing tool docstring | Already documented in existing MCP tool. Add handler-side validation. |
| Time signature validation | Numerator 1-32, denominator in {1,2,4,8,16} | Standard musical time signatures. Power-of-2 denominators required. |
| Panic tool | Skip for v1 | Users can call stop_all_clips + stop_playback. Adds complexity without strong need. |
| Playback position format | Raw beats only | Bars.beats requires knowing time signature and adds complexity. AI can compute if needed. |
| Transport response richness | Include is_playing in responses for start/stop/continue | Lightweight confirmation. Don't include full transport state in every response. |

## Open Questions

1. **set_tempo handler-side validation**
   - What we know: Existing MCP tool docstring says 20-999, but handler does NOT validate
   - What's unclear: Should we add validation to the existing `_set_tempo` handler or leave it to Ableton?
   - Recommendation: Add range validation to the handler (Phase 4 pattern). This is a minor enhancement, not a rewrite. If Ableton silently clamps, our validation is friendlier.

2. **Scene index after create_scene(-1)**
   - What we know: `create_scene(-1)` appends at end and returns the Scene object
   - What's unclear: Is the index always `len(scenes) - 1` after creation?
   - Recommendation: Use `len(self._song.scenes) - 1` as the index when `index == -1`. This matches the `create_midi_track` pattern exactly.

3. **Undo consecutive warning mechanism**
   - What we know: CONTEXT.md says "warn after 3+ consecutive undo calls"
   - What's unclear: Where to track consecutive count -- handler instance state vs MCP tool state
   - Recommendation: Track in MCP tool layer (module-level counter), not handler. Handler returns success/failure; tool adds warning text. Counter resets on any non-undo tool call. This is simplest since handler has no session state.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.25+ |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/test_scenes.py tests/test_transport.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCNE-01 | Create scene sends correct command | unit | `python -m pytest tests/test_scenes.py::test_create_scene_calls_send_command -x` | Wave 0 |
| SCNE-02 | Set scene name sends correct command | unit | `python -m pytest tests/test_scenes.py::test_set_scene_name_calls_send_command -x` | Wave 0 |
| SCNE-03 | Fire scene sends correct command | unit | `python -m pytest tests/test_scenes.py::test_fire_scene_calls_send_command -x` | Wave 0 |
| SCNE-04 | Delete scene sends correct command | unit | `python -m pytest tests/test_scenes.py::test_delete_scene_calls_send_command -x` | Wave 0 |
| TRNS-01 | Start playback returns message | unit | `python -m pytest tests/test_transport.py::test_start_playback_returns_message -x` | Exists |
| TRNS-02 | Stop playback returns message | unit | `python -m pytest tests/test_transport.py::test_stop_playback_returns_message -x` | Exists (implicit) |
| TRNS-03 | Continue playback sends correct command | unit | `python -m pytest tests/test_transport.py::test_continue_playback_calls_send_command -x` | Wave 0 |
| TRNS-04 | Stop all clips sends correct command | unit | `python -m pytest tests/test_transport.py::test_stop_all_clips_calls_send_command -x` | Wave 0 |
| TRNS-05 | Set tempo sends correct command | unit | `python -m pytest tests/test_transport.py::test_set_tempo_calls_send_command -x` | Exists |
| TRNS-06 | Set time signature sends correct command | unit | `python -m pytest tests/test_transport.py::test_set_time_signature_calls_send_command -x` | Wave 0 |
| TRNS-07 | Set loop region sends correct params | unit | `python -m pytest tests/test_transport.py::test_set_loop_region_calls_send_command -x` | Wave 0 |
| TRNS-08 | Get playback position returns JSON | unit | `python -m pytest tests/test_transport.py::test_get_playback_position_returns_json -x` | Wave 0 |
| TRNS-09 | Undo sends correct command | unit | `python -m pytest tests/test_transport.py::test_undo_calls_send_command -x` | Wave 0 |
| TRNS-10 | Redo sends correct command | unit | `python -m pytest tests/test_transport.py::test_redo_calls_send_command -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_scenes.py tests/test_transport.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_scenes.py` -- covers SCNE-01 through SCNE-04 (new file)
- [ ] `tests/test_transport.py` -- extend with TRNS-03, TRNS-04, TRNS-06, TRNS-07, TRNS-08, TRNS-09, TRNS-10 (existing file, new tests)
- [ ] `tests/conftest.py` -- add `MCP_Server.tools.scenes.get_ableton_connection` to `_GAC_PATCH_TARGETS`

## Sources

### Primary (HIGH confidence)
- [AbletonLive-API-Stub Live.xml](https://github.com/cylab/AbletonLive-API-Stub/blob/master/Live.xml) -- Song class and Scene class method signatures, property types, parameter documentation. Extracted via raw XML parsing.
- Existing codebase (`handlers/transport.py`, `handlers/clips.py`, `handlers/mixer.py`, `tools/clips.py`, `tools/transport.py`) -- established patterns for handler structure, tool structure, validation, response format.

### Secondary (MEDIUM confidence)
- [AbletonOSC README and source](https://github.com/ideoforms/AbletonOSC) -- Cross-verified API surface: create_scene, delete_scene, continue_playing, stop_all_clips, undo, redo, loop properties, current_song_time. Confirmed AbletonOSC wraps the same Live Python API methods we call directly.
- [AbletonOSC scene.py](https://github.com/ideoforms/AbletonOSC/blob/master/abletonosc/scene.py) -- Scene class properties: name, color, color_index, tempo, tempo_enabled, is_empty, is_triggered, fire(), fire_as_selected().

### Tertiary (LOW confidence)
- None -- all findings verified through primary or secondary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- using direct Ableton Live Python API, same as all previous phases
- Architecture: HIGH -- exact patterns established in Phases 3-7, no new patterns needed
- Pitfalls: HIGH -- API behavior verified through official docs and cross-reference with AbletonOSC
- Scene API: HIGH -- method signatures extracted from official API XML documentation
- Transport API: HIGH -- three methods already implemented and working in production
- Undo consecutive tracking: MEDIUM -- implementation location (MCP tool vs handler) is a design choice, not an API question

**Research date:** 2026-03-14
**Valid until:** Indefinite -- Ableton Live Python API is stable across major versions. These Song/Scene APIs have existed since Live 9.
