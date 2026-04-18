---
phase: quick-260401-pqm
plan: 01
subsystem: orchestration
tags: [bugfix, next-actions, step-filtering]
dependency_graph:
  requires: []
  provides: [non-callable-step-filtering]
  affects: [get_next_actions_result]
tech_stack:
  added: []
  patterns: [filter-and-partition]
key_files:
  created: []
  modified:
    - MCP_Server/orchestration/next_actions.py
    - MCP_Server/orchestration/execution.py
    - tests/test_next_actions.py
decisions:
  - "Non-callable steps (em-dash, empty, None tool_name) filtered into 'notes' field rather than dropped entirely, preserving instruction text for Claude"
  - "Filtering applied at all 4 return sites in get_next_actions_result for completeness"
metrics:
  duration: ~2m
  completed: "2026-04-01"
  tasks_completed: 2
  tasks_total: 2
---

# Quick Task 260401-pqm: Filter Non-Callable Arrangement Steps Summary

**One-liner:** Filter placeholder steps with em-dash tool_name from get_next_actions_result, preserving descriptions as notes

## What Was Done

### Task 1: Rebase worktree onto misc-fixes
Rebased the worktree onto the latest misc-fixes branch to incorporate changes from parallel agents.

### Task 2: Filter non-callable steps (TDD)

**RED:** Added two failing tests:
- `test_arrangement_steps_exclude_non_callable` - verifies no step with non-callable tool_name is returned
- `test_arrangement_callable_steps_preserved` - verifies all 4 callable arrangement steps are preserved

**GREEN:** Implemented the fix:
- Added `_NON_CALLABLE` frozenset and `_filter_steps()` helper to `next_actions.py`
- Applied filtering at all 4 return sites in `get_next_actions_result`
- Non-callable step descriptions preserved in a `"notes"` list field
- Added clarifying comment to the placeholder step in `execution.py`

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 2 (RED) | 66a5e49 | test(quick-260401-pqm): add failing tests for non-callable step filtering |
| 2 (GREEN) | 46f5b4a | feat(quick-260401-pqm): filter non-callable steps from get_next_actions_result |

## Verification

- `tests/test_next_actions.py`: 8/8 passed (including 2 new tests)
- `tests/test_execution.py`: 9/9 passed (run independently; combined run has pre-existing mock conflict)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED
