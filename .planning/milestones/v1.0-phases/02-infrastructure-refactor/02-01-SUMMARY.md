---
phase: 02-infrastructure-refactor
plan: 01
subsystem: infra
tags: [python, decorator, registry, mixin, command-dispatch, remote-script]

# Dependency graph
requires:
  - phase: 01-foundation-repair
    provides: dict-based command dispatch, handler implementations
provides:
  - CommandRegistry with @command decorator for handler registration
  - handlers/ package with 9 domain mixin modules
  - Slim __init__.py orchestrator (295 lines, down from 1229)
  - Self-scheduling command flag in registry
affects: [02-02, 02-03, all-future-phases]

# Tech tracking
tech-stack:
  added: []
  patterns: [mixin-class-handlers, decorator-registry, build-tables-at-init]

key-files:
  created:
    - AbletonMCP_Remote_Script/registry.py
    - AbletonMCP_Remote_Script/handlers/__init__.py
    - AbletonMCP_Remote_Script/handlers/base.py
    - AbletonMCP_Remote_Script/handlers/transport.py
    - AbletonMCP_Remote_Script/handlers/tracks.py
    - AbletonMCP_Remote_Script/handlers/clips.py
    - AbletonMCP_Remote_Script/handlers/notes.py
    - AbletonMCP_Remote_Script/handlers/devices.py
    - AbletonMCP_Remote_Script/handlers/mixer.py
    - AbletonMCP_Remote_Script/handlers/scenes.py
    - AbletonMCP_Remote_Script/handlers/browser.py
  modified:
    - AbletonMCP_Remote_Script/__init__.py
    - tests/conftest.py
    - tests/test_dispatch.py
    - tests/test_instrument_loading.py

key-decisions:
  - "Mixin class pattern for handler modules -- each module defines a class, AbletonMCP inherits from all"
  - "Absolute imports in handler modules (from AbletonMCP_Remote_Script.registry import command) for Ableton compatibility"
  - "ControlSurface last in MRO so mixin methods take precedence"
  - "Registry stores (cmd_name, method_name, is_write, is_self_scheduling) tuples, builds dispatch at init"

patterns-established:
  - "Handler mixin pattern: each handlers/*.py defines a class with @command-decorated methods"
  - "Adding new command: decorate method in handler module, it auto-registers"
  - "@command decorator: @command('name', write=True, self_scheduling=True)"

requirements-completed: [FNDN-08]

# Metrics
duration: 7min
completed: 2026-03-14
---

# Phase 02 Plan 01: Handler Extraction Summary

**CommandRegistry with @command decorator, 9 handler mixin modules, slim __init__.py orchestrator (295 lines from 1229)**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-14T01:48:07Z
- **Completed:** 2026-03-14T01:55:37Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- Created CommandRegistry class with @command decorator that auto-collects 21 handlers at import time
- Extracted all handler methods into 9 domain modules (base, transport, tracks, clips, notes, devices, mixer, scenes, browser) using mixin class pattern
- Slimmed __init__.py from 1229 lines to 295 lines -- only server infrastructure remains
- Properly flagged 2 self-scheduling commands (load_browser_item, load_instrument_or_effect) in registry
- All 34 tests pass (including updated grep-based tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CommandRegistry and extract handlers into domain modules** - `abe94b7` (feat)
2. **Task 2: Rewrite __init__.py to slim orchestrator** - `3930015` (feat)
3. **Auto-fix: Update Phase 1 grep-based tests for registry dispatch** - `1c99daf` (fix)

## Files Created/Modified
- `AbletonMCP_Remote_Script/registry.py` - CommandRegistry class with @command decorator and build_tables()
- `AbletonMCP_Remote_Script/handlers/__init__.py` - Import manifest triggering decorator registration
- `AbletonMCP_Remote_Script/handlers/base.py` - BaseHandlers mixin: _ping, _get_session_info
- `AbletonMCP_Remote_Script/handlers/transport.py` - TransportHandlers mixin: start/stop playback, set_tempo
- `AbletonMCP_Remote_Script/handlers/tracks.py` - TrackHandlers mixin: create_midi_track, set_track_name, get_track_info
- `AbletonMCP_Remote_Script/handlers/clips.py` - ClipHandlers mixin: create_clip, set_clip_name, fire_clip, stop_clip
- `AbletonMCP_Remote_Script/handlers/notes.py` - NoteHandlers mixin: add_notes_to_clip
- `AbletonMCP_Remote_Script/handlers/devices.py` - DeviceHandlers mixin: set_device_parameter, _get_device_type helper
- `AbletonMCP_Remote_Script/handlers/mixer.py` - MixerHandlers placeholder for Phase 4
- `AbletonMCP_Remote_Script/handlers/scenes.py` - SceneHandlers placeholder for Phase 8
- `AbletonMCP_Remote_Script/handlers/browser.py` - BrowserHandlers mixin: all browser navigation, loading, caching
- `AbletonMCP_Remote_Script/__init__.py` - Slim orchestrator with mixin inheritance and registry integration
- `tests/conftest.py` - Updated remote_script_source fixture to read all handler modules
- `tests/test_dispatch.py` - Rewritten to test CommandRegistry instead of dict literals
- `tests/test_instrument_loading.py` - Updated fixture to read handler package

## Decisions Made
- Used mixin class pattern (each handler module defines a class) instead of standalone functions -- handlers need `self` for Ableton API access
- Used absolute imports (`from AbletonMCP_Remote_Script.registry import command`) in handler modules for maximum Ableton runtime compatibility
- ControlSurface placed last in AbletonMCP's base class list so mixin methods take precedence in MRO
- Registry stores 4-tuple entries (cmd_name, method_name, is_write, is_self_scheduling) instead of 3-tuple to support self-scheduling flag
- _CATEGORY_MAP browser constant moved from __init__.py to handlers/browser.py where it's used

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated Phase 1 grep-based tests for registry pattern**
- **Found during:** Task 2 (Rewrite __init__.py)
- **Issue:** test_dispatch.py checked for `self._read_commands = {` dict literals; test_instrument_loading.py had its own fixture reading only __init__.py; registry.py docstring contained example function names that caused false grep matches
- **Fix:** Rewrote test_dispatch.py to verify CommandRegistry behavior; updated both test file fixtures to read all handler modules; simplified registry docstring examples
- **Files modified:** tests/test_dispatch.py, tests/test_instrument_loading.py, tests/conftest.py, AbletonMCP_Remote_Script/registry.py
- **Verification:** All 34 tests pass
- **Committed in:** 1c99daf

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test updates necessary because handler code moved from __init__.py to handler modules. No scope creep.

## Issues Encountered
None beyond the test fixture updates documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Handler extraction complete -- adding new commands in future phases requires only decorating a method in the appropriate handler module
- Ready for Plan 02-02 (MCP server tools split) and Plan 02-03 (linting + test infrastructure)
- mixer.py and scenes.py are placeholder modules ready for Phase 4 and Phase 8 implementation

## Self-Check: PASSED

- All 11 created files exist
- All 3 commits verified (abe94b7, 3930015, 1c99daf)
- All 34 tests pass

---
*Phase: 02-infrastructure-refactor*
*Completed: 2026-03-14*
