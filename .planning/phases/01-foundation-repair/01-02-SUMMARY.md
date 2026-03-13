---
phase: 01-foundation-repair
plan: 02
subsystem: infra
tags: [socket-protocol, length-prefix-framing, threading, struct, tdd]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Python 3.11-clean source files with pytest infrastructure"
provides:
  - "Length-prefix framing protocol (struct.pack/unpack >I) on both sides of socket"
  - "Thread-safe connection access via threading.Lock"
  - "Real ping command for liveness testing"
  - "Tiered timeout constants (read=10s, write=15s, browser=30s, ping=5s)"
  - "13 protocol and connection tests"
affects: [01-03, 02-socket-protocol]

# Tech tracking
tech-stack:
  added: []
  patterns: [length-prefix-framing, threading-lock-context-manager, tiered-timeouts]

key-files:
  created:
    - tests/test_protocol.py
    - tests/test_connection.py
  modified:
    - AbletonMCP_Remote_Script/__init__.py
    - MCP_Server/server.py

key-decisions:
  - "Protocol functions defined as standalone module-level functions, not class methods, for reuse"
  - "Docstring wording adjusted to avoid literal sendall(b'') pattern that grep-based tests detect"

patterns-established:
  - "Length-prefix framing: 4-byte big-endian header + UTF-8 JSON payload for all socket communication"
  - "Threading.Lock with context manager for all global connection access"
  - "Tiered timeout constants based on operation type (read/write/browser/ping)"
  - "Real ping command for connection liveness testing"

requirements-completed: [FNDN-03, FNDN-04]

# Metrics
duration: 4min
completed: 2026-03-13
---

# Phase 1 Plan 2: Socket Protocol Summary

**Replaced O(n^2) JSON re-parsing with struct.pack length-prefix framing, added threading.Lock for connection safety, eliminated 200ms artificial delays**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-13T22:51:19Z
- **Completed:** 2026-03-13T22:55:53Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Replaced O(n^2) JSON re-parsing accumulation loop with O(n) length-prefix framing using struct.pack/unpack >I
- Added identical send_message/recv_message/_recv_exact protocol functions to both Remote Script and MCP server
- Protected _ableton_connection with threading.Lock (_connection_lock) using context manager pattern
- Eliminated both time.sleep(0.1) calls from send_command (200ms latency per modifying command removed)
- Replaced sendall(b'') liveness test with real ping command + handler
- Added tiered timeout constants: TIMEOUT_READ=10s, TIMEOUT_WRITE=15s, TIMEOUT_BROWSER=30s, TIMEOUT_PING=5s
- Rewrote _handle_client to use framing instead of string buffer accumulation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create protocol and connection tests (RED phase)** - `86524d8` (test)
2. **Task 2: Implement length-prefix framing and threading.Lock in both files** - `4527a20` (feat)

_Note: TDD flow -- tests written in Task 1 (RED), implementation in Task 2 (GREEN)_

## Files Created/Modified
- `tests/test_protocol.py` - 7 protocol roundtrip tests (simple, large, empty, unicode, malformed, oversized, multiple)
- `tests/test_connection.py` - 6 grep-based tests verifying source file patterns (lock, no sleep, no empty sendall, ping, struct.pack)
- `AbletonMCP_Remote_Script/__init__.py` - Added protocol functions, rewrote _handle_client, added _ping handler
- `MCP_Server/server.py` - Added protocol functions, threading.Lock, timeout constants, rewrote send_command and get_ableton_connection

## Decisions Made
- Protocol functions (send_message, recv_message, _recv_exact) placed as standalone module-level functions in both files rather than as class methods -- enables reuse and keeps the wire format implementation visible
- Docstring in get_ableton_connection uses "sending empty bytes" instead of literal sendall(b'') to avoid false-positive grep test matches

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed docstring containing literal sendall(b'') pattern**
- **Found during:** Task 2
- **Issue:** The docstring for get_ableton_connection contained the literal text `sendall(b'')` which the grep-based test `test_no_sendall_empty_bytes` correctly flagged
- **Fix:** Changed docstring wording from "instead of sendall(b'')" to "instead of sending empty bytes"
- **Files modified:** MCP_Server/server.py
- **Verification:** test_no_sendall_empty_bytes passes
- **Committed in:** 4527a20 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial docstring wording fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both source files use identical length-prefix framing protocol -- wire format is symmetric
- Threading.Lock protects connection access -- safe for concurrent MCP tool calls
- Ready for Plan 03 (command dispatch refactor) which operates on the if/elif chain that was intentionally left unchanged

---
*Phase: 01-foundation-repair*
*Completed: 2026-03-13*
