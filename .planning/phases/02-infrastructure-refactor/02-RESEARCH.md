# Phase 2: Infrastructure Refactor - Research

**Researched:** 2026-03-13
**Domain:** Python module architecture, decorator-based command registry, MCP tool organization, ruff linting, pytest/FastMCP testing
**Confidence:** HIGH

## Summary

Phase 2 is a pure structural refactoring of two monolithic files into domain-organized module packages. The Remote Script (`AbletonMCP_Remote_Script/__init__.py`, 1230 lines) splits into a `handlers/` package with 9 domain modules. The MCP Server (`MCP_Server/server.py`, 797 lines) splits into a `tools/` package with domain-specific tool modules. The existing Phase 1 dict-based dispatch evolves into a decorator-based `@command()` registry for the Remote Script, and the MCP server continues using FastMCP's built-in `@mcp.tool()` decorator across domain modules.

Ruff linting is configured at "moderate" strictness (PEP 8 + imports + bugbear + pyupgrade), and pytest smoke tests use FastMCP's built-in `call_tool()` and `list_tools()` async methods for in-memory testing without needing a separate client or subprocess.

**Primary recommendation:** Extract handlers and tools into domain modules with explicit `__init__.py` re-exports, use a simple class-based CommandRegistry with `@command('name')` decorator for the Remote Script, keep FastMCP's `@mcp.tool()` for MCP tools, and test via `await mcp.call_tool()` directly on the server instance.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Keep browser and devices as **separate modules** -- browser.py handles navigation/search, devices.py handles parameters/chains
- Keep transport and scenes as **separate modules** -- transport.py (play, stop, tempo, time sig, loop) and scenes.py (create, fire, delete)
- Remote Script splits into: base.py, transport.py, tracks.py, clips.py, notes.py, devices.py, mixer.py, scenes.py, browser.py
- MCP server splits into tools/ domain modules mirroring the same domains
- **Evolve** Phase 1's dict-based `_build_command_table()` into a formal registry with `@command('name')` decorator
- Each domain module decorates its handlers, registry auto-collects them
- **Standardize all tool names** during the split -- verb_noun pattern (get_track_info, create_clip, set_tempo, fire_clip, add_notes)
- Rename health-check to snake_case (health_check or get_health)
- **Polish all tool docstrings** -- standardize format: one-line summary + parameter descriptions
- **Moderate strictness** ruff -- PEP 8 + import ordering + basic type checking, line length 100, target Python 3.11 for Remote Script, Python 3.10+ for MCP server
- **Smoke tests per domain** -- each domain module gets 1-2 smoke tests verifying tools register and respond (~15-20 tests total)
- **Mock only** -- all tests run without Ableton via mocked socket responses, CI-friendly, fast, deterministic
- Uses FastMCP in-memory client (no socket needed for MCP-side tests)
- **Reorganize Phase 1 tests** into new domain structure

### Claude's Discretion
- Whether MCP tools/ module names mirror Remote Script handler names exactly or group differently for AI client perspective
- Exact @command decorator implementation details (class-based registry vs module-level collector)
- Which Phase 1 tests to keep vs rewrite during reorganization
- Specific ruff rule selection within "moderate" guidance

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FNDN-07 | MCP tools organized into domain modules (tracks, clips, mixing, etc.) | Split server.py into tools/ package with domain modules; each module registers tools via @mcp.tool(); connection module extracted separately |
| FNDN-08 | Remote Script handlers organized into domain modules with @main_thread decorator | Split __init__.py into handlers/ package with @command decorator registry; _dispatch_write_command pattern wrapped in @main_thread |
| FNDN-09 | Linting configured with ruff (target Python 3.11, PEP 8, import ordering) | Ruff config in pyproject.toml with select=["E","F","W","I","B","UP"], line-length=100, target-version="py311" |
| FNDN-10 | Test infrastructure with pytest + pytest-asyncio using FastMCP in-memory client | Use mcp.server.fastmcp.FastMCP.call_tool() and list_tools() directly (async); pytest-asyncio with asyncio_mode="auto" already configured |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp[cli] | >=1.3.0 (installed: 1.4.0) | MCP server framework with FastMCP | Already in use; provides @mcp.tool() decorator and direct call_tool/list_tools for testing |
| ruff | latest | Python linter and formatter | Industry standard, extremely fast, replaces flake8+isort+pyupgrade in one tool |
| pytest | >=8.3 | Test framework | Already in dev dependencies |
| pytest-asyncio | >=0.25 | Async test support | Already in dev dependencies; asyncio_mode="auto" already configured |
| pytest-timeout | >=2.0 | Test timeout protection | Already in dev dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| _Framework.ControlSurface | Ableton built-in | Remote Script base class | Required by all Remote Script modules -- only available inside Ableton's Python runtime |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mcp[cli] FastMCP.call_tool() | Standalone fastmcp Client | Would add another dependency; mcp 1.4.0 already has call_tool/list_tools built into FastMCP |
| ruff | flake8 + isort + pyupgrade | Three separate tools; ruff replaces all with 10-100x speed |
| Class-based CommandRegistry | Module-level dict + decorator function | Class-based is cleaner for the Remote Script pattern where all handlers are instance methods |

**Installation:**
```bash
# ruff is a dev tool, install separately
uv add --dev ruff
```

## Architecture Patterns

### Recommended Remote Script Structure
```
AbletonMCP_Remote_Script/
  __init__.py          # create_instance(), AbletonMCP class (slim: init, server, client handling)
  protocol.py          # send_message, recv_message, _recv_exact (shared protocol functions)
  registry.py          # CommandRegistry class with @command decorator
  handlers/
    __init__.py        # Import all handler modules to trigger registration
    base.py            # _ping, _get_session_info -- session-level queries
    transport.py       # _start_playback, _stop_playback, _set_tempo
    tracks.py          # _create_midi_track, _set_track_name, _get_track_info
    clips.py           # _create_clip, _set_clip_name, _fire_clip, _stop_clip
    notes.py           # _add_notes_to_clip
    devices.py         # _set_device_parameter, _get_device_type
    mixer.py           # (empty placeholder for Phase 4 -- MIX-01..08)
    scenes.py          # (empty placeholder for Phase 8 -- SCNE-01..04)
    browser.py         # _load_browser_item, _load_instrument_or_effect, get_browser_tree, get_browser_items_at_path, _find_browser_item_by_uri, _get_browser_item, _get_browser_categories, _get_browser_items
```

### Recommended MCP Server Structure
```
MCP_Server/
  __init__.py          # __version__, re-export AbletonConnection + get_ableton_connection
  server.py            # FastMCP instance, lifespan, main(), imports tools/ to register
  connection.py        # AbletonConnection dataclass, get_ableton_connection, timeout constants, format_error
  protocol.py          # send_message, recv_message, _recv_exact
  tools/
    __init__.py        # Import all tool modules to trigger @mcp.tool() registration
    session.py         # get_connection_status, get_session_info
    tracks.py          # get_track_info, create_midi_track, set_track_name
    clips.py           # create_clip, set_clip_name, add_notes_to_clip, fire_clip, stop_clip
    transport.py       # start_playback, stop_playback, set_tempo
    devices.py         # load_instrument_or_effect, set_device_parameter (placeholder)
    browser.py         # get_browser_tree, get_browser_items_at_path, load_drum_kit
    mixer.py           # (empty placeholder for Phase 4)
    scenes.py          # (empty placeholder for Phase 8)
```

### Recommended Test Structure
```
tests/
  __init__.py
  conftest.py          # Shared fixtures: mock_ableton_connection, mcp_server, source file readers
  test_session.py      # Test get_connection_status, get_session_info tools
  test_tracks.py       # Test get_track_info, create_midi_track, set_track_name tools
  test_clips.py        # Test create_clip, set_clip_name, add_notes tools
  test_transport.py    # Test start_playback, stop_playback, set_tempo tools
  test_devices.py      # Test load_instrument_or_effect tool
  test_browser.py      # Test get_browser_tree, get_browser_items_at_path tools
  test_protocol.py     # KEEP -- protocol roundtrip tests are infrastructure-level
  test_registry.py     # Test @command decorator and CommandRegistry
```

### Pattern 1: CommandRegistry with @command Decorator (Remote Script)

**What:** A class-based registry that collects command handlers decorated with `@command('name')` and produces read/write dispatch dicts.
**When to use:** For all Remote Script handler registration.

```python
# registry.py
class CommandRegistry:
    """Registry for Remote Script command handlers.

    Decorators record (name, handler, is_write) tuples.
    The AbletonMCP class calls registry.build_tables(self) at init
    to bind handlers to the instance and produce dispatch dicts.
    """

    _commands: list[tuple[str, str, bool]] = []  # (cmd_name, method_name, is_write)

    @classmethod
    def command(cls, name: str, *, write: bool = False):
        """Register a handler method for a command name.

        Args:
            name: Command string sent over the wire (e.g., 'get_session_info')
            write: If True, command runs on main thread via schedule_message
        """
        def decorator(func):
            cls._commands.append((name, func.__name__, write))
            return func
        return decorator

    @classmethod
    def build_tables(cls, instance) -> tuple[dict, dict]:
        """Build read_commands and write_commands dicts bound to instance."""
        read_commands = {}
        write_commands = {}
        for cmd_name, method_name, is_write in cls._commands:
            handler = getattr(instance, method_name)
            if is_write:
                write_commands[cmd_name] = handler
            else:
                read_commands[cmd_name] = handler
        return read_commands, write_commands

# Usage in handler modules:
# handlers/transport.py
from ..registry import CommandRegistry

command = CommandRegistry.command

class TransportHandlers:
    """Mixin class for transport command handlers."""

    @command("start_playback", write=True)
    def _start_playback(self, params=None):
        """Start playing the session."""
        self._song.start_playing()
        return {"playing": self._song.is_playing}

    @command("stop_playback", write=True)
    def _stop_playback(self, params=None):
        """Stop playing the session."""
        self._song.stop_playing()
        return {"playing": self._song.is_playing}

    @command("set_tempo", write=True)
    def _set_tempo(self, params):
        """Set the tempo of the session."""
        tempo = params.get("tempo", 120.0)
        self._song.tempo = tempo
        return {"tempo": self._song.tempo}
```

**IMPORTANT constraint:** The Remote Script runs inside Ableton's Python runtime where `_Framework.ControlSurface` is the base class. Handler methods need `self` (the AbletonMCP instance) to access `self._song`, `self.application()`, `self.log_message()`, etc. The mixin pattern lets domain modules define methods that get composed into the AbletonMCP class.

### Pattern 2: MCP Tool Domain Modules

**What:** Each tool module imports the shared `mcp` server instance and registers tools with `@mcp.tool()`.
**When to use:** For all MCP server tool organization.

```python
# MCP_Server/server.py
from mcp.server.fastmcp import FastMCP
from contextlib import asynccontextmanager

# Create the MCP server instance FIRST
mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)

# Import tool modules AFTER mcp is created so decorators can register
from .tools import session, tracks, clips, transport, devices, browser  # noqa: E402, F401

def main():
    mcp.run()

# MCP_Server/tools/tracks.py
from mcp.server.fastmcp import Context
from ..server import mcp
from ..connection import get_ableton_connection, format_error
import json

@mcp.tool()
def get_track_info(ctx: Context, track_index: int) -> str:
    """Get detailed information about a specific track.

    Parameters:
    - track_index: The index of the track (0-based)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_track_info", {"track_index": track_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get track info",
            detail=str(e),
            suggestion="Verify track_index is valid with get_session_info"
        )
```

### Pattern 3: FastMCP In-Memory Testing

**What:** Use `await mcp.call_tool()` and `await mcp.list_tools()` directly on the FastMCP server instance for testing.
**When to use:** For all MCP server smoke tests.

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_ableton_connection():
    """Create a mock AbletonConnection that returns canned responses."""
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {
        "tempo": 120.0,
        "track_count": 4,
    }
    with patch("MCP_Server.connection.get_ableton_connection", return_value=mock_conn):
        yield mock_conn

@pytest.fixture
def mcp_server():
    """Return the FastMCP server instance for testing."""
    from MCP_Server.server import mcp
    return mcp

# tests/test_tracks.py
import pytest
import json

async def test_get_track_info_registered(mcp_server):
    """get_track_info tool is registered in the MCP server."""
    tools = await mcp_server.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_track_info" in tool_names

async def test_get_track_info_returns_data(mcp_server, mock_ableton_connection):
    """get_track_info returns track data from mocked connection."""
    mock_ableton_connection.send_command.return_value = {
        "index": 0, "name": "Bass", "is_midi_track": True
    }
    result = await mcp_server.call_tool("get_track_info", {"track_index": 0})
    data = json.loads(result[0].text)
    assert data["name"] == "Bass"
```

### Pattern 4: Circular Import Prevention

**What:** The MCP server creates `mcp = FastMCP(...)` in `server.py`, then imports tool modules. Tool modules import `mcp` from `server.py`. This creates a circular import if done naively.
**When to use:** Always when splitting monolithic files into modules that reference shared state.

```python
# SOLUTION: Deferred imports using module-level imports after object creation

# MCP_Server/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AbletonMCP")  # Created before tool imports

# Import tool modules at module level, but AFTER mcp is defined
# Python handles this because by the time tools/__init__.py runs,
# the 'mcp' name is already bound in this module's namespace
import MCP_Server.tools  # noqa: E402

# MCP_Server/tools/__init__.py
"""Import all tool modules to trigger @mcp.tool() registration."""
from . import session, tracks, clips, transport, devices, browser  # noqa: F401

# MCP_Server/tools/tracks.py
import json
from mcp.server.fastmcp import Context
from MCP_Server.server import mcp  # This works because mcp is already created
from MCP_Server.connection import get_ableton_connection, format_error
```

**Alternative if circular import still occurs:** Use a separate `app.py` module that only creates the FastMCP instance, imported by both `server.py` and tool modules.

### Anti-Patterns to Avoid

- **Relative imports in Remote Script:** Ableton's Python runtime has quirks with package imports. Test whether `from .handlers import tracks` works or whether absolute imports are needed. If relative imports fail, use `from AbletonMCP_Remote_Script.handlers import tracks`.
- **Importing tool modules inside functions:** Defeats the purpose of module-level registration. Tools must be imported at module level so `@mcp.tool()` decorators execute on import.
- **Giant `__init__.py` re-exports:** Don't dump all handler code into `handlers/__init__.py`. Keep `__init__.py` files as thin import-only manifests.
- **Mixing handler concerns:** Keep notes.py separate from clips.py even though notes always go in clips. The boundary is the Ableton API method grouping, not the user workflow.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP tool registration | Custom decorator that mimics @mcp.tool() | FastMCP's built-in @mcp.tool() decorator | It handles schema generation, parameter validation, Context injection, and result serialization |
| Import sorting | Manual import ordering | ruff with "I" (isort) rules | Automatic, deterministic, integrates with formatter |
| Python version modernization | Manual code review for old patterns | ruff with "UP" (pyupgrade) rules | Automatically suggests super() instead of super(Class, self), etc. |
| Test async infrastructure | Custom event loop management | pytest-asyncio with asyncio_mode="auto" | Already configured in pyproject.toml; handles async fixtures and tests transparently |
| Error formatting | Custom error string builder per tool | Shared format_error() function in connection module | Already exists; all tools should use it consistently |

**Key insight:** The project already has the right dependencies. No new packages are needed for the refactoring work -- just reorganizing code and adding ruff as a dev tool.

## Common Pitfalls

### Pitfall 1: Circular Imports Between server.py and Tool Modules
**What goes wrong:** `server.py` creates `mcp = FastMCP(...)` and needs to import tool modules. Tool modules need to import `mcp` to use `@mcp.tool()`. Naive mutual imports crash at startup.
**Why it happens:** Python executes module-level code on import. If A imports B before A's own names are bound, B can't import from A.
**How to avoid:** Define `mcp` BEFORE importing tool modules in `server.py`. Use absolute imports in tool modules (`from MCP_Server.server import mcp`). The `mcp` name will be bound by the time tool modules execute.
**Warning signs:** `ImportError: cannot import name 'mcp' from partially initialized module`

### Pitfall 2: Remote Script Import Restrictions
**What goes wrong:** The Remote Script runs inside Ableton's embedded Python 3.11 runtime. Standard package management (pip, venv) doesn't apply. `_Framework` is only available at runtime inside Ableton.
**Why it happens:** Ableton loads Remote Scripts as Python packages from a specific directory. The Python path is controlled by Ableton, not the OS.
**How to avoid:** Never import external packages in Remote Script code. Only use stdlib + `_Framework`. When splitting into modules, ensure all imports resolve within the package directory. Handler mixin classes should not import from MCP_Server.
**Warning signs:** `ModuleNotFoundError` when Ableton loads the script.

### Pitfall 3: Decorator Registration Timing
**What goes wrong:** Using `@command('name')` decorator on handler methods in domain modules, but the module is never imported, so handlers are never registered.
**Why it happens:** Python decorators execute at import time. If a module is never imported, its decorators never run.
**How to avoid:** Explicitly import ALL handler modules in `handlers/__init__.py`. The `__init__.py` must contain `from . import base, transport, tracks, clips, notes, devices, mixer, scenes, browser`.
**Warning signs:** "Unknown command" errors at runtime for commands that should exist.

### Pitfall 4: Mixin Method Resolution Order
**What goes wrong:** When using mixin classes to compose AbletonMCP, method name conflicts between mixins cause one handler to shadow another.
**Why it happens:** Python MRO picks the first matching method in the inheritance chain.
**How to avoid:** Use unique method names (already the case -- all handlers have domain-specific prefixes like `_get_track_info`, `_create_clip`). Alternatively, don't use mixin inheritance at all -- use the registry pattern where handlers are standalone functions that receive `self` via `build_tables()`.
**Warning signs:** Missing commands, or commands that silently call the wrong handler.

### Pitfall 5: Breaking pyproject.toml Entry Point
**What goes wrong:** The entry point `ableton-mcp = "MCP_Server.server:main"` breaks if `server.py` changes its location or if imports fail during module loading.
**Why it happens:** The entry point must resolve to a callable. If any import in the chain fails, the entry point fails.
**How to avoid:** Keep `main()` in `MCP_Server/server.py` and ensure all imports succeed. Test with `uv run ableton-mcp` after refactoring.
**Warning signs:** `ModuleNotFoundError` when running `ableton-mcp` CLI command.

### Pitfall 6: Test Fixtures Referencing Old File Paths
**What goes wrong:** Phase 1 test fixtures (`remote_script_source`, `server_source`) read specific file paths. After refactoring, the source code is spread across multiple files.
**Why it happens:** The grep-based test approach reads raw source text from specific files.
**How to avoid:** Update conftest.py fixtures to read from new module paths. Some Phase 1 tests (test_python3_cleanup.py, test_connection.py) grep source files -- these need updating to read from the correct new files. The protocol tests (test_protocol.py) are independent and need no changes.
**Warning signs:** `FileNotFoundError` or tests that pass vacuously because they're reading the wrong file.

### Pitfall 7: self-scheduling commands need special dispatch handling
**What goes wrong:** `load_browser_item` and `load_instrument_or_effect` manage their own `schedule_message` lifecycle. If routed through the standard `@main_thread` decorator, they get double-scheduled.
**Why it happens:** These commands use multi-tick patterns (schedule load, then schedule verify on next tick). The standard write-command pattern wraps everything in one `schedule_message` call.
**How to avoid:** The `@command` decorator needs a `self_scheduling=True` flag (or the dispatch logic needs to recognize these commands). The existing `_dispatch_write_command` already handles this case -- preserve that logic.
**Warning signs:** Timeouts or deadlocks on load_browser_item commands.

## Code Examples

### Complete CommandRegistry Implementation

```python
# AbletonMCP_Remote_Script/registry.py
"""Command registry with decorator-based handler registration.

Usage in handler modules:
    from AbletonMCP_Remote_Script.registry import command

    @command("get_session_info")
    def _get_session_info(self, params=None):
        ...

    @command("create_midi_track", write=True)
    def _create_midi_track(self, params):
        ...

    @command("load_browser_item", write=True, self_scheduling=True)
    def _load_browser_item(self, params):
        ...
"""


class CommandRegistry:
    """Collects @command-decorated handlers and builds dispatch tables."""

    _entries: list[tuple[str, str, bool, bool]] = []

    @classmethod
    def command(cls, name: str, *, write: bool = False, self_scheduling: bool = False):
        """Register a command handler.

        Args:
            name: Wire command name (e.g., 'get_session_info')
            write: If True, dispatched on Ableton's main thread
            self_scheduling: If True, handler manages its own schedule_message calls
        """
        def decorator(func):
            cls._entries.append((name, func.__name__, write, self_scheduling))
            return func
        return decorator

    @classmethod
    def build_tables(cls, instance):
        """Bind registered handlers to instance and return dispatch dicts.

        Returns:
            (read_commands, write_commands, self_scheduling_commands)
        """
        read_commands = {}
        write_commands = {}
        self_scheduling = set()
        for cmd_name, method_name, is_write, is_self_sched in cls._entries:
            handler = getattr(instance, method_name)
            if is_write:
                write_commands[cmd_name] = handler
                if is_self_sched:
                    self_scheduling.add(cmd_name)
            else:
                read_commands[cmd_name] = handler
        return read_commands, write_commands, self_scheduling


# Convenience alias for use in handler modules
command = CommandRegistry.command
```

### Ruff Configuration

```toml
# In pyproject.toml -- add these sections

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "W",   # pycodestyle warnings
    "I",   # isort (import ordering)
    "B",   # flake8-bugbear (common mistakes)
    "UP",  # pyupgrade (modernize syntax)
]
ignore = [
    "E501",  # line too long -- handled by line-length setting above
    "B905",  # zip() without strict= -- not needed for this project
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # unused imports OK in __init__.py (re-exports)
"tests/**/*.py" = ["B011"]  # assert False OK in tests
"AbletonMCP_Remote_Script/**/*.py" = [
    "UP035",  # deprecated import -- _Framework uses old patterns we can't control
]

[tool.ruff.lint.isort]
known-first-party = ["MCP_Server", "AbletonMCP_Remote_Script"]
```

### FastMCP In-Memory Test Pattern (Verified Working with mcp 1.4.0)

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_connection():
    """Mock AbletonConnection with canned responses."""
    mock = MagicMock()
    mock.send_command.return_value = {}
    # Patch at the connection module level
    with patch("MCP_Server.connection._ableton_connection", mock), \
         patch("MCP_Server.connection.get_ableton_connection", return_value=mock):
        yield mock


@pytest.fixture
def mcp_server():
    """Return the live FastMCP server instance."""
    from MCP_Server.server import mcp
    return mcp


# tests/test_tracks.py
import json
import pytest


async def test_track_tools_registered(mcp_server):
    """All track domain tools are registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_track_info" in names
    assert "create_midi_track" in names
    assert "set_track_name" in names


async def test_get_track_info_response(mcp_server, mock_connection):
    """get_track_info returns formatted track data."""
    mock_connection.send_command.return_value = {
        "index": 0,
        "name": "Bass",
        "is_midi_track": True,
        "devices": [],
    }
    result = await mcp_server.call_tool("get_track_info", {"track_index": 0})
    # call_tool returns Sequence[TextContent|ImageContent|EmbeddedResource]
    data = json.loads(result[0].text)
    assert data["name"] == "Bass"
    mock_connection.send_command.assert_called_once_with(
        "get_track_info", {"track_index": 0}
    )
```

### MCP Tool Module with Standardized Naming

```python
# MCP_Server/tools/transport.py
"""Transport control tools: playback, tempo, time signature."""

import json
from mcp.server.fastmcp import Context
from MCP_Server.server import mcp
from MCP_Server.connection import get_ableton_connection, format_error


@mcp.tool()
def start_playback(ctx: Context) -> str:
    """Start playing the Ableton session.

    Begins playback from the current position. Use stop_playback to halt.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("start_playback")
        return "Started playback"
    except Exception as e:
        return format_error(
            "Failed to start playback",
            detail=str(e),
            suggestion="Verify connection with get_connection_status"
        )


@mcp.tool()
def set_tempo(ctx: Context, tempo: float) -> str:
    """Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM (20-999)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_tempo", {"tempo": tempo})
        return f"Set tempo to {tempo} BPM"
    except Exception as e:
        return format_error(
            "Failed to set tempo",
            detail=str(e),
            suggestion="Tempo must be between 20 and 999 BPM"
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single monolithic server.py (797 lines) | Domain-organized tools/ package | Phase 2 (this phase) | Adding new tools requires touching only one file |
| if/elif dispatch chain | dict-based dispatch (Phase 1) -> @command registry (Phase 2) | Phase 1 -> Phase 2 | O(1) lookup, self-documenting, extensible |
| Manual import ordering | ruff "I" rules (isort) | Phase 2 (this phase) | Automatic, deterministic, CI-enforceable |
| No linting | ruff with E+F+W+I+B+UP | Phase 2 (this phase) | Catches bugs, enforces consistency |
| Grep-based source tests | FastMCP call_tool + mock connection tests | Phase 2 (this phase) | Tests actual tool behavior, not string patterns |

**Deprecated/outdated:**
- `_build_command_table()` method: Replaced by `CommandRegistry.build_tables()` called from `__init__`
- Grep-based tests (test_python3_cleanup.py, test_dispatch.py): Most should be replaced with behavioral tests. test_protocol.py is still valid.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.25+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` (already exists) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v --timeout=10` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FNDN-07 | MCP tools organized into domain modules | smoke | `uv run pytest tests/test_session.py tests/test_tracks.py tests/test_clips.py tests/test_transport.py -x` | Wave 0 |
| FNDN-07 | All 17 existing tools still registered | smoke | `uv run pytest tests/test_session.py::test_all_tools_registered -x` | Wave 0 |
| FNDN-08 | Remote Script handlers in domain modules with registry | unit | `uv run pytest tests/test_registry.py -x` | Wave 0 |
| FNDN-09 | Ruff linting passes | lint | `uv run ruff check MCP_Server/ AbletonMCP_Remote_Script/ tests/` | Wave 0 |
| FNDN-10 | Test infrastructure with FastMCP in-memory client | smoke | `uv run pytest tests/ -x -q` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v --timeout=10 && uv run ruff check MCP_Server/ AbletonMCP_Remote_Script/`
- **Phase gate:** Full suite green + ruff check clean before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_session.py` -- covers FNDN-07 session tools registration and smoke
- [ ] `tests/test_tracks.py` -- covers FNDN-07 tracks tools registration and smoke
- [ ] `tests/test_clips.py` -- covers FNDN-07 clips tools registration and smoke
- [ ] `tests/test_transport.py` -- covers FNDN-07 transport tools registration and smoke
- [ ] `tests/test_devices.py` -- covers FNDN-07 devices tools registration and smoke
- [ ] `tests/test_browser.py` -- covers FNDN-07 browser tools registration and smoke
- [ ] `tests/test_registry.py` -- covers FNDN-08 command registry decorator
- [ ] Updated `tests/conftest.py` -- mock_connection fixture, mcp_server fixture
- [ ] `pyproject.toml` ruff config -- covers FNDN-09
- [ ] `ruff` dev dependency -- `uv add --dev ruff`

## Open Questions

1. **Ableton Remote Script package imports**
   - What we know: Remote Script runs in Ableton's embedded Python 3.11. Standard packages in the script directory are importable. `from _Framework.ControlSurface import ControlSurface` works.
   - What's unclear: Whether relative imports (`from .handlers import tracks`) work reliably in Ableton's import system, or whether absolute imports (`from AbletonMCP_Remote_Script.handlers import tracks`) are needed.
   - Recommendation: Start with relative imports (standard Python). If they fail in Ableton, switch to absolute. This only affects the Remote Script side. Phase 2 is tested by running pytest (MCP server side) and verifying structure (Remote Script side) -- actual Ableton testing happens during integration.

2. **Phase 1 grep-based tests: keep or rewrite?**
   - What we know: 5 test files exist. test_protocol.py tests socket framing (keep as-is). test_python3_cleanup.py, test_connection.py, test_dispatch.py, test_instrument_loading.py all grep source files.
   - What's unclear: Whether some grep tests still provide value after refactoring (e.g., verifying no bare excepts across all new modules).
   - Recommendation: Keep test_protocol.py unchanged. Rewrite test_dispatch.py as test_registry.py (test the new registry). Retire test_python3_cleanup.py and test_connection.py (their invariants are now enforced by ruff rules and behavioral tests). Retire test_instrument_loading.py (replace with mock-based test in test_devices.py or test_browser.py).

3. **MCP tool modules: mirror Remote Script or group differently?**
   - What we know: User wants tools/ to mirror Remote Script domains. But the MCP server has a "session" concept (get_connection_status + get_session_info) that doesn't map to a Remote Script handler domain.
   - What's unclear: Whether to create a `tools/session.py` for connection/session tools or put them elsewhere.
   - Recommendation: Create `tools/session.py` for get_connection_status and get_session_info. These are "meta" tools that don't map to a single Remote Script domain but form a logical group. All other tool modules mirror Remote Script domains exactly.

## Sources

### Primary (HIGH confidence)
- Direct testing of mcp 1.4.0 API: `FastMCP.call_tool()` and `list_tools()` are async methods that work directly on the server instance without needing a separate client (verified locally)
- `FastMCP.tool()` decorator signature: `(self, name: str | None = None, description: str | None = None)` (verified locally)
- Existing codebase analysis: All file contents read directly from source

### Secondary (MEDIUM confidence)
- [FastMCP Testing Documentation](https://gofastmcp.com/servers/testing) - pytest-asyncio integration patterns
- [Ruff Configuration Documentation](https://docs.astral.sh/ruff/configuration/) - pyproject.toml format for lint rules
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/) - rule category descriptions
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) - SDK architecture
- [MCPcat Unit Testing Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers/) - testing patterns for MCP servers
- [GitHub Issue #1252](https://github.com/modelcontextprotocol/python-sdk/issues/1252) - Recommended unit testing approach for MCP endpoints

### Tertiary (LOW confidence)
- [Python Registry Pattern](https://medium.com/@tihomir.manushev/implementing-the-registry-pattern-with-decorators-in-python-de8daf4a452a) - decorator registry implementation patterns (general Python, not project-specific)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all dependencies already in use, versions verified locally
- Architecture: HIGH - patterns derived from reading actual source code and testing FastMCP API
- Pitfalls: HIGH - based on direct codebase analysis and known Python module system behavior
- Testing: HIGH - FastMCP call_tool/list_tools verified working locally with mcp 1.4.0
- Ruff config: MEDIUM - rule selection based on documentation; exact per-file-ignores may need tuning during implementation

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable domain -- Python packaging and linting tools change slowly)
