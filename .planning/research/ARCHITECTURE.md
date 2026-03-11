# Architecture Research

**Domain:** MCP-to-DAW bridge (AI assistant control of Ableton Live)
**Researched:** 2026-03-10
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    MCP CLIENT (Claude AI)                         │
│              (FastMCP / Model Context Protocol)                   │
└──────────────────────────────┬───────────────────────────────────┘
                               │ MCP Protocol (stdio/SSE)
┌──────────────────────────────▼───────────────────────────────────┐
│                    MCP SERVER LAYER                               │
│  MCP_Server/                                                      │
│  ├── server.py          ← FastMCP instance + lifespan            │
│  └── tools/             ← Domain-grouped tool modules            │
│      ├── transport.py   ← start_playback, stop_playback, tempo   │
│      ├── tracks.py      ← create, rename, delete tracks          │
│      ├── clips.py       ← create, edit, fire, stop clips         │
│      ├── notes.py       ← add_notes, quantize, transpose         │
│      ├── devices.py     ← load instruments, effects, params      │
│      ├── mixer.py       ← volume, pan, sends, routing            │
│      ├── scenes.py      ← scene create, launch, rename           │
│      ├── browser.py     ← navigate, search, load presets         │
│      ├── arrangement.py ← arrangement clips, loop, markers       │
│      └── automation.py  ← envelopes, breakpoints                 │
└──────────────────────────────┬───────────────────────────────────┘
                               │ JSON over TCP (localhost:9877)
┌──────────────────────────────▼───────────────────────────────────┐
│                 ABLETON REMOTE SCRIPT LAYER                       │
│  AbletonMCP_Remote_Script/                                        │
│  ├── __init__.py        ← AbletonMCP(ControlSurface) entry point │
│  ├── server.py          ← Socket server + command dispatch       │
│  └── handlers/          ← Domain command handler modules         │
│      ├── base.py        ← BaseHandler with shared helpers        │
│      ├── transport.py   ← Playback, tempo, time sig              │
│      ├── tracks.py      ← Track CRUD, properties                 │
│      ├── clips.py       ← Clip CRUD, session/arrangement         │
│      ├── notes.py       ← MIDI note operations                   │
│      ├── devices.py     ← Device loading, parameter access       │
│      ├── mixer.py       ← Volume, pan, sends, routing            │
│      ├── scenes.py      ← Scene operations                       │
│      ├── browser.py     ← Browser navigation, preset loading     │
│      ├── arrangement.py ← Arrangement view operations            │
│      └── automation.py  ← Automation envelopes                   │
└──────────────────────────────┬───────────────────────────────────┘
                               │ Live Object Model API
┌──────────────────────────────▼───────────────────────────────────┐
│                  ABLETON LIVE 12                                  │
│  Song → Tracks → ClipSlots → Clips → Devices → Parameters        │
│       → Scenes                                                    │
│       → MasterTrack → MixerDevice                                │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Boundary |
|-----------|----------------|----------|
| `server.py` (MCP) | FastMCP instance, lifespan, AbletonConnection singleton | Owns MCP protocol surface and connection state |
| `tools/*.py` (MCP) | MCP tool definitions grouped by domain; translate Claude intent → JSON command | Never touches socket directly; delegates to AbletonConnection |
| `AbletonConnection` | Socket lifecycle, JSON encode/decode, retry, response assembly | Single object per server process; all tools share it |
| `AbletonMCP.__init__` | ControlSurface entry, socket server lifecycle, threading | Bridge between Ableton's plugin system and command dispatch |
| `server.py` (Remote Script) | Accept TCP connections, buffer incoming JSON, dispatch to handlers | Runs on a background socket thread; never calls Live API directly |
| `handlers/base.py` | Shared Live API access helpers, index validation, error wrapping | Referenced by all domain handlers |
| `handlers/*.py` | Domain-specific Live API calls, always run on main thread | No socket I/O; only Live object model access |

## Recommended Project Structure

```
MCP_Server/
├── server.py                # FastMCP instance, lifespan, AbletonConnection
└── tools/
    ├── __init__.py          # Registers all sub-modules with mcp instance
    ├── transport.py         # start_playback, stop_playback, set_tempo, set_time_signature
    ├── tracks.py            # create_midi_track, create_audio_track, delete_track, set_track_name, get_track_info
    ├── clips.py             # create_clip, delete_clip, fire_clip, stop_clip, set_clip_name, get_clip_info
    ├── notes.py             # add_notes_to_clip, clear_notes, quantize_clip, transpose_clip, set_note_velocity
    ├── devices.py           # load_instrument, load_effect, get_device_params, set_device_param, remove_device
    ├── mixer.py             # set_volume, set_pan, set_send, get_mixer_state, mute_track, solo_track
    ├── scenes.py            # create_scene, delete_scene, fire_scene, set_scene_name, get_scenes
    ├── browser.py           # get_browser_tree, browse_path, load_preset, search_browser
    ├── arrangement.py       # create_arrangement_clip, move_clip, set_loop_points, get_arrangement
    └── automation.py        # add_automation_point, clear_automation, get_automation

AbletonMCP_Remote_Script/
├── __init__.py              # AbletonMCP(ControlSurface) — entry, socket startup, disconnect cleanup
├── server.py                # Socket accept loop, JSON buffering, command dispatch table
└── handlers/
    ├── __init__.py          # Exports all handler classes
    ├── base.py              # BaseHandler: song ref, index helpers, main-thread decorator
    ├── transport.py         # TransportHandler
    ├── tracks.py            # TrackHandler
    ├── clips.py             # ClipHandler
    ├── notes.py             # NoteHandler
    ├── devices.py           # DeviceHandler
    ├── mixer.py             # MixerHandler
    ├── scenes.py            # SceneHandler
    ├── browser.py           # BrowserHandler
    ├── arrangement.py       # ArrangementHandler
    └── automation.py        # AutomationHandler
```

### Structure Rationale

- **`tools/` domain split:** FastMCP supports mounting sub-servers or direct import; one file per domain keeps each file under ~200 lines, readable and testable in isolation. Tools in the same file share helpers without cross-file imports.
- **`handlers/` mirroring LOM hierarchy:** The Live Object Model is `Song -> Tracks -> Clips -> Devices -> Parameters`. Handlers mirror this — one handler per LOM object type. This matches how AbletonOSC (the reference implementation at scale) structures its 14 modules.
- **`base.py` shared helpers:** Index validation, song-reference access, the `@main_thread` decorator — these are used by every handler. Centralizing prevents copy-paste drift.
- **`server.py` (Remote Script) as pure router:** Separating the dispatch table from handler implementations keeps the router ignorant of business logic. Adding a new command means adding one handler method and one entry in the dispatch dict — not editing a giant `_process_command` if/elif chain.

## Architectural Patterns

### Pattern 1: Dict-Based Command Router (replaces if/elif chain)

**What:** A dictionary maps command type strings to handler methods. Dispatch is O(1) and handlers are registered at startup. Replacing `elif command_type == "X": ...` chains with a lookup table.

**When to use:** Any time you have more than ~10 command types. The current if/elif chain is already at 15 entries and will break down at 50+.

**Trade-offs:** Slightly less readable than explicit ifs for newcomers; dramatically more maintainable at scale. Adding a command is one dict entry + one method, not touching dispatch logic.

**Example:**
```python
# In server.py (Remote Script)
class CommandDispatcher:
    def __init__(self, song):
        self._handlers = {
            # Query commands — run directly on socket thread (read-only)
            "get_session_info": TransportHandler(song).get_session_info,
            "get_track_info": TrackHandler(song).get_track_info,
            "get_browser_tree": BrowserHandler(song).get_browser_tree,
            # Mutating commands — MUST be scheduled on main thread
            "create_midi_track": (TrackHandler(song).create_midi_track, True),
            "add_notes_to_clip": (NoteHandler(song).add_notes_to_clip, True),
            "set_device_parameter": (DeviceHandler(song).set_device_parameter, True),
        }

    def dispatch(self, command_type, params):
        entry = self._handlers.get(command_type)
        if entry is None:
            return {"status": "error", "message": f"Unknown command: {command_type}"}
        handler, needs_main_thread = entry if isinstance(entry, tuple) else (entry, False)
        if needs_main_thread:
            return self._run_on_main_thread(handler, params)
        return {"status": "success", "result": handler(params)}
```

### Pattern 2: Main-Thread Decorator (replaces inline queue boilerplate)

**What:** A decorator wraps any Live API call to schedule it on Ableton's main thread via `schedule_message()` and block until a result queue is populated. Currently this 20-line boilerplate is duplicated for every mutating command.

**When to use:** Every command that writes to the Live API. Read-only getters that only read Live properties can often run directly (but schedule_message is safe for reads too).

**Trade-offs:** Slightly less visible what's happening; dramatically reduces code volume. Every handler method stays clean — no queue setup in the business logic.

**Example:**
```python
# In handlers/base.py
import queue
import functools

def main_thread(timeout=10.0):
    """Decorator: schedules the wrapped method on Ableton's main thread."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, params):
            response_queue = queue.Queue()
            def task():
                try:
                    result = fn(self, params)
                    response_queue.put({"status": "success", "result": result})
                except Exception as e:
                    response_queue.put({"status": "error", "message": str(e)})
            try:
                self._control_surface.schedule_message(0, task)
            except AssertionError:
                task()  # Already on main thread
            try:
                return response_queue.get(timeout=timeout)
            except queue.Empty:
                return {"status": "error", "message": "Timeout: main thread task did not complete"}
        return wrapper
    return decorator

class BaseHandler:
    def __init__(self, control_surface):
        self._cs = control_surface
        self._song = control_surface.song()

    def _get_track(self, index):
        tracks = list(self._song.tracks)
        if not 0 <= index < len(tracks):
            raise IndexError(f"Track index {index} out of range (0-{len(tracks)-1})")
        return tracks[index]
```

### Pattern 3: FastMCP Server Composition (MCP side tool organization)

**What:** Instead of one giant `server.py` with 50+ tool definitions, create domain-specific modules and register them with the shared FastMCP instance via import.

**When to use:** When a single server.py would exceed ~400 lines. FastMCP supports `mount()` for full sub-server composition with automatic namespacing, or simpler direct import registration.

**Trade-offs:** `mount()` adds tool name prefixes (e.g., `tracks_create_midi_track`) which aids discoverability but changes tool names. Direct import (shared mcp instance) avoids prefixing. Prefer direct import for this project since tool names should be stable for Claude's learned patterns.

**Example (direct import — recommended for this project):**
```python
# MCP_Server/server.py
from mcp.server.fastmcp import FastMCP
from contextlib import asynccontextmanager

mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)

# Register all tool modules — each imports `mcp` and decorates functions
import tools.transport   # noqa: registers tools as side effect
import tools.tracks      # noqa
import tools.clips       # noqa
import tools.notes       # noqa
import tools.devices     # noqa
import tools.mixer       # noqa
import tools.scenes      # noqa
import tools.browser     # noqa
import tools.arrangement # noqa
import tools.automation  # noqa
```

```python
# MCP_Server/tools/tracks.py
from ..server import mcp, get_ableton_connection

@mcp.tool()
def create_midi_track(track_index: int = -1) -> str:
    """Create a new MIDI track. track_index=-1 appends at end."""
    conn = get_ableton_connection()
    result = conn.send_command("create_midi_track", {"index": track_index})
    return f"Created MIDI track: {result.get('name')}"
```

### Pattern 4: Read/Write Command Classification at the Protocol Level

**What:** Commands are declared as read-only or write (mutating) in the protocol itself, not inferred at runtime from a hardcoded list. This eliminates the fragile `is_modifying_command` list in `send_command()`.

**When to use:** Immediately — the current approach of maintaining a list of command strings that need delays is error-prone. Every new command must be manually added to the list.

**Trade-offs:** Requires a protocol change (add a `"mutating": true` field, or prefix command names), but pays off immediately as command count grows.

**Example:**
```python
# Command naming convention: no prefix = read, "set_" / "create_" / "delete_" / "add_" = write
# Server.py infers from name:
READ_PREFIXES = ("get_",)
WRITE_PREFIXES = ("set_", "create_", "delete_", "add_", "fire_", "stop_", "start_", "load_", "clear_")

def is_mutating(command_type: str) -> bool:
    return any(command_type.startswith(p) for p in WRITE_PREFIXES)
```

## Data Flow

### Command Execution Flow (write path)

```
Claude invokes tool (e.g., create_midi_track)
    |
    v
tools/tracks.py: create_midi_track(track_index)
    |
    v
AbletonConnection.send_command("create_midi_track", {"index": -1})
    |  [JSON encode → TCP send]
    v
Remote Script: _handle_client() receives bytes, JSON decode
    |
    v
CommandDispatcher.dispatch("create_midi_track", params)
    |  [detects mutating command]
    v
schedule_message(0, TrackHandler.create_midi_track)
    |  [deferred to Ableton main thread]
    v
TrackHandler.create_midi_track(params) — runs on main thread
    | calls song.create_midi_track(index)
    v
response_queue.put({"status": "success", "result": {...}})
    |
    v
CommandDispatcher returns response to _handle_client
    |  [JSON encode → TCP send]
    v
AbletonConnection receives response, returns dict to tool
    |
    v
Tool formats and returns string to Claude
```

### Query Execution Flow (read path)

```
Claude invokes tool (e.g., get_track_info)
    |
    v
AbletonConnection.send_command("get_track_info", {"track_index": 0})
    |  [no sleep delay, shorter timeout]
    v
CommandDispatcher: detects read command, calls directly (no scheduling)
    | TrackHandler.get_track_info(params) — reads Live API
    v
Returns JSON response immediately
```

### Key Data Flow Rules

1. **All Live API mutations go through schedule_message.** No exceptions. Direct calls from socket threads crash Ableton unpredictably.
2. **Read-only Live API calls may run on the socket thread** but schedule_message is safe for reads too when in doubt.
3. **Tool results are always strings returned to Claude.** JSON is for the MCP-to-RemoteScript protocol only; Claude gets human-readable text.
4. **AbletonConnection is a singleton.** One persistent TCP connection for the server lifetime. All tools share it. No connection-per-tool.

### State Management

```
AbletonConnection (module global in server.py)
    |
    ├── Lazily initialized on first tool call
    ├── Validated with empty-byte ping before each tool call
    └── Replaced on connection failure (reconnect up to 3 times)

Remote Script (AbletonMCP instance — Ableton lifecycle)
    |
    ├── song() reference cached on __init__ as self._song
    ├── Socket server thread: daemon, started in __init__
    └── All handler instances created at startup, hold ref to self._song
```

## Scaling Considerations

| Concern | Current (15 tools) | At Scale (50+ tools) |
|---------|-------------------|----------------------|
| Command routing | if/elif chain (works) | Dict dispatch table (required) |
| Main-thread boilerplate | Inline per command (duplicated) | Decorator pattern (DRY) |
| Tool file organization | Single server.py | Domain modules in tools/ |
| Handler file organization | Single __init__.py | Domain handlers/ package |
| Protocol command classification | Hardcoded list in send_command | Name-prefix inference |
| Error handling | Try/except per tool | BaseHandler shared handling |

### Scaling Priorities

1. **First pain point:** The if/elif dispatch chain. At 15 commands it is already 60+ lines inside `_process_command`. At 50 it becomes unmanageable. Fix this before adding commands.
2. **Second pain point:** The `is_modifying_command` list in `send_command()`. Every new command must be manually added or it silently gets wrong timeout/delay behavior. Automate this via naming convention.
3. **Third pain point:** Single-file tool sprawl. `server.py` at 660 lines with 15 tools extrapolates to 2200+ lines with 50 tools. Extract to `tools/` modules immediately.

## Anti-Patterns

### Anti-Pattern 1: Growing the if/elif Chain

**What people do:** Add `elif command_type == "new_command":` to `_process_command()` for every new feature.

**Why it's wrong:** At 50 commands, `_process_command()` is 300+ lines of boilerplate with no structure. Finding a bug requires scanning the entire function. The duplicate main-thread queue setup bloats further.

**Do this instead:** Dict-based dispatch table. Register handler methods at startup. Adding a command is two lines: one dict entry, one handler method.

### Anti-Pattern 2: Calling Live API from Socket Thread

**What people do:** Skip `schedule_message()` for "simple" reads or writes, call `self._song.tracks` directly in the socket handler thread.

**Why it's wrong:** Ableton's Live API is not thread-safe. Direct calls from background threads cause silent data corruption, crashes, or `AssertionError` exceptions. Even reads can trigger Live's internal state verification which asserts main-thread context.

**Do this instead:** Always use `schedule_message(0, callback)` for any Live API access. The overhead is negligible (~1ms main-thread delay). Use `queue.Queue` to get results back to the socket thread.

### Anti-Pattern 3: Monolithic Remote Script

**What people do:** Put all 50+ handler implementations in `__init__.py` alongside the socket server and ControlSurface boilerplate.

**Why it's wrong:** `__init__.py` becomes 3000+ lines. Ableton cannot live-reload individual files — the entire script reloads. During development, debugging a single handler requires parsing a giant file.

**Do this instead:** Extract a `handlers/` package. Each domain handler is a separate file. AbletonOSC (the production reference for this pattern) uses exactly this structure: `song.py`, `track.py`, `clip.py`, `device.py`, each 100-300 lines.

### Anti-Pattern 4: time.sleep() for Timing

**What people do:** Add `time.sleep(0.1)` before and after state-modifying commands to "give Ableton time to process."

**Why it's wrong:** This is cargo-cult synchronization. The actual synchronization mechanism is `schedule_message()` + `queue.Queue`. The sleep adds 200ms of unnecessary latency to every mutating operation. With 50+ tools, multi-step operations (create track → load instrument → add notes) accumulate seconds of artificial delay.

**Do this instead:** Trust the queue. `schedule_message(0, task)` guarantees the task runs on the main thread. `response_queue.get(timeout=10.0)` blocks until it completes. No sleep needed.

### Anti-Pattern 5: Hardcoded URI Strings for Browser Loading

**What people do:** Require callers to provide exact URI strings like `'query:Synths#Instrument%20Rack:Bass:FileId_5116'` to load instruments.

**Why it's wrong:** URIs are internal, version-specific, and not human-discoverable. Claude cannot know valid URIs without browsing first. Broken instrument loading is the #1 existing defect (per PROJECT.md) and hardcoded URIs are a root cause.

**Do this instead:** Expose browser navigation tools (`get_browser_tree`, `get_browser_items_at_path`) and implement path-based loading that resolves URIs internally. Claude navigates the browser tree, then loads by path — never by raw URI.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Critical Constraint |
|----------|---------------|---------------------|
| MCP tools ↔ AbletonConnection | Method calls on shared singleton | AbletonConnection is not thread-safe across concurrent FastMCP calls; FastMCP async context means tools run in event loop — sync socket calls block correctly |
| AbletonConnection ↔ Remote Script | JSON over TCP localhost:9877 | Single persistent connection; both sides must handle partial reads, framing, and disconnects |
| Socket thread ↔ Live main thread | schedule_message + queue.Queue | The only approved crossing point; no direct calls across this boundary |
| Remote Script handlers ↔ Live API | Direct Python Live API calls | Must only happen on main thread; Ableton asserts this and raises on violation |

### Build Order Implications

The architecture has clear dependency layers that dictate build order:

1. **Protocol foundation first** — Clean up Python 2 artifacts, establish the JSON protocol, fix `receive_full_response` framing. Everything else depends on a working socket layer.

2. **Handler infrastructure second** — `handlers/base.py` with `BaseHandler`, the `@main_thread` decorator, index helpers. All domain handlers depend on this.

3. **Dict dispatch router third** — `server.py` command dispatcher. Once the router exists, domain handlers can be added independently without touching dispatch logic.

4. **Domain handlers incrementally** — Each domain handler (`transport`, `tracks`, `clips`, `notes`, `devices`, `mixer`) is independently buildable once infrastructure exists. Tackle in order of user impact: transport → tracks → clips → notes → devices → mixer → scenes → browser → arrangement → automation.

5. **MCP tool modules last** — Tools are thin wrappers over commands; they can only be written once the corresponding Remote Script handler exists. Build MCP tools in lock-step with their handlers.

## Sources

- AbletonOSC handler architecture (reference implementation for multi-handler Remote Scripts): [github.com/ideoforms/AbletonOSC](https://github.com/ideoforms/AbletonOSC)
- AbletonOSC DeepWiki architecture overview: [deepwiki.com/ideoforms/AbletonOSC](https://deepwiki.com/ideoforms/AbletonOSC)
- FastMCP server composition (mount, import_server): [gofastmcp.com/servers/composition](https://gofastmcp.com/servers/composition)
- Ableton Live Object Model hierarchy: [docs.cycling74.com/apiref/lom/](https://docs.cycling74.com/apiref/lom/)
- Ableton threading constraints (no threading module, use on_timer): [Ableton Forum thread 174043](https://forum.ableton.com/viewtopic.php?t=174043)
- Thread-safe Remote Script with 220 tools (queue-based dispatch): [github.com/Ziforge/ableton-liveapi-tools](https://github.com/Ziforge/ableton-liveapi-tools)
- FastMCP modular tools discussion: [github.com/jlowin/fastmcp/discussions/948](https://github.com/jlowin/fastmcp/discussions/948)

---
*Architecture research for: Ableton MCP Server (comprehensive coverage)*
*Researched: 2026-03-10*
