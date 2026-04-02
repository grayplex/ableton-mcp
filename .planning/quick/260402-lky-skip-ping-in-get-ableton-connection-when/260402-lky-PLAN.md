---
phase: quick
plan: 260402-lky
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/connection.py
  - tests/test_connection_thread_safety.py
  - .planning/codebase/CONCERNS.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "get_ableton_connection() returns immediately when connection is healthy (no ping round-trip)"
    - "get_ableton_connection() pings when connection was previously errored"
    - "get_ableton_connection() pings when creating a fresh connection"
    - "send_command sets _healthy=False on any socket/communication exception"
    - "Thread safety is preserved — _healthy is only read/written under appropriate locks"
  artifacts:
    - path: "MCP_Server/connection.py"
      provides: "_healthy flag on AbletonConnection, skip-ping fast path in get_ableton_connection"
    - path: "tests/test_connection_thread_safety.py"
      provides: "Tests for healthy skip-ping, unhealthy re-ping, and error flag behaviors"
  key_links:
    - from: "get_ableton_connection()"
      to: "AbletonConnection._healthy"
      via: "check _healthy before pinging; skip if True"
      pattern: "_ableton_connection._healthy"
    - from: "AbletonConnection.send_command"
      to: "AbletonConnection._healthy"
      via: "set False in exception handlers, True on success"
      pattern: "self._healthy ="
---

<objective>
Skip the ping round-trip in get_ableton_connection() when the socket is already healthy.

Purpose: Every MCP tool call currently holds _connection_lock and does a ping (up to 5s timeout) before returning. This serializes all concurrent tool calls behind a blocking ping. By tracking connection health with a _healthy flag, we skip the ping on the hot path and only re-validate after errors or fresh connections.

Output: Modified connection.py with _healthy flag, updated tests, resolved CONCERNS.md entry.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@MCP_Server/connection.py
@tests/test_connection_thread_safety.py
@.planning/codebase/CONCERNS.md
</context>

<interfaces>
<!-- Key types and contracts the executor needs. -->

From MCP_Server/connection.py:
```python
@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: socket.socket = None
    _send_lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False, compare=False
    )

    def connect(self) -> bool: ...
    def disconnect(self): ...
    def send_command(self, command_type: str, params: dict[str, Any] = None, timeout: float | None = None) -> dict[str, Any]: ...

# Global connection management
_ableton_connection = None
_connection_lock = threading.Lock()

def get_ableton_connection(): ...
def shutdown_connection(): ...
```

Lock hierarchy:
- `_connection_lock` (global) — guards `_ableton_connection` singleton access
- `_send_lock` (per-connection) — serializes socket write+read within a single connection
- `_healthy` will be read/written ONLY while `_connection_lock` is held (in get_ableton_connection) or while `_send_lock` is held (in send_command), so no data race.
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add _healthy flag and skip-ping fast path</name>
  <files>MCP_Server/connection.py, tests/test_connection_thread_safety.py</files>
  <behavior>
    - Test: AbletonConnection instance has _healthy attribute, initially False
    - Test: get_ableton_connection() skips ping when _ableton_connection is not None and _healthy is True — mock send_command, verify it is NOT called when _healthy=True
    - Test: get_ableton_connection() pings when _ableton_connection exists but _healthy is False — verify send_command("ping") IS called
    - Test: send_command sets _healthy=True after successful response (no exception)
    - Test: send_command sets _healthy=False when TimeoutError, ConnectionError, BrokenPipeError, ConnectionResetError, or JSONDecodeError occurs (before re-raising)
    - Test: New connection creation path (connect + get_session_info validation) sets _healthy=True on success
  </behavior>
  <action>
    1. In AbletonConnection.__init__ (the dataclass fields), add:
       `_healthy: bool = field(default=False, init=False, repr=False, compare=False)`

    2. In send_command, INSIDE the `with self._send_lock:` block:
       - After the successful `return response.get("result", {})` line (line 161), add `self._healthy = True` BEFORE the return. Specifically, after line 160 (`return response.get("result", {})`) restructure so _healthy is set before returning:
         ```python
         result = response.get("result", {})
         self._healthy = True
         return result
         ```
       - In EACH except block (TimeoutError, ConnectionError/BrokenPipeError/ConnectionResetError, JSONDecodeError, generic Exception) at lines 162-180, add `self._healthy = False` BEFORE `self.sock = None`.

    3. In get_ableton_connection(), modify the existing connection check block (lines 207-218):
       - After `if _ableton_connection is not None:` (line 207), add a fast-path check:
         ```python
         if _ableton_connection._healthy:
             return _ableton_connection
         ```
       - Keep the existing try/except ping block for when _healthy is False (the connection exists but needs re-validation).

    4. In the new-connection creation path (around line 232-234), after `_ableton_connection.send_command("get_session_info")` succeeds, `_healthy` will already be True (set by send_command itself). No extra line needed there.

    5. Add tests to tests/test_connection_thread_safety.py (or a new class within it) covering all behaviors listed above. Use unittest.mock.patch on `MCP_Server.connection._ableton_connection` and `MCP_Server.connection._connection_lock` as needed. For the skip-ping test, set up a mock AbletonConnection with _healthy=True and sock=MagicMock(), patch the global, call get_ableton_connection(), and assert send_command was NOT called.
  </action>
  <verify>
    <automated>cd /home/user/ableton-mcp && python -m pytest tests/test_connection_thread_safety.py -x -v 2>&1 | tail -30</automated>
  </verify>
  <done>
    - AbletonConnection has _healthy=False by default
    - get_ableton_connection() returns immediately (no ping) when _healthy is True
    - get_ableton_connection() pings when _healthy is False
    - send_command sets _healthy=True on success, False on any exception
    - All new and existing tests pass
  </done>
</task>

<task type="auto">
  <name>Task 2: Update CONCERNS.md — remove resolved performance entry</name>
  <files>.planning/codebase/CONCERNS.md</files>
  <action>
    In .planning/codebase/CONCERNS.md, under "## Performance Concerns", remove or mark as resolved the entry:
    "**`get_ableton_connection()` pings on every call while holding the global lock:**"
    (lines 45-47 of CONCERNS.md).

    Replace it with a brief resolved note:
    ```
    **`get_ableton_connection()` pings on every call while holding the global lock:** RESOLVED (260402-lky) — Added `_healthy` flag; ping skipped when connection is healthy.
    ```
  </action>
  <verify>
    <automated>cd /home/user/ableton-mcp && grep -c "RESOLVED (260402-lky)" .planning/codebase/CONCERNS.md</automated>
  </verify>
  <done>CONCERNS.md entry for get_ableton_connection ping is marked as resolved.</done>
</task>

</tasks>

<verification>
- All existing tests in test_connection_thread_safety.py still pass (thread safety preserved)
- New tests cover: healthy skip-ping, unhealthy re-ping, _healthy flag transitions
- No behavioral change for callers of get_ableton_connection() or send_command (same return values, same exceptions)
</verification>

<success_criteria>
- get_ableton_connection() hot path has zero socket round-trips when connection is healthy
- Connection errors correctly invalidate _healthy, triggering re-validation on next call
- All tests pass: `python -m pytest tests/test_connection_thread_safety.py -x -v`
</success_criteria>

<output>
After completion, create `.planning/quick/260402-lky-skip-ping-in-get-ableton-connection-when/260402-lky-SUMMARY.md`
</output>
