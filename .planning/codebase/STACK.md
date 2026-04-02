# Technology Stack

**Analysis Date:** 2026-04-02

## Languages

**Primary:**
- Python 3.13 — development runtime, pinned in `.python-version`
- Python >=3.10 — declared minimum in `pyproject.toml` line 7
- Python 3.10 — used in `Dockerfile` (`python:3.10-alpine`)

**Version discrepancy:** `.python-version` pins 3.13 for local dev; Dockerfile pins 3.10-alpine
for containerized deployment; ruff `target-version = "py311"` (`pyproject.toml` line 47).
All are compatible given the `requires-python = ">=3.10"` floor.

**Ableton Remote Script side:**
- Runs under Ableton Live's embedded CPython (pre-3.10 API surface via `_Framework`)
- Ruff suppresses `UP035` (deprecated import) for `AbletonMCP_Remote_Script/**` because
  `_Framework` uses older Python patterns (`pyproject.toml` line 67)
- Only stdlib is used: `json`, `socket`, `struct`, `threading`, `queue`, `time`, `traceback`
  plus Ableton-internal `_Framework.ControlSurface` and `Live.Clip`

**Secondary:** None (pure Python project)

## Runtime

**MCP Server environment:**
- Standard CPython on macOS/Linux/Windows
- Async: `asyncio` via `anyio` (MCP SDK); most tools are synchronous, two tools
  (`apply_mix_recipe`, `apply_master_recipe` in `MCP_Server/tools/mixing.py`) use
  `async def` + `loop.run_in_executor` to avoid blocking the event loop on long Ableton calls

**Ableton Remote Script environment:**
- Runs in Ableton Live's process; no pip, no external packages
- Socket server runs in a daemon thread (`threading.Thread`, `daemon=True`)
- Write commands dispatched to Ableton's main thread via `self.schedule_message(0, task)`
  with a `queue.Queue` for result collection

**Package Manager:**
- `uv` — recommended in README; `uvx ableton-mcp` is the canonical install command
- `pip` — also supported (used in `Dockerfile`)
- Lockfile: `uv.lock` (version 1, revision 3) — committed to repo

## Frameworks

**Core MCP:**
- `mcp[cli]` 1.4.0 (locked; declared `>=1.3.0`) — Model Context Protocol SDK
  - Provides `FastMCP` class (`mcp.server.fastmcp.FastMCP`)
  - `@mcp.tool()` decorator for tool registration
  - `Context` type injected as first parameter of every tool function
  - Default transport: `stdio` — `mcp.run()` in `MCP_Server/server.py` line 48
  - Transitive runtime deps: `anyio` 4.8.0, `httpx` 0.28.1, `starlette` 0.46.1,
    `sse-starlette` 2.2.1, `uvicorn` 0.34.0, `pydantic` 2.10.6, `pydantic-settings`,
    `typer`, `rich`, `httpx-sse` 0.4.0

**Music Theory:**
- `music21` 9.9.1 (locked; declared `>=9.0`) — Music theory computation
  - Lazy-imported on first use to keep server startup fast
  - Used in `MCP_Server/theory/analysis.py`, `theory/chords.py`, `theory/pitch.py`
  - Transitive deps: `matplotlib`, `numpy`, `chardet`, `requests`, `joblib`,
    `more-itertools`, `webcolors`, `jsonpickle`

**Ableton Live Framework (Remote Script only):**
- `_Framework.ControlSurface` — Ableton's internal MIDI Remote Script base class
  - `AbletonMCP` class inherits from it plus 14 handler mixin classes
  - Provides `self.song()`, `self.application()`, `self.schedule_message()`,
    `self.log_message()`, `self.show_message()`
- `Live.Clip` — Ableton's internal module for MIDI note manipulation
  - Imported lazily inside handler methods in `handlers/notes.py`,
    `handlers/arrangement.py`, `handlers/audio_clips.py`

## Key Dependencies

**Production (direct):**
- `mcp[cli]` >=1.3.0 (locked 1.4.0) — The entire MCP protocol layer; without it the server
  cannot expose tools to AI clients. Entry: `MCP_Server/server.py` line 8.
- `music21` >=9.0 (locked 9.9.1) — Music theory engine for theory/chord/scale/rhythm tools.
  Entry: `MCP_Server/theory/` package. Lazy-loaded on first call.

**Development (declared in `[dependency-groups].dev`):**
- `pytest` 9.0.2 — test runner; 48 test files in `tests/`
- `pytest-asyncio` 0.25.x — async test support; `asyncio_mode = "auto"` globally
- `pytest-timeout` 2.x — 10-second default timeout per test
- `ruff` 0.15.6 — linting + formatting in one tool
- `tiktoken` 0.12.0 — token-budget quality gate in `tests/test_genre_quality.py` only;
  not imported in any production code

## Configuration

**No environment variables required.** The only runtime config is the hardcoded socket
endpoint `localhost:9877` defined in:
- `MCP_Server/connection.py` line 348: `AbletonConnection(host="localhost", port=9877)`
- `AbletonMCP_Remote_Script/__init__.py` lines 71-72: `DEFAULT_PORT = 9877`, `HOST = "localhost"`

**Build config files:**
- `pyproject.toml` — project metadata, dependencies, scripts entrypoint, pytest config,
  ruff config, setuptools package list
- `uv.lock` — reproducible dependency resolution (must be committed)
- `Dockerfile` — `python:3.10-alpine` container; installs via `pip install .`; CMD runs
  `python -m MCP_Server.server`
- `smithery.yaml` — Smithery.ai deployment; `type: stdio`; runs `python -m MCP_Server.server`

**Console entrypoint:**
- `ableton-mcp` → `MCP_Server.server:main` (`pyproject.toml` line 22)
- Also: `python -m MCP_Server.server` (Dockerfile, smithery)
- Also: `uvx ableton-mcp` (ephemeral install via uv)

**Registered packages (setuptools):**
`MCP_Server`, `MCP_Server.tools`, `MCP_Server.theory`, `MCP_Server.sounds`,
`MCP_Server.genres`, `MCP_Server.mixing`, `MCP_Server.evaluation`, `MCP_Server.prompt`,
`MCP_Server.refinement`, `MCP_Server.orchestration`

Note: `AbletonMCP_Remote_Script` is NOT in setuptools packages — it is installed manually
into Ableton Live's `MIDI Remote Scripts/` folder, not distributed via pip.

## Platform Requirements

**Development:**
- Python 3.13 (`.python-version`) with `uv` package manager
- Ableton Live 10+ running locally (same machine) with the Remote Script loaded via
  Live Preferences > Link/Tempo/MIDI > MIDI Remote Scripts
- No cloud accounts, API keys, or external services needed

**Production (Smithery / Docker):**
- Docker: `python:3.10-alpine` + `gcc musl-dev libffi-dev` build deps (for C extensions
  in music21 transitive deps like numpy/chardet)
- MCP transport: `stdio` — server reads from stdin, writes to stdout; AI client manages
  the subprocess. No network ports exposed.
- Ableton Live must still run on the same host machine and bind port 9877

**AI client compatibility (confirmed in README):**
- Claude Desktop — `uvx ableton-mcp` via `claude_desktop_config.json`
- Cursor — `uvx ableton-mcp` via MCP settings

---

*Stack analysis: 2026-04-02*
