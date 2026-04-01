---
phase: quick-260401-p9j
plan: 01
subsystem: orchestration
tags: [execution, sentinel, clip-index, session-clips]
dependency_graph:
  requires: []
  provides: [sentinel-clip-index]
  affects: [execution-plans, session-clip-steps]
tech_stack:
  patterns: [sentinel-value-resolution]
key_files:
  modified:
    - MCP_Server/orchestration/execution.py
    - tests/test_phase_execution.py
decisions:
  - "Sentinel value is '<clip_index>' (not the full hint string) in suggested_args to stay within 2000-char budget"
  - "Shortened _SENTINEL_NOTE from 'resolve via' to 'use' to reclaim token budget space"
  - "Clip sentinel hint not added to step descriptions (redundant with arg sentinel); only _SENTINEL_NOTE kept in descriptions"
metrics:
  duration: "~3 minutes"
  completed: "2026-04-01"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 2
---

# Quick Task 260401-p9j: Fix clip_index Hardcoding in Execution Plans Summary

Replaced all 10 hardcoded clip_index=0 values in session-clip execution steps with "<clip_index>" sentinel, following the existing _SENTINEL_NOTE pattern for track_index resolution.

## Task Results

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 (RED) | Add failing tests for sentinel clip_index | a5bf3e0 | tests/test_phase_execution.py |
| 1 (GREEN) | Implement sentinel clip_index in all session-clip steps | e61a487 | MCP_Server/orchestration/execution.py |

## Changes Made

### MCP_Server/orchestration/execution.py
- Added `_SENTINEL_CLIP` constant: `"<clip_index>: first has_clip=false slot via get_track_info()"`
- Replaced `"clip_index": 0` with `"clip_index": "<clip_index>"` in all 10 session-clip step locations across drums, bass, harmony, and melody builders
- Shortened `_SENTINEL_NOTE` from `"<track_index>: resolve via get_all_tracks()"` to `"<track_index>: use get_all_tracks()"` to stay within the 2000-char serialized checklist budget

### tests/test_phase_execution.py
- Added `test_session_clip_steps_use_sentinel_clip_index`: verifies all 4 phase builders (drums, bass, harmony, melody) use sentinel clip_index in session mode
- Added `test_arrangement_clip_steps_have_no_clip_index`: verifies arrangement-clip steps do not contain clip_index at all

## Decisions Made

1. **Sentinel in args only, not descriptions**: Adding `_SENTINEL_CLIP` to step descriptions would exceed the 2000-char token budget. The sentinel value `"<clip_index>"` in suggested_args is self-explanatory (matches the `"<track_index>"` pattern).
2. **Shortened _SENTINEL_NOTE**: Trimmed "resolve via" to "use" (saves ~12 chars per occurrence) to accommodate the clip_index sentinel strings within budget.

## Verification

- `grep -c '"clip_index": 0' execution.py` returns **0** (no hardcoded values)
- `grep -c '"<clip_index>"' execution.py` returns **10** (all sentinel)
- All 10 tests pass including token budget constraint

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Token budget exceeded with full _SENTINEL_CLIP in descriptions**
- **Found during:** Task 1 GREEN phase
- **Issue:** Adding `_SENTINEL_CLIP` to step descriptions pushed drums checklist to 2367 chars (limit 2000)
- **Fix:** Removed _SENTINEL_CLIP from descriptions entirely; shortened _SENTINEL_NOTE text; sentinel value in suggested_args is sufficient
- **Files modified:** MCP_Server/orchestration/execution.py

## Known Stubs

None.

## Self-Check: PASSED

- execution.py: FOUND
- test_phase_execution.py: FOUND
- Commit a5bf3e0 (RED): FOUND
- Commit e61a487 (GREEN): FOUND
