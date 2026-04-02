---
phase: quick-260401-qjf
plan: 01
subsystem: orchestration
tags: [sentinel-resolution, arrangement-overview, execution-steps]
key-files:
  created: []
  modified:
    - MCP_Server/tools/scaffold.py
    - MCP_Server/orchestration/execution.py
    - tests/test_execution.py
    - tests/test_phase_execution.py
decisions:
  - "Used _SENTINEL_HINT constant for consistent phrasing across all phase builders"
  - "Standardized sound_design and mix hint text to match new format"
metrics:
  duration: 140s
  completed: "2026-04-02T00:11:39Z"
  tasks: 1
  files: 4
---

# Quick Task 260401-qjf: Fix get_arrangement_state Track Index / Sentinel Resolution

Surface track index in get_arrangement_overview output ({name, index} dicts instead of bare strings) and add explicit sentinel resolution hints to execution step descriptions.

## Changes Made

### Part A: Track index in get_arrangement_overview

- `MCP_Server/tools/scaffold.py`: Changed track list comprehension from `[t["name"] for t in state["tracks"]]` to `[{"name": t["name"], "index": t["index"]} for t in state["tracks"]]`
- Updated docstring to document the new track format
- The Remote Script handler already returns index per track -- this just surfaces it through the MCP tool

### Part B: Sentinel resolution hints in execution steps

- `MCP_Server/orchestration/execution.py`: Added `_SENTINEL_HINT` constant for consistent hint phrasing
- Applied hint to first `<track_index>` step (set_track_name, step 2) in drums, bass, harmony, melody builders
- Standardized existing hints in `_build_sound_design_steps` and `_build_mix_steps` to use the same phrasing pattern: "resolve <...> via get_arrangement_overview or get_all_tracks"

### Part C: Tests

- `tests/test_execution.py`: Added `TestArrangementOverview` class with `test_arrangement_overview_includes_track_index`
- `tests/test_phase_execution.py`: Added `test_sentinel_steps_have_resolution_hint` covering drums, bass, harmony, melody

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

All 25 tests pass across both test files, including 2000-char budget constraint.

## Commits

| Commit | Message |
|--------|---------|
| 6ee1cce | test(quick-260401-qjf): add failing tests for track index and sentinel hints |
| 92efae0 | feat(quick-260401-qjf): include track index in arrangement overview and add sentinel hints |

## Known Stubs

None.

## Self-Check: PASSED
