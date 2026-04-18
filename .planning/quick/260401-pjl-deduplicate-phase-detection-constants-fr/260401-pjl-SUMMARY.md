---
phase: quick-260401-pjl
plan: 01
subsystem: orchestration
tags: [refactor, deduplication, constants, phase-detection]
dependency_graph:
  requires: []
  provides: [MCP_Server.orchestration.phase_detection]
  affects: [checkpoint.py, next_actions.py]
tech_stack:
  added: []
  patterns: [single-source-of-truth constants module]
key_files:
  created:
    - MCP_Server/orchestration/phase_detection.py
  modified:
    - MCP_Server/orchestration/checkpoint.py
    - MCP_Server/orchestration/next_actions.py
decisions:
  - "_EQ and _DRUM_DEVICE remain in checkpoint.py as they are not shared with next_actions.py"
  - "_EFFECT_CLASSES remains in next_actions.py as it is not shared with checkpoint.py"
  - "290 pre-existing test failures in the worktree are unrelated to this refactor (confirmed same count before and after changes)"
metrics:
  duration: ~10m
  completed: 2026-04-01
---

# Phase quick-260401-pjl Plan 01: Deduplicate Phase-Detection Constants Summary

**One-liner:** Extracted seven shared phase-detection constants (_DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER) from checkpoint.py and next_actions.py into a new phase_detection.py module.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rebase worktree onto misc-fixes | (no code change) | — |
| 2+3 | Create phase_detection.py and update imports, run tests and commit | b8a3c71 | MCP_Server/orchestration/phase_detection.py, checkpoint.py, next_actions.py |

## Deviations from Plan

### Notes

**1. [Rule 1 - Process] Pre-existing test failures are out of scope**
- **Found during:** Task 3
- **Issue:** The worktree has 290 pre-existing test failures (confirmed identical count before and after our changes). The main repo on the misc-fixes branch passes all 31 tests that were passing before.
- **Fix:** Verified our changes introduced zero regressions. All 73 orchestration/checkpoint/next_actions tests pass.
- **Files modified:** None (pre-existing issue, out of scope)

## Verification Results

```
python -c "from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER; print('ok')"
# => ok

grep -n "_DRUM_NAMES" MCP_Server/orchestration/checkpoint.py
# => import line only, no local definition

grep -n "_DRUM_NAMES" MCP_Server/orchestration/next_actions.py
# => import line only, no local definition

python -m pytest tests/ -k "orchestration or checkpoint or next_action or phase" -q
# => 73 passed
```

## Known Stubs

None.

## Self-Check: PASSED

- `MCP_Server/orchestration/phase_detection.py` — FOUND
- `MCP_Server/orchestration/checkpoint.py` — FOUND (modified)
- `MCP_Server/orchestration/next_actions.py` — FOUND (modified)
- Commit `b8a3c71` — FOUND in git log
