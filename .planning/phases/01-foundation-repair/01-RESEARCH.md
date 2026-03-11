# Phase 1: Foundation Repair - Research

**Researched:** 2026-03-10
**Domain:** Python socket protocol repair, thread safety, error handling, Python 2 cleanup
**Confidence:** HIGH

## Summary

Phase 1 addresses six foundational correctness bugs that make the existing MCP server unreliable: Python 2 dead code, bare exception swallowing, O(n^2) JSON parsing, thread-unsafe global connection, broken instrument loading, and a missing dict-based command router. The codebase is two files -- `MCP_Server/server.py` (660 lines, 15 MCP tools) and `AbletonMCP_Remote_Script/__init__.py` (820+ lines, monolithic ControlSurface subclass). Both files will be modified in place; no new files are created in this phase (modular extraction is Phase 2).

The critical technical insight is that ALL changes to the socket protocol (length-prefix framing) must be deployed to BOTH sides simultaneously -- the MCP server and the Remote Script speak the same wire format, so a half-upgrade breaks everything. The second critical insight is that the instrument loading fix requires `selected_track` assignment and `browser.load_item()` to execute in the SAME `schedule_message` callback -- splitting them across ticks causes a race condition.

**Primary recommendation:** Implement changes in dependency order: (1) strip Python 2 code, (2) replace bare excepts with specific handlers, (3) add length-prefix framing to both sides simultaneously, (4) add threading.Lock to global connection, (5) fix instrument loading with same-callback pattern + verification, (6) replace if/elif dispatch with dict router. Add a health-check/ping tool as the final deliverable.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Error reporting: Clean message first, technical detail in a debug section below -- gives AI both actionable info and diagnostic context
- Include suggested fixes in error messages (e.g., "Connection lost. Ensure Ableton is running and Remote Script is loaded.")
- Normalize Ableton error messages into consistent format while preserving the original message
- Load results must report what device was actually loaded: "Loaded 'Analog' on track 3 (device chain: Analog, Reverb)"
- One automatic retry on load failure before reporting error
- Auto-reconnect silently on next tool call when connection drops mid-session -- seamless for AI
- Add a health-check/ping tool in Phase 1 that reports connection state, Ableton version, and basic session info
- Keep snake_case naming convention for all tools
- Minimal browser tool fix in Phase 1 -- fix typo and loading only, defer browser API redesign to Phase 7
- Health-check tool belongs in Phase 1 as a foundation concern
- Fix the 'nstruments' typo AND add basic browser path caching to prevent UI freezes on large libraries
- User is "hands-off" on the Remote Script side -- they want it to work but don't want to think about the internals
- Error messages should be useful to an AI assistant, not a human -- technical detail is valuable

### Claude's Discretion
- Response metadata format (structured JSON vs simple strings) -- pick what works best per tool
- Instrument load verification strategy (device count vs name match vs both)
- Initial connection attempt strategy (fail fast vs retry with delay)
- Whether to consolidate load_instrument_or_effect + load_drum_kit into one tool or keep separate
- Ableton error normalization approach (passthrough with wrapper vs full normalization)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FNDN-01 | Server runs on Python 3 only -- all Python 2 compatibility code removed | Strip `from __future__` (line 1), `try: import Queue as queue` (lines 12-15), `decode()` try/except blocks (lines 142-147, 167-172), old-style `ControlSurface.__init__(self, c_instance)` |
| FNDN-02 | Remote Script uses Python 3.11 idioms (super(), f-strings, type hints, queue module) | Replace `ControlSurface.__init__(self, c_instance)` with `super().__init__(c_instance)`, string concatenation with f-strings, add type hints to public methods, direct `import queue` |
| FNDN-03 | Socket protocol uses length-prefix framing instead of JSON-completeness parsing | Replace `receive_full_response()` O(n^2) parser with `struct.pack(">I", len(payload))` prefix on both sides; must upgrade MCP server AND Remote Script simultaneously |
| FNDN-04 | Global connection protected by threading.Lock for concurrent tool invocations | Wrap `_ableton_connection` global with `threading.Lock()`; protect all reads/writes in `get_ableton_connection()` and `send_command()` |
| FNDN-05 | All error handling uses specific exception types -- no bare except:pass blocks | Replace 5 bare `except: pass` blocks (Remote Script lines 59, 194, 206, 820; server.py line 211) with `except Exception as e:` + logging |
| FNDN-06 | Remote Script command dispatch uses dict-based router instead of if/elif chain | Replace `_process_command()` if/elif chain with `dict[str, callable]` lookup table; each entry maps command type string to handler method |
</phase_requirements>

## Standard Stack

### Core (no new dependencies -- all stdlib + existing)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `struct` | stdlib | Length-prefix framing (pack/unpack 4-byte big-endian length headers) | Standard approach for binary-framed protocols; eliminates O(n^2) JSON re-parsing |
| `threading.Lock` | stdlib | Protect global `_ableton_connection` from concurrent access | Simplest correct synchronization primitive for a shared singleton |
| `queue` | stdlib (Python 3) | Replace `Queue as queue` compat hack; main-thread response passing | Direct import -- no compatibility layer needed on Python 3.11 |
| `traceback` | stdlib | Format exception tracebacks for error reporting debug sections | Already imported in Remote Script; use consistently |
| `logging` | stdlib | Structured error logging in both server and Remote Script | Already in use on server side; Remote Script uses `self.log_message()` which wraps Ableton's logger |

### Supporting (already present)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `mcp[cli]` | 1.26.0 | FastMCP framework -- `@mcp.tool()` decorators, lifespan, MCP transport | All tool definitions; no version change needed for Phase 1 |
| `json` | stdlib | Command serialization over socket protocol | Payload encoding/decoding (inside the length-prefix frame) |
| `socket` | stdlib | TCP communication MCP server <-> Remote Script | Connection management in `AbletonConnection` and Remote Script server |
| `dataclasses` | stdlib | `AbletonConnection` dataclass | Keep existing pattern; add Lock field |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `struct.pack(">I")` length prefix | Newline-delimited JSON (`\n` separator) | Simpler but breaks if JSON payload contains literal newlines in strings; length-prefix is unambiguous |
| `threading.Lock` | `asyncio.Lock` | MCP tools run in async context but socket ops are sync; `threading.Lock` is correct for sync socket code called from async wrappers |
| Dict-based command router | Match/case (Python 3.10+) | Match/case is syntactically heavier for string dispatch; dict lookup is O(1) and more extensible |

**Installation:** No new packages needed. All changes use stdlib modules already available in both Python 3.11 (Remote Script) and the MCP server environment.

## Architecture Patterns

### Recommended Changes (Phase 1 scope -- NO new files)

```
MCP_Server/
  server.py              # MODIFY: length-prefix framing, threading.Lock, error normalization,
                         #         health-check tool, instrument load retry + verification

AbletonMCP_Remote_Script/
  __init__.py            # MODIFY: strip Py2 code, length-prefix framing, dict router,
                         #         replace bare excepts, fix 'nstruments' typo,
                         #         same-callback instrument loading, browser path cache
```

Phase 2 extracts into `tools/` and `handlers/` packages. Phase 1 keeps the monolithic files to minimize risk.

### Pattern 1: Length-Prefix Framing Protocol

**What:** Every JSON message is preceded by a 4-byte big-endian unsigned integer indicating the payload length in bytes. The receiver reads exactly 4 bytes, unpacks the length, then reads exactly that many bytes.

**When to use:** All socket communication between MCP server and Remote Script.

**CRITICAL:** Both sides MUST be upgraded simultaneously. A length-prefix sender talking to a JSON-completeness receiver will break immediately.

**Example (sender -- both sides use identical logic):**
```python
import struct
import json

def send_message(sock: socket.socket, data: dict) -> None:
    """Send a length-prefixed JSON message."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)

def recv_message(sock: socket.socket, timeout: float = 15.0) -> dict:
    """Receive a length-prefixed JSON message."""
    sock.settimeout(timeout)
    # Read exactly 4 bytes for the length header
    header = _recv_exact(sock, 4)
    if not header:
        raise ConnectionError("Connection closed while reading header")
    length = struct.unpack(">I", header)[0]
    if length > 10 * 1024 * 1024:  # 10MB safety limit
        raise ValueError(f"Message too large: {length} bytes")
    # Read exactly `length` bytes for the payload
    payload = _recv_exact(sock, length)
    if not payload:
        raise ConnectionError("Connection closed while reading payload")
    return json.loads(payload.decode("utf-8"))

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """Read exactly n bytes from socket."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)
```

### Pattern 2: Thread-Safe Connection Singleton

**What:** Wrap `_ableton_connection` access with a `threading.Lock`. The lock is held during connection creation/validation and during the entire `send_command` cycle (send + receive) to prevent interleaving.

**When to use:** Every access to `_ableton_connection` in `server.py`.

**Example:**
```python
import threading

_connection_lock = threading.Lock()
_ableton_connection: AbletonConnection | None = None

def get_ableton_connection() -> AbletonConnection:
    global _ableton_connection
    with _connection_lock:
        if _ableton_connection is not None:
            try:
                # Validate with lightweight ping
                _ableton_connection.send_command("ping")
                return _ableton_connection
            except Exception:
                _ableton_connection.disconnect()
                _ableton_connection = None
        # Create new connection (retry logic here)
        _ableton_connection = _create_connection()
        return _ableton_connection
```

**Note on concurrency:** With the lock held during `send_command`, concurrent tool calls are serialized. This is correct for Phase 1 -- the Remote Script handles one command at a time anyway. A connection pool is a Phase 2+ concern.

### Pattern 3: Same-Callback Instrument Loading

**What:** The `selected_track` assignment and `browser.load_item()` call MUST execute inside one `schedule_message` callback to prevent the race condition where the UI selection changes between ticks.

**When to use:** `_load_browser_item` handler in the Remote Script.

**Example:**
```python
def _load_browser_item(self, params):
    response_queue = queue.Queue()

    def do_load():
        try:
            track_index = params.get("track_index", 0)
            item_uri = params.get("item_uri", "")
            track = list(self._song.tracks)[track_index]

            # Count devices BEFORE loading
            devices_before = len(track.devices)

            # Set selection AND load in the SAME callback
            self._song.view.selected_track = track

            item = self._find_browser_item_by_uri(item_uri)
            if item is None:
                response_queue.put({"status": "error", "message": f"Browser item not found: {item_uri}"})
                return

            app = self.application()
            app.browser.load_item(item)

            # Schedule verification on next tick
            self.schedule_message(1, lambda: self._verify_load(
                track, devices_before, item_uri, response_queue, retries=1
            ))
        except Exception as e:
            response_queue.put({"status": "error", "message": str(e)})

    self.schedule_message(0, do_load)
    return response_queue.get(timeout=30.0)  # Longer timeout for browser ops

def _verify_load(self, track, devices_before, uri, response_queue, retries):
    devices_after = len(track.devices)
    if devices_after > devices_before:
        device_names = [d.name for d in track.devices]
        response_queue.put({
            "status": "success",
            "result": {
                "loaded": True,
                "devices": device_names,
                "new_device_count": devices_after - devices_before
            }
        })
    elif retries > 0:
        # One automatic retry -- re-attempt load
        self.schedule_message(1, lambda: self._retry_load(
            track, uri, response_queue
        ))
    else:
        response_queue.put({
            "status": "error",
            "message": f"Device did not appear after loading '{uri}'. Track has {devices_after} devices."
        })
```

### Pattern 4: Dict-Based Command Router

**What:** Replace the `_process_command` if/elif chain with a dictionary mapping command type strings to handler methods.

**When to use:** All command dispatch in the Remote Script.

**Example:**
```python
def _build_command_table(self):
    """Build command dispatch table. Called once at init."""
    self._commands = {
        # Read commands (can run on socket thread via schedule_message)
        "get_session_info": self._get_session_info,
        "get_track_info": self._get_track_info,
        "get_browser_tree": self._get_browser_tree,
        "get_browser_items_at_path": self._get_browser_items_at_path,
        "ping": self._ping,
        # Write commands
        "create_midi_track": self._create_midi_track,
        "create_audio_track": self._create_audio_track,
        "set_track_name": self._set_track_name,
        "create_clip": self._create_clip,
        "add_notes_to_clip": self._add_notes_to_clip,
        "set_clip_name": self._set_clip_name,
        "set_tempo": self._set_tempo,
        "fire_clip": self._fire_clip,
        "stop_clip": self._stop_clip,
        "start_playback": self._start_playback,
        "stop_playback": self._stop_playback,
        "load_browser_item": self._load_browser_item,
        "set_device_parameter": self._set_device_parameter,
    }

def _process_command(self, command_type, params):
    handler = self._commands.get(command_type)
    if handler is None:
        return {"status": "error", "message": f"Unknown command: {command_type}"}
    return handler(params)
```

### Pattern 5: Error Response Format (AI-friendly)

**What:** Structured error responses with clean message, debug detail, and suggested fix.

**When to use:** All error responses from MCP tools back to Claude.

**Example:**
```python
def format_error(message: str, detail: str = "", suggestion: str = "") -> str:
    """Format error for AI consumption."""
    parts = [f"Error: {message}"]
    if suggestion:
        parts.append(f"Suggestion: {suggestion}")
    if detail:
        parts.append(f"Debug: {detail}")
    return "\n".join(parts)

# Usage in a tool:
return format_error(
    "Failed to load instrument on track 3",
    detail=f"browser.load_item raised: {e}\nTrack devices: {devices}",
    suggestion="Verify the URI is valid using get_browser_items_at_path first"
)
```

### Anti-Patterns to Avoid

- **Split schedule_message calls for load_item:** NEVER set `selected_track` in one callback and call `load_item` in another. They MUST be in the same tick.
- **Bare except: pass:** NEVER catch all exceptions silently. Always use `except Exception as e:` with logging at minimum.
- **time.sleep() for synchronization:** NEVER use sleep to "wait for Ableton." Use `schedule_message` + `queue.Queue` for correct timing.
- **Empty-byte connection ping:** NEVER use `sock.sendall(b'')` to test connection liveness. It proves nothing. Use a real `ping` command.
- **Partial protocol upgrade:** NEVER upgrade only one side of the socket protocol. Both MCP server and Remote Script MUST switch to length-prefix framing in the same commit.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Message framing | Custom delimiter parsing / JSON re-parsing | `struct.pack(">I", len(payload))` length prefix | The current O(n^2) approach re-parses all accumulated bytes on every chunk. Length-prefix is the standard solution -- zero ambiguity, O(n) reads |
| Thread synchronization | Manual flag checking / boolean guards | `threading.Lock` context manager (`with lock:`) | Lock is reentrant-safe with context manager, handles exceptions correctly, well-understood semantics |
| Main-thread dispatch | Custom event loop / threading.Event | `self.schedule_message(0, callback)` + `queue.Queue` | This is Ableton's official mechanism. Fighting it causes crashes. |
| JSON encoding | Manual string building | `json.dumps(data, ensure_ascii=False)` | Already in use; ensure_ascii=False allows Unicode instrument names |
| Connection retry | Manual counter + sleep loop | Keep existing retry-3-times pattern but add Lock protection | The pattern is fine; it just needs thread safety |

## Common Pitfalls

### Pitfall 1: Race Condition in Instrument Loading
**What goes wrong:** `selected_track` set in one `schedule_message` tick, `load_item` fires in the next. Between ticks, the user (or another tool call) changes the UI selection. Instrument loads on wrong track -- silent failure, no sound.
**Why it happens:** `browser.load_item` always targets Ableton's UI-selected track, not a parameter.
**How to avoid:** Both operations in ONE callback. Verify device count increased after loading.
**Warning signs:** Tool reports "loaded" but `track.devices` is empty. Instrument appears on a different track.

### Pitfall 2: Protocol Upgrade Must Be Atomic
**What goes wrong:** MCP server sends length-prefixed messages but Remote Script still expects raw JSON. First 4 bytes are interpreted as the start of a JSON string, parse fails silently, connection drops.
**Why it happens:** Two separate codebases for the two sides. Easy to update one and forget the other.
**How to avoid:** Implement length-prefix send AND receive on both sides in the same commit/deployment. Test both directions.
**Warning signs:** "Invalid JSON" errors immediately after protocol change. Connection drops on first command.

### Pitfall 3: Lock Contention Causing Timeouts
**What goes wrong:** `threading.Lock` held during entire `send_command` (send + receive). If a browser tree traversal takes 10+ seconds, all other tool calls queue behind it and time out.
**Why it happens:** Single lock serializes all operations. Browser operations are slow due to Live API tree traversal.
**How to avoid:** Accept serialization for Phase 1 (correctness first). Add the browser path cache as documented in CONTEXT.md to reduce traversal time. Increase queue timeout to 30s for browser operations.
**Warning signs:** Non-browser tool calls failing with timeout when a browser operation is in flight.

### Pitfall 4: schedule_message Timeout vs Actual Completion
**What goes wrong:** `queue.get(timeout=10)` fires before the `schedule_message` callback executes. The callback eventually completes successfully, but the error response has already been sent.
**Why it happens:** `schedule_message(0, fn)` defers to next display tick (~100ms usually, but can be seconds if Ableton is under load).
**How to avoid:** Use 30-second timeout for browser/loading operations. After timeout, check actual state before reporting failure.
**Warning signs:** "Timeout" errors followed by successful state in Ableton on next query.

### Pitfall 5: Python 2 Code Removal Breaking Active Code Paths
**What goes wrong:** Removing `from __future__` or the Queue compat block is straightforward, but the `buffer = ''` (string) vs `buffer = b''` (bytes) distinction throughout `_handle_client` requires careful audit. Missing a single string/bytes conversion crashes the socket handler.
**Why it happens:** The current code has mixed string/bytes handling because of Python 2 compatibility. Some paths use `str`, some use `bytes`, some try/except between them.
**How to avoid:** Audit ALL buffer operations in `_handle_client`. Socket operations ALWAYS produce/consume `bytes`. Use `bytearray` for accumulation buffers. Decode to `str` only at JSON parse boundary.
**Warning signs:** `TypeError: a bytes-like object is required` or `TypeError: can't concat str to bytes` after cleanup.

### Pitfall 6: Bare Except Removal Revealing Hidden Bugs
**What goes wrong:** Replacing `except: pass` with `except Exception as e: log(e)` suddenly surfaces errors that were silently swallowed. One of those errors might be a real bug that crashes the Remote Script.
**Why it happens:** The bare excepts were hiding real problems (e.g., `AttributeError` when accessing `app.browser` before Ableton is fully loaded).
**How to avoid:** Replace bare excepts with `except Exception as e: self.log_message(f"[ERROR] {e}")` first. Read the logs. Fix any newly-visible bugs before moving on.
**Warning signs:** Ableton Log.txt suddenly full of errors after the cleanup. Remote Script crashes on startup.

## Code Examples

### Example 1: Python 2 Code to Remove (Remote Script __init__.py)

```python
# REMOVE -- line 1:
from __future__ import absolute_import, print_function, unicode_literals

# REMOVE -- lines 12-15:
try:
    import Queue as queue  # Python 2
except ImportError:
    import queue  # Python 3

# REPLACE WITH:
import queue

# REPLACE -- line 30:
# OLD: ControlSurface.__init__(self, c_instance)
# NEW:
super().__init__(c_instance)

# REPLACE -- lines ~142-147, ~167-172 (decode try/except):
# OLD:
# try:
#     data = data.decode('utf-8')
# except (UnicodeDecodeError, AttributeError):
#     pass
# NEW:
data = data.decode('utf-8')  # socket.recv always returns bytes in Python 3
```

### Example 2: Replace Bare Except Blocks

```python
# OLD (line 59 in __init__.py):
except:
    pass

# NEW:
except Exception as e:
    self.log_message(f"[ERROR] Unexpected error in server accept loop: {e}")

# OLD (line 211 in server.py):
except:
    pass

# NEW:
except Exception as e:
    logger.warning(f"Error during connection cleanup: {e}")
```

### Example 3: Fix 'nstruments' Typo + Basic Cache

```python
# OLD (line 675 in __init__.py):
if path_parts[0].lower() == "nstruments":

# NEW -- dict-based category mapping with cache:
_CATEGORY_MAP = {
    "instruments": "instruments",
    "sounds": "sounds",
    "drums": "drums",
    "audio_effects": "audio_effects",
    "midi_effects": "midi_effects",
    "max_for_live": "max_for_live",
    "plug_ins": "plug_ins",
    "clips": "clips",
    "samples": "samples",
    "packs": "packs",
}

# Basic path cache (cleared on disconnect):
self._browser_path_cache = {}

def _get_browser_item(self, params):
    path = params.get("path", "")
    if path in self._browser_path_cache:
        return self._browser_path_cache[path]
    # ... resolve path using _CATEGORY_MAP ...
    self._browser_path_cache[path] = result
    return result
```

### Example 4: Health-Check / Ping Tool

```python
# MCP_Server/server.py -- new tool
@mcp.tool()
def get_connection_status(ctx: Context) -> str:
    """Check connection health and get Ableton session summary.
    Returns connection state, Ableton version, and basic session info.
    Use this to verify the connection before starting work."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("ping")
        session = ableton.send_command("get_session_info")
        return json.dumps({
            "connected": True,
            "ableton_version": session.get("version", "unknown"),
            "tempo": session.get("tempo"),
            "track_count": session.get("track_count"),
            "scene_count": session.get("scene_count"),
        }, indent=2)
    except Exception as e:
        return format_error(
            "Cannot reach Ableton",
            detail=str(e),
            suggestion="Ensure Ableton is running and Remote Script is loaded in Preferences > Link/Tempo/MIDI"
        )

# Remote Script -- ping handler (minimal, for connection validation)
def _ping(self, params):
    return {"status": "success", "result": {"pong": True}}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python 2/3 compat (`from __future__`, Queue hack) | Python 3 only | Ableton Live 12 (2023) ships Python 3.11 | Remove all compat code -- zero Python 2 users exist |
| JSON-completeness parsing (re-parse every chunk) | Length-prefix framing (`struct.pack(">I")`) | Standard practice for TCP protocols | Eliminates O(n^2) parsing, handles large payloads correctly |
| if/elif command dispatch | Dict-based dispatch table | Standard refactoring pattern | O(1) lookup, one-line-per-command extensibility |
| `sendall(b'')` connection test | Real ping command with response | Always was wrong; empty send proves nothing | Reliable connection health detection |
| `ControlSurface.__init__(self, c_instance)` | `super().__init__(c_instance)` | Python 3 MRO is standard | Cleaner, handles multiple inheritance correctly |

**Deprecated/outdated:**
- `from __future__ import absolute_import, print_function, unicode_literals`: No-ops in Python 3. Delete.
- `try: import Queue as queue`: Dead code path. Python 3 is `import queue` directly.
- `data.decode('utf-8')` wrapped in try/except AttributeError: `socket.recv()` always returns `bytes` in Python 3. No AttributeError possible.

## Open Questions

1. **Consolidate load_instrument_or_effect + load_drum_kit?**
   - What we know: Both call `load_browser_item` on the Remote Script. `load_drum_kit` is a two-step operation (load rack, then load kit).
   - What's unclear: Whether consolidation simplifies or complicates the API for Claude.
   - Recommendation: Keep separate for Phase 1 (less risk). The planner can decide based on implementation complexity. Both benefit from the same-callback fix.

2. **Browser path cache invalidation**
   - What we know: Browser content does not change during a session. Cache is safe to hold until disconnect.
   - What's unclear: Whether `disconnect()` is reliably called when the Remote Script reloads.
   - Recommendation: Clear cache in `disconnect()` AND on any `KeyError`/`AttributeError` during cache lookup (stale reference).

3. **Exact timeout values for browser operations**
   - What we know: 10 seconds is too short for browser tree traversal on large libraries. 30 seconds was suggested in pitfalls research.
   - What's unclear: Real-world timing on the user's specific Ableton installation.
   - Recommendation: Use 30 seconds for browser/load operations, 15 seconds for other write operations, 10 seconds for reads. Make these named constants at module level.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.25+ |
| Config file | none -- Wave 0 must add `[tool.pytest.ini_options]` to `pyproject.toml` |
| Quick run command | `uv run pytest tests/ -x --timeout=10` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FNDN-01 | No Python 2 imports in codebase | unit (grep-based) | `uv run pytest tests/test_python3_cleanup.py -x` | No -- Wave 0 |
| FNDN-02 | Python 3.11 idioms used (super, f-strings, queue) | unit (AST/grep) | `uv run pytest tests/test_python3_cleanup.py -x` | No -- Wave 0 |
| FNDN-03 | Length-prefix framing send/receive roundtrip | unit | `uv run pytest tests/test_protocol.py -x` | No -- Wave 0 |
| FNDN-04 | Concurrent connection access does not crash | unit (threading) | `uv run pytest tests/test_connection.py -x` | No -- Wave 0 |
| FNDN-05 | No bare except: blocks in codebase | unit (grep-based) | `uv run pytest tests/test_python3_cleanup.py::test_no_bare_excepts -x` | No -- Wave 0 |
| FNDN-06 | Dict router dispatches known commands, rejects unknown | unit | `uv run pytest tests/test_dispatch.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x --timeout=10`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `pyproject.toml` -- add `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`
- [ ] `tests/__init__.py` -- empty init for test package
- [ ] `tests/conftest.py` -- shared fixtures (mock socket, mock Ableton connection)
- [ ] `tests/test_python3_cleanup.py` -- grep-based tests for FNDN-01, FNDN-02, FNDN-05
- [ ] `tests/test_protocol.py` -- length-prefix framing roundtrip tests for FNDN-03
- [ ] `tests/test_connection.py` -- threading.Lock concurrent access tests for FNDN-04
- [ ] `tests/test_dispatch.py` -- dict router tests for FNDN-06
- [ ] Framework install: `uv add --dev pytest>=8.3 pytest-asyncio>=0.25`

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `MCP_Server/server.py` (660 lines), `AbletonMCP_Remote_Script/__init__.py` (820+ lines) -- all line numbers and code patterns verified by reading the actual files
- `.planning/research/PITFALLS.md` -- 6 critical pitfalls with verified line numbers
- `.planning/research/ARCHITECTURE.md` -- dict dispatch pattern, main-thread decorator pattern, data flow diagrams
- `.planning/research/STACK.md` -- Python 3.11 confirmation, mcp[cli] 1.26.0, stdlib-only Remote Script constraint
- `.planning/codebase/CONCERNS.md` -- race condition in global connection, O(n^2) JSON parsing, bare excepts
- `.planning/codebase/ARCHITECTURE.md` -- current architecture, data flow, error handling tiers

### Secondary (MEDIUM confidence)
- `.planning/phases/01-foundation-repair/01-CONTEXT.md` -- user decisions, implementation constraints
- Python `struct` module documentation -- `pack(">I", n)` for 4-byte big-endian unsigned int
- Ableton Remote Script community patterns (Ziforge/ableton-liveapi-tools) -- queue-based thread safety

### Tertiary (LOW confidence)
- Browser path cache effectiveness -- no benchmarks available; recommendation based on architectural reasoning that browser content is static within a session

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all stdlib, no new dependencies, verified against existing codebase
- Architecture: HIGH -- patterns are well-documented in prior research, line numbers verified in source
- Pitfalls: HIGH -- all 6 pitfalls traced to specific code lines, root causes understood
- Validation: MEDIUM -- test framework not yet set up; test strategy is sound but untested

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable domain -- stdlib and existing codebase)
