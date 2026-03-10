# Coding Conventions

**Analysis Date:** 2026-03-10

## Naming Patterns

**Files:**
- Private/internal module files use underscores: `_Framework`, `_get_session_info`
- Standard Python convention: lowercase with underscores for module names

**Functions:**
- Private/internal functions prefixed with single underscore: `_get_session_info()`, `_handle_client()`, `_process_command()`
- Public tool functions (MCP decorators) are lowercase with underscores: `get_session_info()`, `set_track_name()`, `create_midi_track()`
- Methods follow snake_case convention: `send_command()`, `receive_full_response()`, `get_ableton_connection()`

**Variables:**
- Instance variables use snake_case: `self.sock`, `self.host`, `self.port`, `self.running`
- Local variables use snake_case: `buffer`, `response_queue`, `client_thread`
- Constants use UPPER_SNAKE_CASE: `DEFAULT_PORT = 9877`, `HOST = "localhost"`
- Private/internal variables prefixed with underscore: `_ableton_connection`, `_song`

**Classes:**
- PascalCase for class names: `AbletonConnection`, `AbletonMCP`, `ControlSurface`
- Dataclass uses `@dataclass` decorator: `AbletonConnection` is a dataclass

**Type Hints:**
- Functions include return type hints: `def send_command(...) -> Dict[str, Any]:`
- Parameter types are annotated: `def get_track_info(ctx: Context, track_index: int) -> str:`
- Complex types use typing module: `Dict[str, Any]`, `List[Dict[str, Union[int, float, bool]]]`, `AsyncIterator[Dict[str, Any]]`

## Code Style

**Formatting:**
- Imports are organized with standard library first, then third-party
- No explicit formatter detected (Prettier/Black/isort not configured)
- Line length appears to exceed 100 characters (no configuration enforced)
- Indentation: 4 spaces

**Linting:**
- No ESLint, Prettier, or similar tools detected
- No `.flake8` or `pyproject.toml` linting configuration found
- Code follows general PEP 8 conventions but not strictly enforced

**Docstring Style:**
- Triple-quoted docstrings for functions and classes
- Docstrings include purpose and parameter descriptions
- Format: standard Python docstring (not Google or NumPy style)
- Example from `server.py`:
  ```python
  def get_track_info(ctx: Context, track_index: int) -> str:
      """
      Get detailed information about a specific track in Ableton.

      Parameters:
      - track_index: The index of the track to get information about
      """
  ```

## Import Organization

**Order:**
1. Standard library imports (logging, json, socket, threading, time, traceback)
2. Dataclasses and contextlib utilities
3. Typing module imports
4. Third-party framework imports (mcp, _Framework)

**Example from `server.py`:**
```python
from mcp.server.fastmcp import FastMCP, Context
import socket
import json
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Union
```

**Path Aliases:**
- No path aliases detected
- Imports use full module paths: `from mcp.server.fastmcp import FastMCP`

## Error Handling

**Patterns:**
- Broad try/except blocks catching generic `Exception`
- Specific exception handling for known errors: `socket.timeout`, `json.JSONDecodeError`, `ConnectionError`, `BrokenPipeError`, `ConnectionResetError`
- Re-raise pattern: catch, log, then raise with custom message
- Inner try/except for recovery and retry logic (connection retry loops)

**Common Error Handling Structure:**
```python
try:
    # Main logic
    ableton.send_command("command_type")
except socket.timeout:
    logger.error("Socket timeout...")
    raise Exception("Timeout message")
except (ConnectionError, BrokenPipeError) as e:
    logger.error(f"Connection error: {str(e)}")
    raise Exception(f"Custom error: {str(e)}")
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {str(e)}")
    raise Exception(f"Parse error: {str(e)}")
except Exception as e:
    logger.error(f"Generic error: {str(e)}")
    raise Exception(f"Communication error: {str(e)}")
```

**Cleanup Patterns:**
- `finally` blocks used for resource cleanup (socket closing, thread cleanup)
- Example: `finally: client.close()`

## Logging

**Framework:** Python's built-in `logging` module

**Logger Setup:**
```python
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AbletonMCPServer")
```

**Patterns:**
- `logger.info()` for operational messages: connection established, command sent, response received
- `logger.warning()` for non-critical issues: timeout, connection lost but recovered
- `logger.error()` for failures and exceptions
- All exceptions logged before returning error to caller
- Informational logging includes data sizes and status: `logger.info(f"Received {len(response_data)} bytes")`

**Logging Philosophy:**
- Diagnostic logging for socket operations (connect, send, receive)
- Status updates for state changes (connection valid, task timeout)
- Error logging with full context (raw data, exception details)

**Remote Script Logging:**
- Uses Ableton's built-in logging: `self.log_message()` and `self.show_message()`
- `log_message()` for internal logging
- `show_message()` for user-facing messages in Ableton UI
- Example: `self.log_message("AbletonMCP initialized")`

## Comments

**When to Comment:**
- Comments used for clarifying algorithm intent (e.g., "Check if we've received a complete JSON object")
- Comments used for explaining platform-specific behavior (e.g., "Python 2 vs Python 3" branching)
- Comments used for state-modifying operation classification (e.g., "Check if this is a state-modifying command")
- No over-commenting; code is generally self-documenting

**Comment Style:**
- Single-line comments use `#` followed by space
- Inline comments for complex logic or non-obvious behavior
- Example: `# For state-modifying commands, add a small delay to give Ableton time to process`

## Function Design

**Size:**
- Small to medium functions (20-60 lines typical)
- Larger functions (100+ lines) used for complex socket operations with multiple try/except branches
- Example: `send_command()` is 52 lines; `_process_command()` is 118 lines

**Parameters:**
- Simple, minimal parameters preferred
- Complex data passed as dictionaries: `params: Dict[str, Any]`
- Type hints required for all parameters
- Default values used for optional parameters: `index: int = -1`, `category_type: str = "all"`

**Return Values:**
- Functions return structured data (dicts, strings) for API functions
- Tool functions return JSON-serializable strings
- Internal methods return typed dictionaries for composition

**Async Patterns:**
- Async context manager used for server lifecycle: `@asynccontextmanager`
- FastMCP framework handles async execution
- Tool implementations are sync (decorated with `@mcp.tool()`)

## Module Design

**Exports:**
- Public API exposed in `__init__.py` files
- Example from `MCP_Server/__init__.py`:
  ```python
  from .server import AbletonConnection, get_ableton_connection
  ```

**Barrel Files:**
- Minimal barrel file pattern
- `MCP_Server/__init__.py` exports key classes and functions
- `AbletonMCP_Remote_Script/__init__.py` contains all implementation (no sub-modules)

**Dataclass Usage:**
- `AbletonConnection` implemented as dataclass with manual socket attribute
- Contains both data fields (host, port) and methods (connect, disconnect, send_command)

**Global State:**
- Single global variable for persistent connection: `_ableton_connection`
- Accessed through getter function: `get_ableton_connection()`
- Connection lifecycle managed by server lifespan context manager

## Platform Compatibility

**Python 2/3 Compatibility:**
- Code supports both Python 2 and Python 3
- Conditional imports: `try: import Queue as queue` / `except: import queue`
- Encoding/decoding branching: `try: data.decode('utf-8')` / `except AttributeError: data` (already string)
- String handling with explicit encoding: `json.dumps(response).encode('utf-8')`
- Example from `AbletonMCP_Remote_Script/__init__.py`:
  ```python
  try:
      buffer += data.decode('utf-8')  # Python 3
  except AttributeError:
      buffer += data  # Python 2
  ```

---

*Convention analysis: 2026-03-10*
