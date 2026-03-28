---
phase: 27-locator-and-scaffolding-commands
plan: 02
subsystem: arrangement
tags: [mcp-tool, remote-script, locators, arrangement-overview, bar-conversion]

# Dependency graph
requires:
  - phase: 27-01
    provides: scaffold_arrangement tool, _bar_to_beat helper, ScaffoldHandler mixin
provides:
  - get_arrangement_overview MCP tool for reading back arrangement state
  - get_arrangement_state Remote Script handler for cue points, tracks, song length
  - _beat_to_bar helper for beat-to-bar conversion (inverse of _bar_to_beat)
affects: [28-arrangement-clip-writing, future arrangement tools]

# Tech tracking
tech-stack:
  added: []
  patterns: [read-only handler pattern (no write=True), beat-to-bar inverse conversion]

key-files:
  created: []
  modified:
    - AbletonMCP_Remote_Script/handlers/scaffold.py
    - MCP_Server/tools/scaffold.py
    - tests/test_scaffold.py

key-decisions:
  - "get_arrangement_state is read-only (no write=True) -- only reads cue_points, tracks, song_length, time sig"
  - "session_length_bars uses int() division not _beat_to_bar -- length not position, no +1 offset"
  - "_beat_to_bar uses math.floor for fractional beat positions -- maps to containing bar"

patterns-established:
  - "Beat-to-bar inverse: _beat_to_bar(beat, bpb) = floor(beat/bpb) + 1 mirrors _bar_to_beat(bar, bpb) = (bar-1) * bpb"
  - "Read-only handler pattern: @command without write=True uses TIMEOUT_READ by default"

requirements-completed: [SCAF-02]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 27 Plan 02: Arrangement Overview Summary

**get_arrangement_overview MCP tool reading locators, tracks, and session length from Ableton with beat-to-bar conversion**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-28T05:21:59Z
- **Completed:** 2026-03-28T05:24:15Z
- **Tasks:** 1 (code) + 1 (checkpoint, non-blocking)
- **Files modified:** 3

## Accomplishments
- Implemented get_arrangement_overview MCP tool returning locators with 1-indexed bars, flat track names, and session_length_bars
- Added get_arrangement_state Remote Script handler reading cue_points, tracks, song_length, and time signature
- Added _beat_to_bar helper as inverse of existing _bar_to_beat
- 21 scaffold tests passing (8 new: 3 bar conversion + 4 overview + 1 registration)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing tests** - `38a8411` (test)
2. **Task 1 (GREEN): Implement overview tool and handler** - `4307133` (feat)

_TDD task with RED/GREEN phases._

## Files Created/Modified
- `AbletonMCP_Remote_Script/handlers/scaffold.py` - Added get_arrangement_state handler reading cue points, tracks, song length, time sig
- `MCP_Server/tools/scaffold.py` - Added _beat_to_bar helper and get_arrangement_overview MCP tool
- `tests/test_scaffold.py` - Added TestBarConversions, TestArrangementOverview, test_overview_tool_registered

## Decisions Made
- get_arrangement_state is read-only (no write=True flag) since it only reads LOM properties
- session_length_bars uses int(song_length / beats_per_bar) not _beat_to_bar -- it's a length not a position
- _beat_to_bar uses math.floor for fractional beat positions to map to the containing bar

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failures in test_arrangement.py and test_audio_clips.py (await on non-async MagicMock) -- unrelated to this plan, not in scope

## Known Stubs

None -- all functionality is fully wired.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Arrangement overview tool ready for use alongside scaffold_arrangement
- Phase 28 can build on top of locator/track reading capability

---
*Phase: 27-locator-and-scaffolding-commands*
*Completed: 2026-03-28*
