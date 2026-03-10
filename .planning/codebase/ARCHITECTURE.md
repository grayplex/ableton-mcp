# Architecture

**Analysis Date:** 2026-03-10

## Pattern Overview

**Overall:** Client-Server Bridge Pattern with MCP (Model Context Protocol) adapter

**Key Characteristics:**
- Two-tier architecture: MCP Server (Claude-facing) bridges to Ableton Remote Script (DAW-facing)
- Socket-based JSON command-response protocol for inter-process communication
- Lifespan-managed connection pooling with automatic reconnection
- Thread-safe command queuing for Ableton's main thread requirements
- Asynchronous tool execution via FastMCP framework

## Layers

**MCP Server Layer (Claude Interface):**
- Purpose: Implements Model Context Protocol tools for Claude AI to invoke
- Location: `MCP_Server/server.py`
- Contains: Tool definitions, async handlers, connection management
- Depends on: FastMCP framework, socket communication, JSON serialization
- Used by: Claude AI, Cursor IDE

**Connection Layer:**
- Purpose: Manages persistent socket connection to Ableton Remote Script
- Location: `MCP_Server/server.py` (AbletonConnection class)
- Contains: Socket lifecycle management, command serialization, response deserialization
- Depends on: Python socket module, JSON encoding/decoding
- Used by: All tool handlers

**Ableton Remote Script Layer (DAW Control):**
- Purpose: Embedded MIDI Remote Script in Ableton Live that executes commands on DAW
- Location: `AbletonMCP_Remote_Script/__init__.py`
- Contains: Socket server, command handler, Ableton Live API interaction
- Depends on: Ableton's _Framework, threading, queue management
- Used by: Connection Layer (receives commands from)

## Data Flow

**Command Execution Flow:**

1. Claude invokes MCP tool (e.g., `create_midi_track`)
2. Tool handler calls `get_ableton_connection()` to get persistent socket connection
3. Tool serializes parameters into JSON command with `type` and `params`
4. AbletonConnection sends JSON command to Remote Script socket server on `localhost:9877`
5. Remote Script receives JSON command in `_handle_client()`
6. For query commands: direct processing and response
7. For state-modifying commands: queued on Ableton main thread via `schedule_message()`
8. Remote Script waits for main thread task completion (timeout: 10 seconds)
9. Response (JSON with `status` and `result`) sent back to MCP server
10. Tool handler parses response and returns formatted string to Claude

**Error Recovery:**
- Connection timeout triggers automatic reconnection (up to 3 attempts)
- Failed commands reset socket to None, forcing reconnection on next tool call
- Main thread task timeouts return error status with descriptive message

## State Management

**Global Connection State:**
- `_ableton_connection` (module-level global) holds AbletonConnection instance
- Lazily initialized on first tool invocation
- Validated on each tool call (sends test byte to verify socket alive)
- Gracefully disconnected on server shutdown via lifespan handler

**Ableton Session State:**
- Remote Script maintains reference to `song` object via `self._song = self.song()`
- Track, clip, and device access via Ableton's Live API (indices-based)
- Session tempo, time signature, track count cached per request

## Key Abstractions

**AbletonConnection:**
- Purpose: Encapsulates socket communication protocol with Ableton
- Examples: `AbletonMCP_Remote_Script/__init__.py`
- Pattern: Dataclass with methods for connect(), disconnect(), send_command()
- Responsibilities: Socket lifecycle, JSON serialization/deserialization, response assembly (handles multi-chunk responses)

**Tool Handlers:**
- Purpose: FastMCP tool decorators that translate Claude requests to Ableton commands
- Examples: `get_session_info()`, `create_midi_track()`, `add_notes_to_clip()`
- Pattern: Async functions wrapped with `@mcp.tool()` decorator
- Responsibilities: Parameter validation, error handling, result formatting

**Command Router:**
- Purpose: Maps JSON command type to handler implementation in Remote Script
- Examples: `_process_command()` in Remote Script checks `command_type`
- Pattern: if/elif chain routing to `_<command>()` handler methods
- Responsibilities: Command dispatch, response wrapping, error handling

## Entry Points

**MCP Server Entry:**
- Location: `MCP_Server/server.py:main()`
- Triggers: Invoked by `ableton-mcp` console script (configured in `pyproject.toml`)
- Responsibilities: Instantiate FastMCP, start lifespan, run event loop

**Ableton Remote Script Entry:**
- Location: `AbletonMCP_Remote_Script/__init__.py:create_instance()`
- Triggers: Ableton Live loads control surface from User Remote Scripts directory
- Responsibilities: Instantiate AbletonMCP class, initialize socket server

**Tool Registration:**
- All tools decorated with `@mcp.tool()` on FastMCP instance
- Tools auto-discovered by MCP framework for schema generation

## Error Handling

**Strategy:** Three-tier error handling with graceful degradation

**Patterns:**

1. **Socket Level (AbletonConnection):**
   - `socket.timeout`: Logs timeout, returns new connection attempt
   - `ConnectionError`, `BrokenPipeError`: Sets socket to None, forces reconnect
   - `json.JSONDecodeError`: Logs raw response (first 200 bytes), raises exception

2. **Command Level (Tool Handlers):**
   - Try/except wrapping all tool invocations
   - Returns error string prefixed with "Error" to Claude
   - Never raises exceptions; always returns string response

3. **Remote Script Level:**
   - Main thread task wrapped in try/except
   - Errors placed in response queue with `{"status": "error", "message": ...}`
   - Timeout waiting for main thread task: returns error after 10 seconds
   - Client handler catches all exceptions, sends JSON error response, attempts recovery

## Cross-Cutting Concerns

**Logging:**
- Approach: Python logging module configured at INFO level
- Located in: Module-level logger `logger = logging.getLogger("AbletonMCPServer")`
- Captures: Connection state changes, command flow, errors with tracebacks

**Validation:**
- Parameter validation at tool level: type hints on function signatures
- Index bounds checking: Track index, clip index validation in Remote Script handlers
- Status checking: Verifies response status before extracting result

**Thread Safety:**
- Approach: Main thread task scheduling via Ableton's `schedule_message()` API
- Queue-based synchronization: Response queue for main thread task completion
- No direct thread access to Ableton Live API (only from main thread)

**Connection Management:**
- State-modifying commands: 15-second timeout for socket operations
- Query commands: 10-second timeout for socket operations
- Automatic reconnection with 3 retry attempts, 1-second delay between attempts
- Connection validation via empty byte send on each tool invocation

## Communication Protocol

**JSON Command Format (MCP → Remote Script):**
```json
{
  "type": "create_midi_track",
  "params": {
    "index": -1
  }
}
```

**JSON Response Format (Remote Script → MCP):**
```json
{
  "status": "success",
  "result": {
    "index": 0,
    "name": "MIDI Track 1"
  }
}
```

**Error Response Format:**
```json
{
  "status": "error",
  "message": "Track index out of range"
}
```

---

*Architecture analysis: 2026-03-10*
