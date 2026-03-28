---
phase: 32-device-state-reader-and-gain-staging
plan: 02
subsystem: api
tags: [mcp-tools, analysis, gain-staging, meter-levels, tdd]

# Dependency graph
requires:
  - phase: 32-01
    provides: get_mix_state and get_track_meters RS handlers, GAIN_TARGETS data module

provides:
  - get_mix_state MCP tool: single-call device parameter snapshot for all tracks
  - check_gain_staging MCP tool: per-track dBFS gain health report with role-aware targets

affects:
  - 33 (suggest_mix_adjustments will consume get_mix_state output to diff against recipes)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD red-green cycle: failing import error confirms RED state before implementation"
    - "Round meter_db to 1 decimal before boundary comparison to avoid float precision issues"
    - "Flatten tracks/return_tracks/master_track into single list for uniform processing"

key-files:
  created:
    - MCP_Server/tools/analysis.py
    - tests/test_analysis.py
  modified:
    - tests/conftest.py

key-decisions:
  - "Round meter_db to 1 decimal before comparing against gain targets — avoids float boundary issues (0.316 → -10.009 rounds to -10.0 which is within kick target -10.0..-4.0)"
  - "all_zero detection uses all() on flattened track list including master_track — consistent with per-track processing loop"
  - "no_signal status takes precedence over role inference — meter_db=None check happens before role check"

# Metrics
duration: 3min
completed: 2026-03-28
---

# Phase 32 Plan 02: Device State Reader and Gain Staging — MCP Tools Summary

**get_mix_state and check_gain_staging MCP tools with full TDD coverage: single-call session snapshot and role-aware dBFS gain staging analysis**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-28T21:27:13Z
- **Completed:** 2026-03-28T21:30:40Z
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `get_mix_state` MCP tool: single RS round-trip returns device parameter snapshot for all tracks (STATE-01)
- `check_gain_staging` MCP tool: reads live meter levels, infers roles from track names, compares dBFS against GAIN_TARGETS (GAIN-01, GAIN-02)
- `_meter_to_db` helper: linear amplitude to dBFS via `20*log10(value)`, returns None for silence
- `_infer_role` helper: case-insensitive substring match against ROLES list, first match wins (pad before atmospheric)
- Full TDD cycle: 29 tests written in RED phase, all passing in GREEN phase
- tests/conftest.py updated with new patch target for analysis module

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_analysis.py (RED state)** - `030ea6e` (test)
2. **Task 2: Create analysis.py (GREEN state)** - `0689de8` (feat)

## Files Created/Modified

- `MCP_Server/tools/analysis.py` — Two @mcp.tool functions plus two private helpers
- `tests/test_analysis.py` — 29 tests across 5 test classes (TestGainTargets, TestMeterToDb, TestInferRole, TestGetMixState, TestCheckGainStaging)
- `tests/conftest.py` — Added `MCP_Server.tools.analysis.get_ableton_connection` to `_GAC_PATCH_TARGETS`

## Decisions Made

- Round `meter_db` to 1 decimal before boundary comparison — `0.316` produces `-10.009 dBFS` raw, which rounds to `-10.0` (within kick target `-10.0..-4.0`). Without rounding the boundary test fails on float precision.
- `no_signal` takes precedence: `meter_db is None` check runs first, before role inference — a zero-level kick track reports `no_signal`, not `too_quiet`.
- `all_zero` detection scans all flattened tracks (regular + return + master) for consistency with the processing loop.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed float boundary precision for status classification**
- **Found during:** Task 2 (GREEN verification)
- **Issue:** `_meter_to_db(0.316)` returns `-10.009...` which is just below the kick target low bound of `-10.0`, causing `too_quiet` instead of `ok` for the boundary test
- **Fix:** Round `meter_db` to 1 decimal place before comparing against gain targets, matching the precision of the output field
- **Files modified:** `MCP_Server/tools/analysis.py`
- **Commit:** `0689de8`

## Known Stubs

None — both tools wire directly to real RS handlers implemented in plan 32-01.

---
*Phase: 32-device-state-reader-and-gain-staging*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: MCP_Server/tools/analysis.py
- FOUND: tests/test_analysis.py
- FOUND: tests/conftest.py (with analysis patch target)
- FOUND commit 030ea6e (RED state tests)
- FOUND commit 0689de8 (GREEN state implementation)
