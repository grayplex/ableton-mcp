# Technology Stack

**Analysis Date:** 2026-04-01

## Languages

**Primary:**
- Python 3.13 - MCP Server (`MCP_Server/`) and orchestration logic
- Python 2.x compat (CPython embedded in Ableton Live) - Remote Script (`AbletonMCP_Remote_Script/`); runs under Ableton's bundled CPython, which uses older `_Framework` APIs

**Secondary:**
- None (pure Python project)

## Runtime

**Environment:**
- Development/server: Python 3.13 (pinned via `.python-version`)
- `pyproject.toml` minimum: `requires-python = ">=3.10"`
- Ableton Remote Script: runs under Ableton Live's embedded CPython (version varies by Live release; `_Framework` uses pre-3.10 patterns — see `ruff` per-file ignore `UP035` for `AbletonMCP_Remote_Script/`)
- Docker baseline: `python:3.10-alpine` (see `Dockerfile`)

**Package Manager:**
- `uv` (lockfile: `uv.lock` present and committed)
- Build backend: `setuptools>=61.0` with `wheel`

## Frameworks

**Core:**
- `mcp[cli]` 1.4.0 (resolved; declared `>=1.3.0`) - Model Context Protocol SDK; provides `FastMCP` server, `@mcp.tool()` decorator, `Context` parameter injection, and `stdio` transport
- `FastMCP` from `mcp.server.fastmcp` - specific import used throughout `MCP_Server/server.py` and all `MCP_Server/tools/*.py`

**Testing:**
- `pytest` 9.0.2 (`>=8.3`) - test runner
- `pytest-asyncio` 1.3.0 (`>=0.25`) - async test support; `asyncio_mode = "auto"` in `pyproject.toml`
- `pytest-timeout` 2.4.0 (`>=2.0`) - per-test timeout (default 10s via `pyproject.toml`)

**Build/Dev:**
- `ruff` 0.15.6 (`>=0.15.6`) - linting and formatting; `line-length = 100`, `target-version = "py311"`, rules E/F/W/I/B/UP

## Key Dependencies

**Critical (production):**
- `mcp[cli]` 1.4.0 - the entire MCP server protocol, tool registration, and stdio transport
- `music21` 9.9.1 (`>=9.0`) - music theory computation: key detection, chord identification, scale analysis; lazy-imported in `MCP_Server/theory/analysis.py` to avoid startup cost

**Development only:**
- `tiktoken` 0.12.0 (`>=0.7`) - token budget validation in `tests/test_genre_quality.py`; uses `cl100k_base` encoding to enforce 400-1200 token limit on genre blueprints; not imported anywhere in `MCP_Server/`

## Configuration

**Environment:**
- No `.env` file or environment variables required for operation
- Connection target is hardcoded: `localhost:9877` (`MCP_Server/connection.py`, `AbletonMCP_Remote_Script/__init__.py`)
- No secrets or API keys; the only external system is Ableton Live running locally

**Build:**
- `pyproject.toml` - single source of truth for metadata, dependencies, scripts, and tool config
- `uv.lock` - reproducible installs
- `[project.scripts]`: `ableton-mcp = "MCP_Server.server:main"` - CLI entrypoint
- `smithery.yaml` - Smithery.ai deployment config; starts server via `python -m MCP_Server.server`
- `Dockerfile` - `python:3.10-alpine` image, installs via `pip install .`, runs `python -m MCP_Server.server`

**Packages registered in setuptools:**
`MCP_Server`, `MCP_Server.tools`, `MCP_Server.theory`, `MCP_Server.sounds`, `MCP_Server.genres`, `MCP_Server.mixing`, `MCP_Server.evaluation`, `MCP_Server.prompt`, `MCP_Server.refinement`, `MCP_Server.orchestration`

Note: `AbletonMCP_Remote_Script` is NOT in `[tool.setuptools].packages` — it is installed directly into Ableton Live's MIDI Remote Scripts folder, not via pip.

## Platform Requirements

**Development:**
- Python 3.13 (`.python-version`)
- `uv` for dependency management
- Ableton Live (any version with MIDI Remote Script support) running locally on the same machine

**Production / Deployment:**
- MCP Server: any Python 3.10+ environment (Docker, Smithery, local)
- Remote Script: must be copied into Ableton's `MIDI Remote Scripts/` directory; loaded by Ableton Live at runtime
- Communication: both sides must share `localhost:9877` (TCP)

---

*Stack analysis: 2026-04-01*
