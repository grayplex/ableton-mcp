---
phase: quick
plan: 260401-q1g
subsystem: orchestration
tags: [performance, deduplication, socket-optimization]
dependency_graph:
  requires: []
  provides: [pre-fetched-transition-guidance]
  affects: [MCP_Server/orchestration/next_actions.py, tests/test_next_actions.py]
tech_stack:
  added: []
  patterns: [keyword-only-args, conditional-fetch]
key_files:
  created: []
  modified:
    - MCP_Server/orchestration/next_actions.py
    - tests/test_next_actions.py
decisions:
  - "Keyword-only params (after *) to avoid breaking positional callers"
  - "All-or-nothing pre-fetch: all three params required to skip Ableton connection"
  - "Renamed duplicate TestGetTransitionGuidance class to TestGetTransitionGuidanceToPhase"
metrics:
  duration: 87s
  completed: "2026-04-01"
  tasks_completed: 1
  tasks_total: 1
---

# Quick Plan 260401-q1g: Fix get_transition_guidance Duplicate Checkpoint Queries Summary

Keyword-only optional params (tracks, clips_by_track, master_devices) on get_transition_guidance to skip redundant Ableton socket calls when checkpoint data is already available.

## What Changed

### MCP_Server/orchestration/next_actions.py

- Added keyword-only params `tracks`, `clips_by_track`, `master_devices` to `get_transition_guidance`
- When all three are provided, the function skips `get_ableton_connection()` entirely -- zero socket round-trips
- When any are missing (including the default None), falls back to live Ableton query (backward compatible)
- No changes to `_phase_complete` or downstream logic -- same variables flow through

### tests/test_next_actions.py

- Added `TestTransitionGuidancePreFetched` class with 3 tests:
  - `test_prefetched_skips_ableton_connection`: asserts mock_gac.assert_not_called()
  - `test_prefetched_incomplete_phase`: pre-fetched data correctly reports blockers
  - `test_partial_prefetch_still_queries_ableton`: partial params fall back to live query
- Renamed duplicate `TestGetTransitionGuidance` (line 131) to `TestGetTransitionGuidanceToPhase` to avoid class shadowing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Renamed duplicate test class**
- **Found during:** Task 1 (test file read)
- **Issue:** Two classes named `TestGetTransitionGuidance` -- second shadows first in pytest collection
- **Fix:** Renamed second class to `TestGetTransitionGuidanceToPhase`
- **Files modified:** tests/test_next_actions.py
- **Commit:** c0afb0c

## Verification

- `python -m pytest tests/test_next_actions.py -x -v` -- 13/13 passed
- Full test suite: pre-existing failures in unrelated test files (test_arrangement.py, test_transport.py); no regressions from this change

## Known Stubs

None.

## Self-Check: PASSED
