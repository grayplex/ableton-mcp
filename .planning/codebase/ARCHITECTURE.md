# Architecture

**Analysis Date:** 2026-04-01

## Pattern Overview

**Overall:** Two-tier bridge architecture — MCP Server (Python process) ↔ Remote Script (Ableton Live plugin)

**Key Characteristics:**
- MCP Server runs as a standalone async Python process; Remote Script runs inside Ableton's Python runtime
- All communication crosses a TCP socket boundary on `localhost:9877` using a length-prefix framing protocol
- MCP Server owns all intelligence (music theory, genre blueprints, orchestration logic); Remote Script is a thin command executor
- Write commands (state-mutating) are dispatched to Ableton's main thread via `schedule_message`; read commands run directly on the socket thread
- Tools register themselves at import time via `@mcp.tool()` decorators; RS handlers register via `@command()` decorators

---

## Tiers

### Tier 1 — MCP Server (`MCP_Server/`)

**Purpose:** Exposes MCP tools to an AI client (Claude). Contains all business logic, pure-computation libraries, and socket-based communication with Ableton.

**Entry point:** `MCP_Server/server.py` — creates a `FastMCP("AbletonMCP")` instance with a lifespan context manager that opens/closes the Ableton socket connection. On startup it imports `MCP_Server.tools` which triggers all `@mcp.tool()` registrations.

**Layers inside MCP Server:**

- **`MCP_Server/connection.py`** — Socket lifecycle, connection pooling, timeout dispatch, error formatting. Exposes `get_ableton_connection()` (thread-safe, with ping-based liveness test and 3-attempt reconnect). The global `_ableton_connection` is protected by `threading.Lock`.
- **`MCP_Server/protocol.py`** — Length-prefix framing: `send_message` / `recv_message` over raw TCP. 4-byte big-endian length header + UTF-8 JSON payload. 10MB safety limit.
- **`MCP_Server/tools/`** — All MCP tool functions. Each module uses `@mcp.tool()` decorators. Tools call `get_ableton_connection().send_command(...)` for live state; pure-computation tools call domain libraries directly.
- **Domain libraries** (`theory/`, `genres/`, `sounds/`, `mixing/`, `evaluation/`, `prompt/`, `refinement/`, `orchestration/`, `devices/`) — Stateless pure-Python libraries. No socket calls except `orchestration/checkpoint.py` and `orchestration/next_actions.py`.

### Tier 2 — Remote Script (`AbletonMCP_Remote_Script/`)

**Purpose:** Ableton Live control surface plugin. Runs a TCP server inside Live's Python runtime. Receives JSON commands, executes them against Live Object Model (LOM), returns JSON responses.

**Entry point:** `AbletonMCP_Remote_Script/__init__.py` → `create_instance(c_instance)` → `AbletonMCP(c_instance)`. `AbletonMCP` inherits from `ControlSurface` and all handler mixin classes.

**Layers inside Remote Script:**

- **`AbletonMCP_Remote_Script/__init__.py`** — Socket server lifecycle, client accept loop (daemon thread), client handler loop, command dispatch. Owns `_read_commands` and `_write_commands` dispatch dicts built at init time.
- **`AbletonMCP_Remote_Script/registry.py`** — `CommandRegistry` class. `@command(name, write=False, self_scheduling=False)` decorator records `(cmd_name, method_name, is_write, is_self_scheduling)` tuples at import time. `build_tables(instance)` binds handlers to the live instance and returns dispatch dicts.
- **`AbletonMCP_Remote_Script/handlers/`** — 14 mixin classes, one per domain. Each defines methods decorated with `@command(...)`. All become methods of `AbletonMCP` via multiple inheritance.

---

## Communication Protocol

**Transport:** TCP socket, `localhost:9877`

**Framing:** Length-prefix (implemented identically in both tiers):
```
[4-byte big-endian uint32: payload length][UTF-8 JSON payload]
```

**Request shape (MCP Server to RS):**
```json
{"type": "command_name", "params": {"key": "value"}}
```

**Response shape (RS to MCP Server):**
```json
{"status": "success", "result": {...}}
{"status": "error", "message": "error description"}
```

**Timeouts** (defined in `MCP_Server/connection.py`):
- Read commands: 10.0s (`TIMEOUT_READ`)
- Write commands: 15.0s (`TIMEOUT_WRITE`)
- Browser/load commands: 30.0s (`TIMEOUT_BROWSER`)
- Ping: 5.0s (`TIMEOUT_PING`)

---

## Threading Model

### MCP Server side
- FastMCP runs async (asyncio event loop). Tool functions are called from async context.
- `get_ableton_connection()` is synchronous and protected by `threading.Lock` — safe for concurrent tool calls.
- Each `send_command()` call is synchronous: sends, then blocks on `recv_message()` until response arrives.

### Remote Script side
- Main Ableton thread: handles Live Object Model mutations. Must be used for all write operations.
- Socket server thread (daemon): accepts connections in `_server_thread()`.
- Per-client handler thread (daemon): `_handle_client()` — reads commands, dispatches them.
- **Read commands** run directly on the client handler thread (LOM reads are thread-safe in Ableton's runtime).
- **Write commands** use `queue.Queue` + `schedule_message(0, task)` to marshal execution onto Ableton's main thread. The handler thread blocks on `response_queue.get(timeout=10.0)`.
- **Self-scheduling commands** (e.g., `load_browser_item`) manage their own `schedule_message` chains and run directly without the queue.

---

## Data Flow: Typical Tool Call

1. AI client calls MCP tool (e.g., `create_midi_track`).
2. `MCP_Server/tools/tracks.py` receives call, builds params dict.
3. Calls `get_ableton_connection()` — acquires lock, returns (or creates) persistent socket connection.
4. Calls `connection.send_command("create_midi_track", params)`.
5. `MCP_Server/protocol.py` serializes `{"type": ..., "params": ...}` to length-prefixed bytes and sends.
6. RS client handler thread receives, deserializes, looks up `"create_midi_track"` in `_write_commands`.
7. Handler is a write command — `_dispatch_write_command` puts a task on `response_queue`, calls `schedule_message(0, main_thread_task)`.
8. Ableton main thread executes `TrackHandlers._create_midi_track(params)`, mutates LOM, puts result on queue.
9. Client handler thread unblocks from `response_queue.get()`, sends `{"status": "success", "result": {...}}`.
10. MCP Server `recv_message()` deserializes response, returns `result` dict to tool function.
11. Tool function formats result as JSON string and returns to AI client.

---

## Data Flow: Orchestration Tool Call

### Pure-computation path (no Ableton connection required)

`get_production_agenda` and `get_phase_execution_plan`:
1. AI client calls tool in `MCP_Server/tools/orchestration.py`.
2. Tool calls `MCP_Server/orchestration/agenda.py` or `execution.py`.
3. Module reads from `MCP_Server/genres/catalog.py` (genre blueprint data), computes result.
4. Returns JSON string directly — no RS involvement.

### Live-state path (requires Ableton connection)

`get_production_checkpoint` and `get_phase_transition_guidance`:
1. Tool calls `MCP_Server/orchestration/checkpoint.py` or `next_actions.py`.
2. These modules call `get_ableton_connection()` and issue multiple RS commands: `get_arrangement_state`, `get_mix_state`, `get_arrangement_clips` (up to 8 tracks).
3. Infer phase completion from track names + device class names + clip presence heuristics.
4. Return `ProductionCheckpoint` TypedDict serialized as JSON.

`get_next_actions` checks whether `phase_name` was explicitly provided:
- If yes: pure-computation (calls `get_execution_plan` only).
- If no: reads checkpoint first, then builds step list from active phase.

---

## Orchestration Package (`MCP_Server/orchestration/`)

Added in v1.9 (phases 48–51). Five modules forming the production guidance system:

| Module | RS calls? | Purpose |
|---|---|---|
| `schema.py` | No | TypedDict definitions: `ProductionPhase`, `ProductionAgenda`, `ExecutionStep`, `PhaseChecklist`, `ProductionCheckpoint`, `SessionStats` |
| `agenda.py` | No | `AGENDA_CATALOG` (12 genres to phase orderings) + `get_agenda()` |
| `execution.py` | No | `get_execution_plan()` — concrete step lists with exact tool names, genre-appropriate MIDI patterns, sentinel args |
| `checkpoint.py` | Yes | `get_checkpoint()` — reads live Ableton state, infers completed phases |
| `next_actions.py` | Yes (optional) | `get_next_actions_result()` + `get_transition_guidance()` — reads checkpoint, returns next steps; falls back to setup checklist if no live connection |

The 5 MCP tools wrapping these are in `MCP_Server/tools/orchestration.py`:
- `get_production_agenda`
- `get_phase_execution_plan`
- `get_production_checkpoint`
- `get_next_actions`
- `get_phase_transition_guidance`

---

## Domain Library Organization

All domain libraries live under `MCP_Server/` and are stateless pure computation (no socket calls, no side effects), except where noted:

| Package | Purpose | Key dependency |
|---|---|---|
| `theory/` | Music theory: chords, scales, progressions, analysis, voice leading, rhythm | `music21` |
| `genres/` | Genre blueprints: BPM ranges, scales, instrumentation roles, arrangement templates for 12 genres | None |
| `sounds/` | Instrument profiles: sonic descriptors, browser paths, recommendation engine | None |
| `mixing/` | Mix recipes: role x genre device parameter tables | `devices/` |
| `devices/` | Device parameter catalog + normalization/denormalization between natural and 0.0–1.0 units | None |
| `evaluation/` | Session quality evaluators: arrangement, harmonic, mix balance, sounds coverage | `genres/`, `theory/` |
| `prompt/` | Prompt interpretation: `classify_prompt`, `derive` → `ProductionBrief` | `genres/`, `theory/` |
| `refinement/` | Section state reader, iterative refinement plan builder | `prompt/`, `mixing/` |
| `orchestration/` | Production agenda, execution plans, checkpoint inference, next-action recommendations | `genres/`; `checkpoint.py` and `next_actions.py` call RS |

---

## Handler Registration Patterns

### Remote Script handler registration
```python
# AbletonMCP_Remote_Script/registry.py — decorator records at import time
@command("create_midi_track", write=True)
def _create_midi_track(self, params):
    ...

# At AbletonMCP.__init__ time:
self._read_commands, self._write_commands, self._self_scheduling = (
    CommandRegistry.build_tables(self)
)
```

### MCP Server tool registration
```python
# MCP_Server/server.py — mcp created first, then tools imported
mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)
import MCP_Server.tools  # triggers all @mcp.tool() registrations

# In any tool module:
from MCP_Server.server import mcp

@mcp.tool()
def create_midi_track(ctx: Context, index: int = -1) -> str:
    ...
```

The `MCP_Server/tools/__init__.py` imports all 28 tool modules explicitly, ensuring all `@mcp.tool()` calls run before `main()` starts serving.

---

## Error Handling

**MCP Server tools:**
- Wrap `get_ableton_connection()` and `send_command()` in try/except.
- Return `format_error(message, detail, suggestion)` as a plain string on failure.
- `format_error` (in `connection.py`) produces AI-friendly output: `"Error: ...\nSuggestion: ...\nDebug: ..."`.

**Connection layer:**
- Socket errors (`ConnectionError`, `BrokenPipeError`, `TimeoutError`) set `self.sock = None`, causing the next call to reconnect.
- `get_ableton_connection()` retries 3 times with 1s delay, validates with `get_session_info` after connect.

**Remote Script:**
- `_handle_client` catches all exceptions per-command and sends `{"status": "error", "message": str(e)}` to preserve the connection.
- Write commands: if `schedule_message` raises `AssertionError` (not on main thread), falls back to direct call.
- `_dispatch_write_command` uses 30s timeout for self-scheduling commands, 10s for standard write commands.

---

## Cross-Cutting Concerns

**Logging:** `logging.getLogger("AbletonMCPServer")` used throughout MCP Server. RS uses `self.log_message(...)` (Ableton's built-in logger to Live's log file).

**Validation:** Tool layer validates inputs — range checks, genre resolution via `resolve_alias()` (in `genres/catalog.py`). RS handlers validate LOM object existence (track index bounds, clip slot existence).

**Authentication:** None. Single-tenant local socket — accepted only from `localhost`.

**State:** No server-side state beyond the single persistent TCP socket. All Ableton session state lives in the LOM and is queried per-request.

---

*Architecture analysis: 2026-04-01*
