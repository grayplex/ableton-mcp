---
phase: quick
plan: 260401-ox3
subsystem: remote-script
tags: [bugfix, arrangement-state, track-index]
dependency_graph:
  requires: []
  provides: [track-index-in-arrangement-state]
  affects: [checkpoint, next-actions, execution-tools, evaluation]
tech_stack:
  added: []
  patterns: [enumerate-for-index]
key_files:
  created: []
  modified:
    - AbletonMCP_Remote_Script/handlers/scaffold.py
    - tests/test_scaffold.py
    - tests/test_execution.py
    - tests/test_evaluation_phase40.py
decisions:
  - index field uses 0-based enumerate position matching song.tracks order
metrics:
  duration: 2m 25s
  completed: 2026-04-01T22:10:00Z
---

# Quick Task 260401-ox3: Add index field to get_arrangement_state Summary

Added 0-based index field to each track dict returned by _get_arrangement_state RS handler, enabling downstream consumers to identify tracks by position instead of relying solely on name matching.

## What Changed

### AbletonMCP_Remote_Script/handlers/scaffold.py
- Changed `_get_arrangement_state` track list comprehension from `for track in self._song.tracks` to `for i, track in enumerate(self._song.tracks)`
- Each track dict now includes `"index": i` alongside existing `name` and `has_devices` fields
- Updated docstring to reflect new return shape: `{"index": int, "name": str, "has_devices": bool}`

### Test Files Updated
- **tests/test_scaffold.py**: Updated `_mock_overview_factory` default tracks to include `index` field
- **tests/test_execution.py**: Updated `_mock_execution_factory` defaults and all inline track dicts (14 instances) to include `index`
- **tests/test_evaluation_phase40.py**: Updated all arrangement evaluator track dicts (6 instances) to include `index`

## Verification

- 45 tests pass across test_scaffold.py, test_checkpoint.py, test_next_actions.py, test_execution.py
- 44 tests pass across test_scaffold.py, test_execution.py, test_evaluation_phase40.py
- `get_arrangement_overview` output unchanged (flat name list, no index leaked)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Consistency] Updated test_execution.py and test_evaluation_phase40.py mocks**
- **Found during:** Task 1
- **Issue:** Plan files_modified only listed scaffold.py and test_scaffold.py, but test_execution.py and test_evaluation_phase40.py also construct track dicts for get_arrangement_state mocks without index fields
- **Fix:** Added index field to all track dicts in both files for consistency with the new RS handler return shape
- **Files modified:** tests/test_execution.py, tests/test_evaluation_phase40.py
- **Commit:** 8816575

## Known Stubs

None.

## Commits

| Hash | Message |
|------|---------|
| 8816575 | feat(quick-260401-ox3): add index field to _get_arrangement_state track dicts |

## Self-Check: PASSED
