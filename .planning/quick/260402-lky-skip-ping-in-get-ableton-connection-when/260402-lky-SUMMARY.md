---
phase: quick
plan: 260402-lky
subsystem: connection
tags: [performance, connection, thread-safety]
dependency_graph:
  requires: []
  provides: [_healthy-flag-skip-ping]
  affects: [MCP_Server/connection.py]
tech_stack:
  added: []
  patterns: [health-flag-fast-path]
key_files:
  created: []
  modified:
    - MCP_Server/connection.py
    - tests/test_connection_thread_safety.py
    - .planning/codebase/CONCERNS.md
decisions:
  - "_healthy flag read/written only under _connection_lock or _send_lock -- no data race"
  - "send_command sets _healthy=True on success, False on any exception -- single source of truth"
metrics:
  duration: ~3m
  completed: 2026-04-02
---

# Quick Task 260402-lky: Skip Ping in get_ableton_connection When Healthy

**One-liner:** Added _healthy flag to AbletonConnection so get_ableton_connection() skips the ping round-trip on the hot path, only re-validating after errors or fresh connections.

## Changes Made

### Task 1: Add _healthy flag and skip-ping fast path (TDD)
- Added `_healthy: bool` dataclass field to `AbletonConnection`, defaulting to `False`
- Modified `send_command` to set `_healthy = True` on successful response, `_healthy = False` in all exception handlers (TimeoutError, ConnectionError, BrokenPipeError, ConnectionResetError, JSONDecodeError, generic Exception)
- Added fast-path in `get_ableton_connection()`: when `_ableton_connection._healthy` is `True`, returns immediately without ping
- When `_healthy` is `False`, existing ping-based re-validation path is preserved
- New connection creation path gets `_healthy = True` automatically via `send_command("get_session_info")` success
- Added 7 new tests in `TestHealthyFlag` and `TestSkipPingFastPath` classes covering all behaviors
- **Commit:** `4867792`

### Task 2: Update CONCERNS.md
- Marked the "get_ableton_connection() pings on every call while holding the global lock" performance concern as RESOLVED (260402-lky)
- **Commit:** `57ade6b`

## Deviations from Plan

None -- plan executed exactly as written. Task 1 was already committed by a prior execution attempt; verified tests pass and code matches plan spec.

## Known Stubs

None.

## Verification

- All 11 tests in `tests/test_connection_thread_safety.py` pass (3 existing + 8 new covering _healthy flag behaviors)
- Thread safety preserved: `_healthy` only modified under `_send_lock` (in send_command) or `_connection_lock` (in get_ableton_connection)
- No behavioral change for callers -- same return values, same exceptions

## Self-Check: PASSED
