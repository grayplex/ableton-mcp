---
phase: quick-260401-qhm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/connection.py
autonomous: true
requirements: [THREAD-SAFE-01]

must_haves:
  truths:
    - "Concurrent send_command calls on the same AbletonConnection serialize — socket write+read pairs never interleave"
    - "send_command acquires the per-connection lock before send_message and releases it after recv_message"
    - "All existing tests pass"
  artifacts:
    - path: "MCP_Server/connection.py"
      provides: "_send_lock field on AbletonConnection, lock acquisition in send_command"
      contains: "_send_lock"
  key_links:
    - from: "AbletonConnection._send_lock"
      to: "send_command try block"
      via: "with self._send_lock:"
      pattern: "with self\\._send_lock"
---

<objective>
Add a per-connection `_send_lock` to `AbletonConnection` and acquire it around the
`send_message` + `recv_message` calls in `send_command`, so concurrent FastMCP tool
dispatches cannot interleave their socket I/O.

Purpose: Prevent response corruption when two tools call `send_command` simultaneously
on the shared `_ableton_connection` singleton.
Output: `MCP_Server/connection.py` with thread-safe socket I/O.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@MCP_Server/connection.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rebase onto misc-fixes</name>
  <files></files>
  <action>
    From the worktree for this quick task, rebase onto the latest `misc-fixes` branch
    so all recent parallel-agent changes are included before modifying connection.py:

    ```
    git fetch origin
    git rebase origin/misc-fixes
    ```

    If there are no conflicts, proceed. If conflicts exist in connection.py, resolve them
    by keeping both sides (the rebase changes AND the incoming changes) — the subsequent
    task will apply the thread-safety fix on top of the resolved file.
  </action>
  <verify>
    <automated>git log --oneline -5</automated>
  </verify>
  <done>Worktree is rebased onto misc-fixes with no outstanding conflicts.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Add _send_lock to AbletonConnection and acquire in send_command</name>
  <files>MCP_Server/connection.py, tests/test_connection_thread_safety.py</files>
  <behavior>
    - Test 1: Two threads calling send_command concurrently never interleave their
      send_message/recv_message pairs — mock socket verifies strict alternation.
    - Test 2: A fresh AbletonConnection instance has a `_send_lock` attribute that is
      a `threading.Lock` (not None).
    - Test 3: Existing send_command happy-path still returns the correct response dict.
  </behavior>
  <action>
    Modify `MCP_Server/connection.py`:

    1. Add `dataclasses.field` import — change the import line:
       `from dataclasses import dataclass` → `from dataclasses import dataclass, field`

    2. Inside the `AbletonConnection` dataclass, add the lock as a field after `sock`:
       ```python
       _send_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False, compare=False)
       ```
       Using `init=False` keeps the constructor signature unchanged (host, port, sock
       are the only user-supplied fields). `repr=False` and `compare=False` keep the
       dataclass behaviour clean.

    3. In `send_command`, wrap the entire try/except block with the lock. The lock must
       be acquired BEFORE the try so the except branches that null out `self.sock` also
       run while the lock is held (prevents a second thread seeing a half-torn-down
       socket). Change:

       ```python
       try:
           logger.info(...)
           send_message(self.sock, command)
           ...
       except ...:
           ...
       ```

       to:

       ```python
       with self._send_lock:
           try:
               logger.info(...)
               send_message(self.sock, command)
               ...
           except ...:
               ...
       ```

    Do NOT move the pre-flight `if not self.sock and not self.connect():` check inside
    the lock — it is intentionally outside to avoid deadlock when `connect()` itself
    calls `send_command("get_session_info")` during `get_ableton_connection`. The lock
    guards only the socket I/O, not the connection setup.

    Write `tests/test_connection_thread_safety.py` with the three test cases above,
    using `unittest.mock.patch` to mock `send_message` and `recv_message` from
    `MCP_Server.connection`. Use threading.Barrier or event ordering assertions to
    verify serialisation in Test 1.
  </action>
  <verify>
    <automated>python -m pytest tests/test_connection_thread_safety.py -v</automated>
  </verify>
  <done>
    All three new tests pass. `AbletonConnection()` has a `_send_lock` field.
    `send_command` wraps its try/except in `with self._send_lock:`.
    The pre-flight reconnect check remains outside the lock.
  </done>
</task>

<task type="auto">
  <name>Task 3: Run full test suite and confirm no regressions</name>
  <files></files>
  <action>
    Run the full test suite to verify no existing tests are broken by the change:

    ```
    python -m pytest tests/ -v
    ```

    If failures occur, inspect the error — likely a test that constructs
    `AbletonConnection` with positional args. The `_send_lock` field uses
    `init=False` so it must NOT appear as a constructor argument; verify the
    dataclass field declaration is correct if issues arise.
  </action>
  <verify>
    <automated>python -m pytest tests/ -v --tb=short 2>&1 | tail -20</automated>
  </verify>
  <done>All tests pass (new thread-safety tests + all pre-existing tests).</done>
</task>

</tasks>

<verification>
- `grep -n "_send_lock" MCP_Server/connection.py` shows two hits: field declaration and `with self._send_lock:` in send_command.
- `grep -n "with self._send_lock" MCP_Server/connection.py` shows the lock wrapping the try/except, not just send_message.
- `python -m pytest tests/ -q` exits 0.
</verification>

<success_criteria>
- `AbletonConnection` dataclass has `_send_lock: threading.Lock = field(default_factory=threading.Lock, init=False, ...)`.
- `send_command` body is `with self._send_lock: try: ... except ...:`.
- Pre-flight reconnect check (`if not self.sock`) remains outside the lock.
- All tests pass including the new concurrency tests.
</success_criteria>

<output>
After completion, create `.planning/quick/260401-qhm-make-send-command-thread-safe-by-holding/260401-qhm-SUMMARY.md`
</output>
