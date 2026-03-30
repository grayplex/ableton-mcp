---
phase: 02-infrastructure-refactor
plan: 03
subsystem: testing
tags: [ruff, pytest, fastmcp, smoke-tests, linting, test-infrastructure]

# Dependency graph
requires:
  - phase: 02-infrastructure-refactor
    provides: "Handler registry (02-01), MCP Server module split with tools/ package (02-02)"
provides:
  - "ruff configuration with moderate strictness (E/F/W/I/B/UP)"
  - "FastMCP in-memory test fixtures (mock_connection, mcp_server)"
  - "Smoke tests for all 6 domain modules (session, tracks, clips, transport, devices, browser)"
  - "CommandRegistry unit tests"
  - "CI command: ruff check + pytest"
affects: [all-future-phases]

# Tech tracking
tech-stack:
  added: [ruff]
  patterns: [fastmcp-in-memory-testing, mock-connection-multi-patch, domain-smoke-tests]

key-files:
  created:
    - tests/test_session.py
    - tests/test_tracks.py
    - tests/test_clips.py
    - tests/test_transport.py
    - tests/test_devices.py
    - tests/test_browser.py
    - tests/test_registry.py
  modified:
    - pyproject.toml
    - tests/conftest.py
    - tests/test_protocol.py
    - MCP_Server/connection.py
    - MCP_Server/server.py
    - MCP_Server/tools/clips.py
    - MCP_Server/tools/transport.py
    - MCP_Server/tools/browser.py

key-decisions:
  - "Patch get_ableton_connection at every import site (7 modules) to prevent real connection attempts in tests"
  - "Domain smoke tests verify tool registration + mocked send_command response, not Ableton-specific behavior"
  - "Retired 4 grep-based test files; ruff enforces what those tests verified (Python 3 idioms, import hygiene)"

patterns-established:
  - "Test pattern: async test function with (mcp_server, mock_connection) fixtures for behavioral verification"
  - "CI command: uv run ruff check MCP_Server/ AbletonMCP_Remote_Script/ tests/ && uv run pytest tests/ -v --timeout=10"
  - "Adding domain tests: create tests/test_{domain}.py, use mock_connection.send_command.return_value to set response"

requirements-completed: [FNDN-09, FNDN-10]

# Metrics
duration: 5min
completed: 2026-03-14
---

# Phase 02 Plan 03: Lint + Test Infrastructure Summary

**Ruff linting (E/F/W/I/B/UP) + FastMCP in-memory test suite with 27 tests across 8 files, replacing grep-based tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-14T01:59:04Z
- **Completed:** 2026-03-14T02:04:14Z
- **Tasks:** 2
- **Files modified:** 22

## Accomplishments
- Configured ruff with moderate strictness and fixed all lint issues across the entire codebase (43 auto-fixed, 14 manual)
- Built FastMCP in-memory test infrastructure with mock_connection and mcp_server fixtures
- Created 6 domain smoke test files + 1 registry test file with 20 new behavioral tests
- Preserved 7 protocol roundtrip tests from Phase 1
- Retired 4 grep-based test files (test_python3_cleanup, test_connection, test_dispatch, test_instrument_loading)
- Full CI command works: `uv run ruff check MCP_Server/ AbletonMCP_Remote_Script/ tests/ && uv run pytest tests/ -v --timeout=10`

## Task Commits

Each task was committed atomically:

1. **Task 1: Configure ruff and fix lint issues** - `f7c7d4b` (chore)
2. **Task 2: Build test infrastructure and retire old tests** - `b299c40` (feat)

## Files Created/Modified
- `pyproject.toml` - Added ruff dev dependency and [tool.ruff] configuration sections
- `tests/conftest.py` - Rewritten with mock_connection (multi-patch) and mcp_server fixtures
- `tests/test_session.py` - 3 tests: tool registration, get_session_info, get_connection_status
- `tests/test_tracks.py` - 3 tests: tool registration, create_midi_track, get_track_info
- `tests/test_clips.py` - 3 tests: tool registration, create_clip, fire_clip
- `tests/test_transport.py` - 3 tests: tool registration, set_tempo, start_playback
- `tests/test_devices.py` - 2 tests: tool registration, load_instrument_or_effect
- `tests/test_browser.py` - 2 tests: tool registration, get_browser_tree
- `tests/test_registry.py` - 4 tests: decorator, build_tables, self_scheduling, all_commands
- `MCP_Server/connection.py` - Fixed B904 raise-from-except (4 exception chains), removed unused imports
- `MCP_Server/server.py` - Removed unused variable, import ordering
- `MCP_Server/tools/clips.py` - Removed 5 unused result variables
- `MCP_Server/tools/transport.py` - Removed 3 unused result variables
- `MCP_Server/tools/browser.py` - Removed 1 unused result variable

## Decisions Made
- Patched `get_ableton_connection` at all 7 import sites (connection module + 6 tool modules) to fully isolate tests from real socket connections. The `from X import Y` pattern copies references, so patching only at definition site is insufficient.
- Domain smoke tests verify tool registration and mocked responses only, not Ableton-specific behavior. This keeps tests fast and dependency-free.
- Retired grep-based tests because ruff now enforces the same rules (Python 3 idioms, import hygiene, bare except detection). Behavioral tests via FastMCP are more reliable than source text inspection.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mock_connection fixture to patch at all import sites**
- **Found during:** Task 2 (first test run)
- **Issue:** Tool modules import `get_ableton_connection` via `from MCP_Server.connection import get_ableton_connection`, creating local references. Patching only `MCP_Server.connection.get_ableton_connection` did not affect the tool modules' local references, causing real `get_ableton_connection` logic (including ping) to execute.
- **Fix:** Added `_GAC_PATCH_TARGETS` list in conftest.py that patches all 7 modules importing `get_ableton_connection`.
- **Files modified:** tests/conftest.py
- **Verification:** All 27 tests pass with correct mock isolation
- **Committed in:** b299c40 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correct test isolation. No scope creep.

## Issues Encountered
None beyond the mock patching fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full CI quality gate established: `uv run ruff check ... && uv run pytest tests/ -v`
- Phase 02 (Infrastructure Refactor) is now complete
- All 3 plans delivered: handler extraction, MCP server split, lint+test infrastructure
- Ready for Phase 03+ feature development with regression protection

## Self-Check: PASSED

- All 7 created test files exist
- Both commits verified (f7c7d4b, b299c40)
- 27 tests pass, ruff check clean

---
*Phase: 02-infrastructure-refactor*
*Completed: 2026-03-14*
