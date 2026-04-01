# External Integrations

**Analysis Date:** 2026-04-01

## APIs & External Services

**None (no third-party cloud APIs):**
- The system is entirely local. The only "integration" is between the MCP Server process and Ableton Live running on the same machine.

---

## Ableton Live Integration

**What it is:**
Ableton Live is the DAW being controlled. The `AbletonMCP_Remote_Script` package runs *inside* Ableton as a MIDI Remote Script (loaded from Live's `MIDI Remote Scripts/` directory). It exposes a TCP socket server that the MCP Server connects to.

**Connection:**
- Host: `localhost`
- Port: `9877` (constant `DEFAULT_PORT` in `AbletonMCP_Remote_Script/__init__.py`)
- Transport: TCP (`socket.AF_INET, socket.SOCK_STREAM`)
- Direction: MCP Server is the client; Remote Script is the server
- Persistence: single long-lived connection, re-established on failure (up to 3 retry attempts with 1s delay, validated with `get_session_info` after connect)

**Remote Script framework:**
- Inherits from `_Framework.ControlSurface` (Ableton's internal Python framework, not publicly documented)
- `create_instance(c_instance)` is the Live-required entry point called at script load
- `self.song()` provides access to the Live Object Model (LOM) — the entire session state
- Write commands are dispatched to Ableton's main thread via `self.schedule_message(0, task)` + a `queue.Queue` to get the result back to the socket thread
- Read commands run directly on the socket thread (no main-thread dispatch needed)

**Command dispatch architecture (Remote Script side):**
- `AbletonMCP_Remote_Script/registry.py` - `@command(name, write=bool, self_scheduling=bool)` decorator registers handlers at import time
- `AbletonMCP_Remote_Script/__init__.py` `AbletonMCP` class - inherits from all handler mixins + `ControlSurface`; calls `CommandRegistry.build_tables(self)` to produce `_read_commands` and `_write_commands` dicts
- Handler modules: `handlers/base.py`, `handlers/arrangement.py`, `handlers/audio_clips.py`, `handlers/automation.py`, `handlers/browser.py`, `handlers/clips.py`, `handlers/devices.py`, `handlers/grooves.py`, `handlers/mixer.py`, `handlers/notes.py`, `handlers/routing.py`, `handlers/scaffold.py`, `handlers/scenes.py`, `handlers/tracks.py`, `handlers/transport.py`

**Connection management (MCP Server side):**
- `MCP_Server/connection.py` - `AbletonConnection` dataclass with `send_command(type, params)` method
- Global singleton `_ableton_connection` protected by `threading.Lock`
- Liveness check: sends `ping` command before reusing existing connection
- `get_ableton_connection()` — public API used by all tool modules

---

## MCP Protocol Integration

**What it is:**
The Model Context Protocol (MCP) defines how AI clients (e.g., Claude Desktop, Cursor) discover and invoke tools. The MCP Server exposes all Ableton control capabilities as MCP tools.

**SDK:** `mcp[cli]` 1.4.0 from `mcp.server.fastmcp`

**Server creation:**
```python
# MCP_Server/server.py
mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)
```

**Tool registration pattern:**
```python
# Every tool in MCP_Server/tools/*.py
from MCP_Server.server import mcp
from mcp.server.fastmcp import Context

@mcp.tool()
def tool_name(ctx: Context, param: str) -> str:
    ...
```
All tool modules are imported in `MCP_Server/tools/__init__.py`, which is imported after `mcp` is created in `MCP_Server/server.py` to trigger registration.

**Transport:** `stdio` (default FastMCP transport); `mcp.run()` in `main()` starts the stdio loop

**Entrypoints:**
- CLI: `ableton-mcp` (via `[project.scripts]`)
- Module: `python -m MCP_Server.server`
- Smithery: `python -m MCP_Server.server` (from `smithery.yaml`)
- Docker: `python -m MCP_Server.server` (from `Dockerfile`)

**Lifespan:**
- On startup: attempts Ableton connection, logs warning if not available (server starts regardless)
- On shutdown: calls `shutdown_connection()` to cleanly close the socket

**Tool count (v1.9):**
Tools span 28 modules in `MCP_Server/tools/`. Key tool groups:
- `session.py`: `get_connection_status`, `get_session_info`, `get_session_state`
- `tracks.py`: `create_midi_track`, `create_audio_track`, `delete_track`, `set_track_name`, etc.
- `clips.py`, `notes.py`, `devices.py`, `mixer.py`, `arrangement.py`, `automation.py`, etc.
- `orchestration.py`: 5 new v1.9 tools (see below)
- `evaluation.py`, `analysis.py`, `theory.py`, `sounds.py`, `genres.py`, `mixing.py`, etc.

---

## Socket Wire Protocol

**Protocol:** Length-prefix framing over TCP

**Encoding:**
- Each message = 4-byte big-endian unsigned int header (payload length) + UTF-8 JSON payload
- Maximum message size: 10MB (enforced on receive)
- Defined identically in both `MCP_Server/protocol.py` and `AbletonMCP_Remote_Script/__init__.py`

**Message format (MCP Server → Remote Script):**
```json
{"type": "command_name", "params": {"key": "value"}}
```

**Message format (Remote Script → MCP Server):**
```json
{"status": "success", "result": {...}}
{"status": "error", "message": "error description"}
```

**Timeouts** (`MCP_Server/connection.py`):
| Category | Timeout | Commands |
|----------|---------|----------|
| Ping | 5s | `ping` |
| Read (default) | 10s | `get_*` commands |
| Write | 15s | state-modifying commands |
| Browser | 30s | `get_browser_tree`, `load_instrument_or_effect`, `get_session_state`, `apply_recipe` |

---

## music21 Integration

**What it is:** Open-source music theory and analysis library.

**Package:** `music21` 9.9.1 (declared `>=9.0`)

**Usage pattern:** Lazy-imported to avoid startup cost:
```python
# MCP_Server/theory/analysis.py
def _get_stream_module():
    global _stream_module
    if _stream_module is None:
        from music21 import stream
        _stream_module = stream
    return _stream_module
```

**Used in:**
- `MCP_Server/theory/analysis.py` - key detection, harmonic rhythm analysis using `music21.stream`, `music21.note`
- `MCP_Server/theory/chords.py` - chord identification via music21 pitch objects
- `MCP_Server/theory/progressions.py` - chord progression analysis

**Not used in:** Remote Script (`AbletonMCP_Remote_Script/`) — music21 is MCP Server-only

---

## tiktoken Integration

**What it is:** OpenAI's BPE tokenizer library, used as a dev/test dependency only.

**Package:** `tiktoken` 0.12.0 (dev dependency, declared `>=0.7`)

**Usage:** Exclusively in `tests/test_genre_quality.py`

**Purpose:** Enforces token budget quality gate — genre blueprints must be 400-1200 tokens (cl100k_base encoding) to stay within AI context constraints:
```python
enc = tiktoken.get_encoding("cl100k_base")
token_count = len(enc.encode(json.dumps(blueprint)))
```

**Not imported** in any `MCP_Server/` production code.

---

## v1.9 Orchestration Package (New in v1.9)

**Location:** `MCP_Server/orchestration/`

**Modules:**
- `schema.py` - TypedDicts: `ProductionPhase`, `ProductionAgenda`, `ExecutionStep`, `PhaseChecklist`, `ProductionCheckpoint`, `SessionStats`
- `agenda.py` - `get_agenda(genre, brief)` returns `ProductionAgenda`; `AGENDA_CATALOG` maps 12 genre ids to ordered phase lists
- `execution.py` - `get_execution_plan(phase_name, genre, section_name, context)` returns `PhaseChecklist` with concrete `ExecutionStep` entries (exact tool names, genre-appropriate suggested args, sentinel strings for session-state values)
- `checkpoint.py` - `get_checkpoint(genre)` reads live Ableton state via `get_arrangement_state` + `get_mix_state` + `get_arrangement_clips` commands; infers completed phases from track names/devices/clips
- `next_actions.py` - `get_next_actions_result(genre, phase_name, n)` and `get_transition_guidance(from_phase, genre, to_phase)`

**5 new MCP tools** registered in `MCP_Server/tools/orchestration.py`:

| Tool | Function | Description |
|------|----------|-------------|
| `get_production_agenda` | `agenda.get_agenda` | Ordered phase list for a genre; respects `brief.energy_level` to elevate drums |
| `get_phase_execution_plan` | `execution.get_execution_plan` | Concrete step checklist for one phase; supports session vs. arrangement clip mode |
| `get_production_checkpoint` | `checkpoint.get_checkpoint` | Reads live Ableton state; infers completed/active phases and next steps |
| `get_next_actions` | `next_actions.get_next_actions_result` | Next N tool calls for current phase; falls back to setup if no connection |
| `get_phase_transition_guidance` | `next_actions.get_transition_guidance` | Go/no-go verdict with blockers and fix hints for advancing phases |

**Genres supported:** `house`, `techno`, `ambient`, `hip_hop_trap`, `drum_and_bass`, `dubstep`, `trance`, `synthwave`, `future_bass`, `lo_fi`, `neo_soul_rnb`, `disco_funk`

**Phase types:** `setup`, `drums`, `bass`, `harmony`, `melody`, `sound_design`, `arrangement`, `mix`, `master`

**Checkpoint inference signals:**
- `setup` complete: `>=2 tracks`
- `drums` complete: track name matches `{drum,kick,snare,percussion,beat}` + has devices + has clips
- `bass`/`harmony`/`melody` complete: similar name+device+clip heuristic
- `mix` complete: `Compressor2` device class on any non-master track
- `master` complete: `GlueCompressor` + `Limiter2` both on master track

---

## CI/CD & Deployment

**Hosting:**
- Local installation (primary usage)
- Smithery.ai (via `smithery.yaml`)
- Docker (`Dockerfile` — `python:3.10-alpine`)

**CI Pipeline:**
- None detected (no `.github/` directory or CI config files)

---

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None

---

*Integration audit: 2026-04-01*
