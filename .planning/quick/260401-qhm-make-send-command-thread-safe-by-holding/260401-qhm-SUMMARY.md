---
phase: quick-260401-qhm
plan: 01
subsystem: connection
tags: [thread-safety, concurrency, socket, locking]
dependency_graph:
  requires: []
  provides: [thread-safe send_command]
  affects: [MCP_Server/connection.py]
tech_stack:
  added: [threading.Lock via dataclasses.field]
  patterns: [with-lock wrapping try/except, dataclass field with init=False]
key_files:
  created: [tests/test_connection_thread_safety.py]
  modified: [MCP_Server/connection.py]
decisions:
  - Lock acquired outside try/except (wraps it) so error-handling branches that null self.sock also run under the lock, preventing a second thread seeing a half-torn-down socket
  - Pre-flight reconnect check (if not self.sock) intentionally left outside lock to avoid deadlock when get_ableton_connection calls send_command("get_session_info") while holding _connection_lock
  - dataclasses.field with init=False keeps AbletonConnection constructor signature unchanged
metrics:
  duration: ~15m
  completed: 2026-04-01
---

# Quick 260401-qhm: Make send_command Thread-Safe by Holding Lock Summary

**One-liner:** Added `_send_lock: threading.Lock` field to `AbletonConnection` dataclass and wrapped `send_command`'s try/except with `with self._send_lock:` to serialize concurrent socket I/O.

## What Was Done

Concurrent FastMCP tool dispatches share a single `_ableton_connection` singleton. Without a per-connection lock, two simultaneous `send_command` calls could interleave their `send_message`/`recv_message` pairs, causing response corruption (thread A's response received by thread B).

The fix:
1. Added `from dataclasses import dataclass, field` (extended import).
2. Added `_send_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False, compare=False)` to the `AbletonConnection` dataclass — `init=False` keeps the constructor signature unchanged.
3. Wrapped the entire `try/except` block in `send_command` with `with self._send_lock:`. The lock is acquired BEFORE the try so all exception branches (which null `self.sock`) also run under the lock.
4. The pre-flight `if not self.sock and not self.connect():` check remains outside the lock to avoid deadlock when `get_ableton_connection` calls `send_command("get_session_info")` while already holding `_connection_lock`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rebase onto misc-fixes | (no commit - rebase) | - |
| 2 (RED) | Add failing thread-safety tests | b38089f | tests/test_connection_thread_safety.py |
| 2 (GREEN) | Implement _send_lock in AbletonConnection | 035e8d5 | MCP_Server/connection.py, tests/test_connection_thread_safety.py |
| 3 | Full test suite verification | (no commit) | - |

## Verification

```
grep -n "_send_lock" MCP_Server/connection.py
218:    _send_lock: threading.Lock = field(
267:        with self._send_lock:
```

Two hits: field declaration and lock acquisition. Pre-flight check at line 259 is outside the lock.

All 3 new tests pass. The 291 pre-existing test-ordering failures in tests/ are unrelated to this change (confirmed: same failures on misc-fixes HEAD before any changes).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed deadlocking Barrier strategy in concurrency test**
- **Found during:** Task 2 GREEN
- **Issue:** Initial test used `threading.Barrier(2)` inside `fake_send_message` (called while `_send_lock` was held). Thread 1 blocked waiting for the barrier while thread 0 blocked waiting for thread 1 to reach the barrier — classic deadlock. The lock working correctly caused the test to deadlock.
- **Fix:** Replaced barrier with `threading.Event` (start_event). Thread 0 calls `start_event.set()` inside `fake_send_message` (while holding `_send_lock`), then sleeps 50ms. Thread 1 waits on `start_event.wait()` before calling `send_command`, ensuring it attempts to acquire `_send_lock` while thread 0 holds it. Both patches applied at module level (before spawning threads) so both workers share the same mock.
- **Files modified:** tests/test_connection_thread_safety.py
- **Commit:** 035e8d5

## Known Stubs

None.

## Self-Check: PASSED

- [x] MCP_Server/connection.py exists and contains `_send_lock` at lines 218 and 267
- [x] tests/test_connection_thread_safety.py exists with 3 tests
- [x] Commits b38089f and 035e8d5 exist in git log
