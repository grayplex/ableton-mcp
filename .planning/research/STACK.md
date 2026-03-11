# Stack Research

**Domain:** MCP server bridging AI assistants to Ableton Live 12 via Remote Scripts
**Researched:** 2026-03-10
**Confidence:** HIGH (core stack verified via official docs and PyPI; Remote Script constraints confirmed via community sources)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python (MCP server) | 3.11+ | Runtime for MCP server | Ableton Live 12 ships Python 3.11 — using the same version eliminates edge-case incompatibilities. `pyproject.toml` already pins `>=3.10`; bump to `>=3.11` to match the embedded runtime. |
| Python (Remote Script) | 3.11 (embedded) | Runs inside Ableton Live | Ableton Live 12's embedded interpreter is Python 3.11 (`.cpython-311.pyc` bytecache confirms this). **No control over this version** — code must be compatible and Python 2 compat code must be stripped. |
| `mcp[cli]` | 1.26.0 | Model Context Protocol SDK | Official Anthropic SDK. Already in use as `from mcp.server.fastmcp import FastMCP`. Provides `FastMCP`, `Context`, tool decorators, lifespan management, and the MCP stdio transport. v1.26.0 is the current 1.x release (2.0 in development on main branch, not yet released). |
| `uv` | latest | Package management | Already adopted (uv.lock present). Faster than pip, handles Python version management, lock files, and virtual environments. Standard for new Python projects in 2025/2026. |

### Supporting Libraries (MCP Server)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | >=8.3 | Test framework | All tests. Baseline requirement — zero test coverage is the biggest risk to safe expansion. |
| `pytest-asyncio` | >=0.25 | Async test support | FastMCP tools run in async context; test fixtures require `asyncio_mode = "auto"`. Required alongside pytest. |
| `ruff` | >=0.9 | Linter + formatter | Replaces flake8 + black + isort in a single Rust-backed tool. Configure in `pyproject.toml` under `[tool.ruff]`. No existing linting config — this is the right time to add it. |
| `inline-snapshot` | >=0.18 | Test assertions on complex structures | MCP tools return JSON strings — inline-snapshot simplifies asserting complex nested outputs without brittle string comparisons. Use when writing tool response tests. |

### Remote Script (Ableton-embedded Python 3.11)

**Critical constraint:** The Remote Script runs inside Ableton's sandboxed Python 3.11. It cannot install third-party packages. Only Python stdlib and Ableton's `_Framework` / `Live` modules are available.

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `_Framework.ControlSurface` | Ableton-bundled | Base class for all Remote Scripts | The documented entry point. `create_instance()` must return a `ControlSurface` subclass. No alternative — this is the contract Ableton specifies. |
| `socket` (stdlib) | stdlib | TCP socket server inside Ableton | Stdlib only — no asyncio in the Remote Script (Ableton's event loop is not compatible). Blocking sockets run in daemon threads. Keep it simple. |
| `threading` (stdlib) | stdlib | Background socket server thread | Ableton's main thread must not block. The socket server runs in a daemon thread; all Live API calls are dispatched to the main thread via `schedule_message()`. |
| `queue` (stdlib) | stdlib | Thread-safe response passing | `queue.Queue` is the correct Python 3 import (remove the `try/except Queue as queue` Py2 compat). Used to pass responses from main thread back to socket thread. |
| `json` (stdlib) | stdlib | Command serialization | Already the protocol format. No alternative needed — JSON is fast enough for the command volumes involved. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `uv` | Dependency management, virtual environments | `uv add <dep>` for prod, `uv add --dev <dep>` for dev. `uv run pytest` runs tests in the managed venv. |
| `ruff` | Lint and format | Configure `[tool.ruff.lint]` and `[tool.ruff.format]` in `pyproject.toml`. Set `target-version = "py311"`. Enforces PEP 8 + import ordering. |
| MCP Inspector | Manual tool testing | Ships with `mcp[cli]`. Run `mcp dev MCP_Server/server.py` to get a browser UI for testing tools without Claude. Invaluable during development. |
| Ableton Live log | Remote Script debugging | `self.log_message()` writes to `%USERPROFILE%\AppData\Roaming\Ableton\Live 12.x\Preferences\Log.txt` on Windows. Tail this file during development. |

---

## Installation

```bash
# Core runtime dependency (already in pyproject.toml — update version pin)
uv add "mcp[cli]>=1.26.0"

# Development dependencies
uv add --dev pytest>=8.3
uv add --dev pytest-asyncio>=0.25
uv add --dev ruff>=0.9
uv add --dev inline-snapshot>=0.18
```

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]  # pycodestyle, pyflakes, isort, pyupgrade
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `mcp[cli]` 1.26.0 (from official SDK) | `fastmcp` 3.1.0 (standalone PrefectHQ package) | Use standalone `fastmcp` if you need OAuth 2.1 auth, OpenAPI integration, or the provider/transform architecture from FastMCP 3.x. For this project (simple bridge, no auth), the official SDK's built-in FastMCP is sufficient and avoids a dependency fork. |
| stdlib `socket` + `threading` in Remote Script | `asyncio` | Asyncio is not usable inside Ableton's embedded interpreter — Ableton's event model is not async-compatible. Use stdlib blocking sockets in threads only. |
| Length-prefix framing for socket protocol | Parse-until-valid-JSON (current) | The current approach re-parses accumulated bytes on every chunk (O(n²) for large responses). A 4-byte length prefix is the robust fix. Implement a `struct.pack(">I", len(data))` prefix to eliminate ambiguity and the performance issue. |
| `ruff` | `black` + `flake8` + `isort` | Only if the team already has black/flake8 configured and doesn't want migration cost. For a fresh config (which this project needs), ruff does all three jobs 10-100x faster. |
| `pytest` + `pytest-asyncio` | `unittest` | Use unittest only if pytest is too heavy a dependency. It's not — pytest is 2026 standard. |
| `uv` | `pip` + `venv` | Use pip/venv only in locked-down CI environments that can't install uv. Not a concern here. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Python 2 compat code (`try: import Queue`, `from __future__ import`) | Ableton Live 12 uses Python 3.11. No Python 2 Ableton versions exist in the wild that matter. The compat code adds complexity, hides bugs, and makes the codebase read as legacy. | Pure Python 3 syntax throughout |
| `from __future__ import unicode_literals` | Python 3 strings are Unicode by default. This import is a no-op that signals Python 2 thinking. | Delete it |
| `try: data.decode('utf-8') except AttributeError: data` | In Python 3, `socket.recv()` always returns `bytes`. The AttributeError branch is dead code that masks type errors. | `data.decode('utf-8')` directly — no try/except needed |
| Bare `except:` clauses | Catches `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit` — this silently swallows Ctrl-C and makes debugging impossible. | `except Exception:` at minimum; `except (ConnectionError, BrokenPipeError):` specifically |
| Validate JSON completeness by re-parsing on every chunk | O(n²) complexity. For a 100KB response in 8KB chunks = 12+ full parse passes. Also fragile for partial UTF-8 boundaries. | Length-prefix framing: 4-byte big-endian length header before each JSON payload |
| Global mutable `_ableton_connection` without a lock | Multiple async tasks can race on this global. One task sets it to `None` while another reads it — results in `AttributeError`. | `threading.Lock()` protecting all reads/writes, or restructure as a connection manager class |
| `time.sleep()` as a post-command delay | 100ms sleep to "let Ableton process" is a hack that makes the MCP server slower and doesn't guarantee correctness. | Proper acknowledgment in the response protocol — the Remote Script confirms completion before responding |
| Standalone `fastmcp` 3.x package | FastMCP 3.x (PrefectHQ) and `mcp.server.fastmcp` (official SDK) have diverged. An Anthropic engineer confirmed they are "sufficiently diverged." Mixing both creates confusion. Since this project already uses the official SDK's FastMCP, stay there. | `from mcp.server.fastmcp import FastMCP` from `mcp[cli]` |

---

## Stack Patterns by Variant

**For the MCP Server (Claude-facing):**
- Use `mcp[cli]` with `FastMCP` + `@mcp.tool()` decorators
- Connection to Ableton is synchronous (blocking socket calls inside async wrappers)
- Lifespan manager handles connection setup/teardown
- Use `threading.Lock` to protect the global connection singleton

**For the Remote Script (Ableton-facing):**
- Extend `_Framework.ControlSurface`
- Socket server in a `daemon=True` thread; **never** block the main thread
- All `Live.*` API calls via `self.schedule_message(0, self._do_thing)` or `self.call_later(0, self._do_thing)` — never call them from a non-main thread
- Use `queue.Queue` for main-thread → socket-thread response passing

**For the socket protocol between them:**
- Use length-prefix framing: `struct.pack(">I", len(payload)) + payload`
- Receiver: read 4 bytes for length, then read exactly N bytes
- This eliminates the O(n²) chunk-parsing issue and handles large payloads (device lists, MIDI note arrays) correctly

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `mcp[cli]` 1.26.0 | Python 3.10–3.13 | 1.26.0 is the latest 1.x; 2.0 is under development but unreleased as of 2026-03-10. Pin `>=1.26.0,<2` if concerned about breaking changes from 2.0. |
| `pytest-asyncio` 0.25+ | `pytest` 8.x | `asyncio_mode = "auto"` in `pyproject.toml` required. Earlier versions required explicit `@pytest.mark.asyncio` on every test. |
| `ruff` 0.9+ | Python 3.11 target | Set `target-version = "py311"` so ruff understands which syntax is valid. |
| Remote Script | Ableton Live 12 (Python 3.11) | `.cpython-311.pyc` bytecache format confirms Python 3.11. Remote Script directory: `%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\` |

---

## Sources

- [PyPI: fastmcp](https://pypi.org/project/fastmcp/) — Current version 3.1.0 (standalone PrefectHQ package), verified 2026-03-10 — HIGH confidence
- [PyPI: mcp](https://pypi.org/project/mcp/) — Current version 1.26.0 (official Anthropic SDK), verified 2026-03-10 — HIGH confidence
- [MCP Python SDK releases](https://github.com/modelcontextprotocol/python-sdk/releases) — v1.26.0 is latest 1.x; 2.0 in development — HIGH confidence
- [FastMCP 2.0 vs MCP SDK issue](https://github.com/modelcontextprotocol/python-sdk/issues/1068) — Anthropic engineer confirmed packages have "sufficiently diverged" — HIGH confidence
- [FastMCP testing docs](https://gofastmcp.com/servers/testing) — pytest-asyncio + Client fixture pattern — HIGH confidence
- [Ableton Live 12 Python 3.11 confirmation](https://forum.ableton.com/viewtopic.php?t=248076) — `.cpython-311.pyc` bytecache confirms Python 3.11 — MEDIUM confidence (community source, but consistent with PROJECT.md)
- [Ziforge ableton-liveapi-tools](https://github.com/Ziforge/ableton-liveapi-tools) — stdlib-only Remote Script pattern, 220 tools for reference — MEDIUM confidence
- [Ruff documentation](https://docs.astral.sh/ruff/) — Configuration patterns, current as of 2026 — HIGH confidence
- [uv documentation](https://docs.astral.sh/uv/) — Project management patterns — HIGH confidence
- Existing codebase: `.planning/codebase/STACK.md`, `ARCHITECTURE.md`, `CONCERNS.md`, `CONVENTIONS.md` — Confirmed current dependencies and pain points — HIGH confidence

---

*Stack research for: Ableton Live 12 MCP server (brownfield extension)*
*Researched: 2026-03-10*
