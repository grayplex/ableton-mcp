---
phase: 02-infrastructure-refactor
plan: 02
subsystem: infra
tags: [mcp, fastmcp, modular-tools, domain-split, connection-management]

# Dependency graph
requires:
  - phase: 01-foundation-repair
    provides: "Protocol functions, timeout constants, connection management in server.py"
provides:
  - "MCP_Server/tools/ package with 7 domain modules for tool registration"
  - "MCP_Server/connection.py: AbletonConnection, get_ableton_connection, format_error, shutdown_connection"
  - "MCP_Server/protocol.py: send_message, recv_message length-prefix framing"
  - "Slim server.py orchestrator (48 lines) with FastMCP + lifespan + tool imports"
  - "Pattern: one-file-per-domain tool registration via @mcp.tool() decorator"
affects: [phase-03, phase-04, phase-05, phase-06, phase-07, phase-08]

# Tech tracking
tech-stack:
  added: []
  patterns: [domain-module-tool-registration, circular-import-prevention, shutdown-connection-lifecycle]

key-files:
  created:
    - MCP_Server/protocol.py
    - MCP_Server/connection.py
    - MCP_Server/tools/__init__.py
    - MCP_Server/tools/session.py
    - MCP_Server/tools/tracks.py
    - MCP_Server/tools/clips.py
    - MCP_Server/tools/transport.py
    - MCP_Server/tools/devices.py
    - MCP_Server/tools/browser.py
    - MCP_Server/tools/mixer.py
    - MCP_Server/tools/scenes.py
  modified:
    - MCP_Server/server.py
    - MCP_Server/__init__.py
    - pyproject.toml
    - tests/conftest.py
    - tests/test_connection.py
    - tests/test_instrument_loading.py

key-decisions:
  - "Created shutdown_connection() function in connection.py for proper lifecycle management instead of importing private globals"
  - "Tool modules import mcp from server.py; circular import prevented by creating mcp before importing tools"
  - "Updated 3 test fixtures to point at post-refactor source files (connection.py, protocol.py, tools/session.py)"

patterns-established:
  - "Domain tool module pattern: import mcp from server, import helpers from connection, decorate with @mcp.tool()"
  - "Adding a new tool requires editing exactly one file in MCP_Server/tools/"
  - "Standardized tool docstring format: imperative one-line summary + Parameters section"

requirements-completed: [FNDN-07]

# Metrics
duration: 6min
completed: 2026-03-14
---

# Phase 02 Plan 02: MCP Server Module Split Summary

**Split 797-line monolithic server.py into domain-organized tools/ package (7 modules, 17 tools) plus extracted connection.py and protocol.py**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-14T01:47:51Z
- **Completed:** 2026-03-14T01:53:52Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Extracted protocol.py (send_message, recv_message, _recv_exact) and connection.py (AbletonConnection, get_ableton_connection, format_error, timeout constants) as standalone modules
- Created tools/ package with 6 active domain modules (session, tracks, clips, transport, devices, browser) and 2 placeholders (mixer, scenes)
- Rewrote server.py from 797 lines to 48-line slim orchestrator (FastMCP instance, lifespan, main, tool imports)
- All 17 MCP tools verified registered via list_tools() async check
- Updated 3 test fixtures broken by the refactor to point at correct source files

## Task Commits

Each task was committed atomically:

1. **Task 1: Extract connection.py and protocol.py from server.py** - `c5e1791` (refactor)
2. **Task 2: Create tools/ package and rewrite server.py as slim orchestrator** - `e7c6441` (feat)

## Files Created/Modified
- `MCP_Server/protocol.py` - Length-prefix framing: send_message, recv_message, _recv_exact
- `MCP_Server/connection.py` - AbletonConnection, get_ableton_connection, format_error, timeout constants, shutdown_connection
- `MCP_Server/tools/__init__.py` - Import manifest triggering @mcp.tool() registration
- `MCP_Server/tools/session.py` - get_connection_status, get_session_info (2 tools)
- `MCP_Server/tools/tracks.py` - get_track_info, create_midi_track, set_track_name (3 tools)
- `MCP_Server/tools/clips.py` - create_clip, add_notes_to_clip, set_clip_name, fire_clip, stop_clip (5 tools)
- `MCP_Server/tools/transport.py` - set_tempo, start_playback, stop_playback (3 tools)
- `MCP_Server/tools/devices.py` - load_instrument_or_effect (1 tool)
- `MCP_Server/tools/browser.py` - get_browser_tree, get_browser_items_at_path, load_drum_kit (3 tools)
- `MCP_Server/tools/mixer.py` - Empty placeholder for Phase 4
- `MCP_Server/tools/scenes.py` - Empty placeholder for Phase 8
- `MCP_Server/server.py` - Slim orchestrator: FastMCP instance, lifespan, main(), tool imports (48 lines)
- `MCP_Server/__init__.py` - Re-exports from connection module instead of server
- `pyproject.toml` - Added MCP_Server.tools to setuptools packages
- `tests/conftest.py` - Added connection_source, protocol_source, session_tools_source fixtures
- `tests/test_connection.py` - Updated 3 tests to use new fixtures
- `tests/test_instrument_loading.py` - Updated health check test to use session_tools_source

## Decisions Made
- Created `shutdown_connection()` function in connection.py for clean lifecycle management. The lifespan shutdown code in server.py originally accessed `_ableton_connection` as a module-global directly; importing it would create a stale reference. A dedicated function in connection.py properly manages the global.
- Tool modules use `from MCP_Server.server import mcp` pattern. Circular import prevented by defining `mcp = FastMCP(...)` before `import MCP_Server.tools` in server.py.
- Updated test fixtures that grepped server.py for code now in connection.py, protocol.py, and tools/session.py rather than leaving broken tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added shutdown_connection() to connection.py**
- **Found during:** Task 2 (rewriting server.py lifespan)
- **Issue:** Original server.py lifespan directly accessed `_ableton_connection` global and `_connection_lock`. After refactor, importing these from connection.py would create stale references that can't set the module-level global to None.
- **Fix:** Added `shutdown_connection()` function to connection.py that properly manages the global within its own module scope.
- **Files modified:** MCP_Server/connection.py, MCP_Server/server.py
- **Verification:** Server lifespan imports and calls shutdown_connection() correctly
- **Committed in:** e7c6441 (Task 2 commit)

**2. [Rule 3 - Blocking] Updated 3 test fixtures for post-refactor file locations**
- **Found during:** Task 2 verification (running pytest)
- **Issue:** Tests grepped server.py for _connection_lock, struct.pack, and get_connection_status that moved to connection.py, protocol.py, and tools/session.py respectively.
- **Fix:** Added connection_source, protocol_source, session_tools_source fixtures; updated 3 tests to use them.
- **Files modified:** tests/conftest.py, tests/test_connection.py, tests/test_instrument_loading.py
- **Verification:** All 3 previously-failing tests now pass (24/31 pass; 7 remaining failures are pre-existing from plan 02-01 Remote Script refactor)
- **Committed in:** e7c6441 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
- 7 pre-existing test failures in test_dispatch.py and test_instrument_loading.py caused by plan 02-01's Remote Script handler extraction. These tests grep `__init__.py` for functions now in handler sub-modules. Logged to deferred-items.md for plan 02-03.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MCP Server is fully modular: adding new tools requires editing one file in tools/
- Placeholder modules (mixer.py, scenes.py) ready for Phase 4 and Phase 8
- connection.py and protocol.py are standalone, reusable modules
- 7 pre-existing test failures from 02-01 should be addressed in 02-03

---
*Phase: 02-infrastructure-refactor*
*Completed: 2026-03-14*
