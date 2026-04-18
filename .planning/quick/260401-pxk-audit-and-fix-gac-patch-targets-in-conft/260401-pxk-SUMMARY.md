---
quick_task: 260401-pxk
subsystem: tests
tags: [conftest, fixtures, mocking, get_ableton_connection]
key-files:
  modified:
    - tests/conftest.py
decisions: []
metrics:
  duration: ~5m
  completed: 2026-04-01
---

# Quick Task 260401-pxk: Audit and Fix GAC Patch Targets in conftest.py

**One-liner:** Added 5 missing `get_ableton_connection` patch targets for orchestration and v1.9 tool modules to conftest.py.

## What Was Done

Audited `_GAC_PATCH_TARGETS` in `tests/conftest.py` against all modules that import `get_ableton_connection` via `from ... import`. Five modules introduced in v1.9 were missing from the list, meaning tests using `mock_connection` would not patch those modules and could receive a real (unpatched) connection or fail unexpectedly.

### Entries Added

| Entry | Module |
|-------|--------|
| `MCP_Server.orchestration.checkpoint.get_ableton_connection` | Orchestration checkpoint tool |
| `MCP_Server.orchestration.next_actions.get_ableton_connection` | Orchestration next-actions tool |
| `MCP_Server.tools.evaluation.get_ableton_connection` | Evaluation tool |
| `MCP_Server.tools.intelligence.get_ableton_connection` | Intelligence tool |
| `MCP_Server.tools.refinement.get_ableton_connection` | Refinement tool |

All 5 modules were confirmed to exist and export `get_ableton_connection`.

## Verification

- All 5 modules verified to exist and expose `get_ableton_connection` attribute.
- Full test suite run confirmed: 290 failures exist both before and after the change (pre-existing, unrelated to this task). No new failures introduced.
- Test count: 767 passed, 290 pre-existing failures (unchanged).

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- `tests/conftest.py` modified with 5 new entries: CONFIRMED
- Commit `d601aa2` exists: CONFIRMED
- No new test failures introduced: CONFIRMED
