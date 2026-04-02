---
phase: quick
plan: 260402-rb4
subsystem: orchestration/execution
tags: [sentinel-resolution, depends-on-step, execution-plan, tdd]
dependency_graph:
  requires: []
  provides: [sentinel-depends-on-invariant, query-step-prepend]
  affects: [sound_design-phase, mix-phase, execution-plan-generation]
tech_stack:
  added: []
  patterns: [query-step-prepend-for-sentinel-resolution]
key_files:
  created: []
  modified:
    - MCP_Server/orchestration/execution.py
    - tests/test_phase_execution.py
    - .planning/codebase/CONCERNS.md
decisions:
  - "Prepend get_arrangement_overview as step 1 in sound_design and mix builders rather than rely on description hints alone"
metrics:
  duration: ~2m
  completed: 2026-04-02
---

# Quick Task 260402-rb4: Ensure All Sentinel-Arg Execution Steps Have depends_on_step

Prepended get_arrangement_overview query steps to _build_sound_design_steps and _build_mix_steps so every sentinel-arg step has an explicit depends_on_step chain; enforced with test across all 9 phases.

## Changes Made

### Task 1: Add query steps to sound_design and mix, test sentinel depends_on invariant

**Tests (RED - commit c648124):**
- `test_sentinel_steps_have_depends_on_step`: For all 9 phase types x house genre, every step with a `<...>` sentinel in suggested_args must have `depends_on_step` set to a non-None integer
- `test_sound_design_starts_with_query_step`: sound_design/house step 1 must be get_arrangement_overview
- `test_mix_starts_with_query_step`: mix/house step 1 must be get_arrangement_overview

**Implementation (GREEN - commit eda5a73):**
- `_build_sound_design_steps`: Prepended `get_arrangement_overview` query step as step 1. Renumbered existing steps 1-4 to 2-5, each with depends_on_step chaining from the query step.
- `_build_mix_steps`: Prepended `get_arrangement_overview` query step as step 1. Role steps start at step 2; first role depends on query step (1), subsequent roles chain from previous role.

All 18 tests pass including existing json_output_under_2000_chars and step_numbers_sequential.

### Task 2: Update CONCERNS.md (commit 6c9b6db)

- Fragile area "Sentinel value resolution" marked RESOLVED with 260402-rb4 reference
- Architectural risk entry updated with note about explicit dependency chain
- Test coverage gap entry updated noting structural invariant test exists

## Deviations from Plan

None - plan executed exactly as written. The RED commit already existed from a prior partial execution; GREEN and docs commits were completed in this session.

## Verification

```
$ python -m pytest tests/test_phase_execution.py -x -v
18 passed, 2 warnings in 0.03s
```

## Known Stubs

None.
