# External Integrations

**Analysis Date:** 2026-04-02

## System Overview

This project has **no third-party cloud APIs** and **no external service credentials**.
The two integration surfaces are:

1. **Ableton Live** — a locally-running DAW controlled via a custom TCP socket protocol
2. **MCP Protocol** — the standard by which AI clients (Claude Desktop, Cursor) discover
   and invoke tools

All communication is local (localhost only). No HTTP calls are made at runtime.

---

## Ableton Live Integration

### Architecture

The Remote Script runs *inside* Ableton Live's Python interpreter as a MIDI Remote Script.
It exposes a TCP socket server. The MCP Server process connects to it as a client.

```
AI Client (Claude Desktop / Cursor)
    ↕ MCP stdio protocol
MCP Server (Python 3.10+ process)
    ↕ TCP socket localhost:9877
AbletonMCP Remote Script (inside Ableton Live process)
    ↕ Live Object Model (LOM) API
Ableton Live session state
```

### Socket Server (Remote Script side)

**File:** `AbletonMCP_Remote_Script/__init__.py`

- Binds `localhost:9877` (`SO_REUSEADDR` set)
- Listens for up to 5 queued connections (`server.listen(5)`)
- Each connection is handled in a daemon thread (`threading.Thread`, `daemon=True`)
- Server accept loop runs in its own daemon thread with 1s timeout for clean shutdown
- Constants: `DEFAULT_PORT = 9877`, `HOST = "localhost"` (lines 71-72)

**Start/stop lifecycle:**
- `start_server()` called in `__init__()` — socket bound and listen thread launched
- `disconnect()` called by Ableton when script is removed — sets `self.running = False`,
  closes socket, joins server thread with 1s timeout

### Socket Client (MCP Server side)

**File:** `MCP_Server/connection.py`

- `AbletonConnection` dataclass (lines 213-302): wraps `socket.socket`, serializes
  concurrent calls with `threading.Lock`
- `get_ableton_connection()` (lines 319-379): global singleton, thread-safe, liveness-checked
  via `ping` command before reuse, up to 3 connection attempts with 1s delay between attempts,
  validated with `get_session_info` after connect
- `shutdown_connection()` (lines 310-317): called on server shutdown via lifespan context

**Connection target:** `AbletonConnection(host="localhost", port=9877)` (line 348)

### Wire Protocol

**File:** `MCP_Server/protocol.py` (MCP Server side)
**Duplicated in:** `AbletonMCP_Remote_Script/__init__.py` lines 38-68 (Remote Script side)

- Length-prefix framing: 4-byte big-endian unsigned int header + UTF-8 JSON payload
- Maximum message size: 10MB (enforced in `recv_message`)
- Framing uses `struct.pack(">I", len(payload))` / `struct.unpack(">I", header)[0]`

**Command message (MCP Server → Remote Script):**
```json
{"type": "command_name", "params": {"key": "value"}}
```

**Response message (Remote Script → MCP Server):**
```json
{"status": "success", "result": {...}}
{"status": "error", "message": "human-readable error description"}
```

### Timeout Policy

Defined in `MCP_Server/connection.py` lines 14-35; applied per command in
`_timeout_for(command_type)` (lines 202-210):

| Category | Timeout | Applied to |
|----------|---------|-----------|
| Ping | 5s | `ping` only |
| Read (default) | 10s | all `get_*` read commands |
| Write | 15s | state-modifying commands (create, set, delete, etc.) |
| Browser | 30s | `get_browser_tree`, `load_instrument_or_effect`, `get_session_state`, `apply_recipe`, and other browser/bulk operations |

On timeout: socket is set to `None` (forces reconnect on next call); exception raised with
retry suggestion: `"This may happen when Ableton is scanning plugins. Retry the command."`

### Remote Script Command Dispatch

**Files:** `AbletonMCP_Remote_Script/registry.py`, `AbletonMCP_Remote_Script/__init__.py`

**Registration:** `@command(name, write=bool, self_scheduling=bool)` decorator in
`registry.py` records `(cmd_name, method_name, is_write, is_self_scheduling)` at import time.
`CommandRegistry.build_tables(self)` called in `__init__` to produce two dispatch dicts.

**Read commands:** Run directly on the socket thread (safe for read-only LOM access).

**Write commands:** Dispatched to Ableton's main thread via `self.schedule_message(0, task)`.
Result is returned via `queue.Queue` with a 10s timeout (30s for self-scheduling commands).
`AssertionError` fallback: runs task directly if `schedule_message` is unavailable
(e.g., in tests).

**Self-scheduling commands:** Commands that manage their own `schedule_message` chains
(e.g., `load_browser_item` which requires multi-tick execution) are called directly
without the queue pattern.

**Handler mixin classes** (all inherited by `AbletonMCP` class):
- `handlers/base.py` — `ping`, `get_session_info`
- `handlers/transport.py` — playback, tempo, time signature, loop, metronome, cue points
- `handlers/tracks.py` — create/delete/duplicate MIDI/audio/return/group tracks
- `handlers/clips.py` — create/delete/duplicate/configure clips
- `handlers/notes.py` — add/remove/quantize/transpose MIDI notes; note selection by ID
- `handlers/devices.py` — device parameters, Simpler, DrumRack, Wavetable, Operator,
  Drift, plugin presets, rack chains — 110KB, the largest handler file
- `handlers/mixer.py` — volume, pan, mute, solo, arm, sends, crossfader
- `handlers/scenes.py` — create/fire/delete scenes, scene properties
- `handlers/arrangement.py` — arrangement clips, locators, take lanes
- `handlers/automation.py` — envelope breakpoints, automation re-enable
- `handlers/audio_clips.py` — warp markers, audio clip properties
- `handlers/routing.py` — input/output routing
- `handlers/browser.py` — browser tree traversal, instrument/effect loading
- `handlers/grooves.py` — groove pool, groove parameters
- `handlers/scaffold.py` — `scaffold_tracks` bulk track creation

**Total registered commands:** ~190 (counted via `@command` decorator occurrences)

### Ableton Live Object Model (LOM) Access

The Remote Script accesses Ableton state through:
- `self._song` — cached reference to `self.song()` (the Live `Song` object)
- `self._song.tracks`, `self._song.return_tracks`, `self._song.master_track`
- `self._song.tempo`, `self._song.is_playing`, `self._song.signature_*`
- `self.application().get_major_version()` — Ableton version in `ping` response
- `import Live.Clip` — lazily imported inside handler methods for MIDI note access

---

## MCP Protocol Integration

### Overview

The Model Context Protocol defines how AI clients discover, describe, and invoke server
tools. This project exposes Ableton control capabilities as MCP tools.

**SDK:** `mcp[cli]` 1.4.0 from PyPI
**Transport:** `stdio` (subprocess stdin/stdout; AI client spawns the MCP server)
**Server name:** `"AbletonMCP"` (`MCP_Server/server.py` line 40)

### Server Initialization

```python
# MCP_Server/server.py
mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)
import MCP_Server.tools  # triggers @mcp.tool() registration
```

The `lifespan` context manager (`server_lifespan`) attempts the Ableton connection on
startup and calls `shutdown_connection()` on teardown. If Ableton is not running, the
server starts anyway with a warning.

### Tool Registration Pattern

Every tool module follows this pattern:
```python
from mcp.server.fastmcp import Context
from MCP_Server.server import mcp

@mcp.tool()
def tool_name(ctx: Context, param: type) -> str:
    """Docstring shown to AI clients as tool description."""
    ...
    return json.dumps(result, indent=2)
```

All tools return JSON strings. The `Context` parameter is injected by FastMCP; used by
async tools (`apply_mix_recipe`, `apply_master_recipe`) to emit progress via `ctx.info()`.

**Total tools registered:** 233 (counted via `@mcp.tool()` occurrences across all tool files)

**Tool modules** (`MCP_Server/tools/`):
- `session.py` — `get_connection_status`, `get_session_info`, `get_session_state`
- `tracks.py` — track CRUD and properties
- `clips.py` — clip creation, configuration, launch settings
- `notes.py` — MIDI note editing (add, remove, transpose, quantize, duplicate)
- `devices.py` — device parameters, Simpler/Wavetable/Operator/DrumRack control
- `mixer.py` — volume, pan, mute, solo, arm, sends
- `transport.py` — tempo, playback, time signature, loop, metronome
- `scenes.py` — scene management
- `arrangement.py` — arrangement view clips and locators
- `automation.py` — parameter envelopes
- `audio_clips.py` — warp markers and audio clip properties
- `routing.py` — I/O routing
- `browser.py` — Ableton browser navigation and instrument loading
- `grooves.py` — groove pool
- `scaffold.py` — `scaffold_arrangement` bulk track scaffolding
- `theory.py` — music theory (MIDI↔note, chords, scales, progressions, rhythm)
- `analysis.py` — session analysis (gain staging, role inference)
- `sounds.py` — instrument preset suggestions
- `genres.py` — genre blueprint retrieval
- `mixing.py` — `apply_mix_recipe`, `apply_master_recipe` (async tools)
- `evaluation.py` — session quality scoring
- `execution.py` — low-level command execution helpers
- `catalog.py` — device and recipe catalog queries
- `plans.py` — production plan generation
- `prompt.py` — `interpret_prompt`, `interpret_prompt_to_plan`
- `refinement.py` — section state and refinement suggestions
- `intelligence.py` — mix adjustment suggestions by diffing state vs recipe
- `orchestration.py` — production workflow tools (agenda, phase plans, checkpoints)

### MCP Entrypoints

| Method | Command |
|--------|---------|
| CLI script | `ableton-mcp` |
| Module | `python -m MCP_Server.server` |
| Ephemeral (uv) | `uvx ableton-mcp` |
| Docker | `CMD ["python", "-m", "MCP_Server.server"]` |
| Smithery | `python -m MCP_Server.server` (from `smithery.yaml`) |

---

## music21 Integration

**Package:** `music21` 9.9.1 (declared `>=9.0`, locked in `uv.lock`)

**Usage scope:** MCP Server only (`MCP_Server/theory/` package). Not used in Remote Script.

**Lazy import pattern** (all theory submodules):
```python
# MCP_Server/theory/chords.py
def _get_harmony_module():
    global _harmony_module
    if _harmony_module is None:
        from music21 import harmony
        _harmony_module = harmony
    return _harmony_module
```

This pattern avoids the ~2s music21 startup cost on server init.

**music21 submodules used:**
- `music21.harmony` — chord symbols and quality parsing (`theory/chords.py`)
- `music21.chord` — chord object construction (`theory/chords.py`)
- `music21.key` — key signature and tonal analysis (`theory/chords.py`, `theory/pitch.py`)
- `music21.roman` — Roman numeral analysis (`theory/chords.py`)
- `music21.pitch` — pitch class and enharmonic spelling (`theory/chords.py`, `theory/pitch.py`)
- `music21.scale` — scale object construction (`theory/chords.py`)
- `music21.stream` — note sequence analysis for key detection (`theory/analysis.py`)
- `music21.note` — note object wrapping (`theory/analysis.py`)

**Pure-Python fallback:** Pitch class math and scale analysis in `MCP_Server/theory/scales.py`,
`theory/rhythm.py`, `theory/progressions.py`, `theory/voicing.py` do NOT use music21 —
implemented with native arithmetic for speed.

---

## tiktoken Integration

**Package:** `tiktoken` 0.12.0 (dev dependency, declared `>=0.7`)

**Usage:** `tests/test_genre_quality.py` only — NOT in production code.

**Purpose:** Quality gate enforcing that each genre blueprint serializes to 400-1200 tokens
(OpenAI `cl100k_base` encoding), ensuring blueprints fit within AI context windows without
excessive consumption.

**Not imported anywhere in `MCP_Server/`.**

---

## Smithery.ai Deployment Integration

**File:** `smithery.yaml`

```yaml
startCommand:
  type: stdio
  commandFunction: (config) => ({ command: 'python', args: ['-m', 'MCP_Server.server'] })
```

- Transport: `stdio`
- No config schema properties — no user-configurable options
- Smithery registry: `@ahujasid/ableton-mcp`
- Badge in README: `https://smithery.ai/badge/@ahujasid/ableton-mcp`

---

## Docker Deployment

**File:** `Dockerfile`

- Base: `python:3.10-alpine`
- Build deps: `gcc musl-dev libffi-dev` (needed for music21 transitive C extensions)
- Install: `pip install --no-cache-dir .`
- CMD: `python -m MCP_Server.server`
- No ports exposed (MCP communicates via stdio, not TCP)

**Limitation:** In Docker, the socket connection to Ableton (`localhost:9877`) will only
work if Ableton Live runs in the same container or network namespace — which is impractical
for a DAW. Docker deployment is primarily for Smithery's managed hosting environment where
Ableton runs on the host and the Docker process is the MCP server subprocess.

---

## Data Storage

**Databases:** None
**File Storage:** None (no disk writes during normal operation)
**Caching:** In-memory only
- `_ableton_connection` global singleton (`MCP_Server/connection.py` line 306)
- `self._browser_path_cache: dict` in the Remote Script (`AbletonMCP_Remote_Script/__init__.py`
  line 124) — cleared on disconnect

---

## Authentication & Identity

**None.** No authentication between MCP Server and Remote Script — connection is
`localhost` only, no token or credential exchange. AI client authentication is handled
by the AI client host (Claude Desktop, Cursor) outside this project.

---

## CI/CD

**None detected.** No `.github/` directory, no CI config files. Tests run locally via
`pytest` or `uv run pytest`.

---

*Integration audit: 2026-04-02*
