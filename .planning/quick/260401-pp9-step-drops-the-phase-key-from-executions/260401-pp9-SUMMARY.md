---
phase: quick
plan: 260401-pp9
subsystem: orchestration
tags: [schema-fix, execution, tdd]
dependency_graph:
  requires: []
  provides: [phase-key-in-execution-steps]
  affects: [MCP_Server/orchestration/execution.py]
tech_stack:
  added: []
  patterns: [TypedDict-conformance]
key_files:
  created: []
  modified:
    - MCP_Server/orchestration/execution.py
    - tests/test_phase_execution.py
decisions:
  - Removed verbose sentinel description hints to stay within 2000-char budget after adding phase key
metrics:
  duration: ~3m
  completed: "2026-04-01"
---

# Quick Plan 260401-pp9: Step Drops the Phase Key from Executions Summary

**One-liner:** Added missing `phase` key to `_step()` dicts so they conform to the `ExecutionStep` TypedDict schema.

## What Changed

The `_step()` helper in `execution.py` accepted a `phase` parameter but discarded it -- the returned dict never included `"phase"`. This meant every `ExecutionStep` dict violated the `ExecutionStep` TypedDict declared in `schema.py`, which defines `phase: str` as a required field.

### Fix

Added `"phase": phase` to the dict literal in `_step()`. This was a one-line addition that brings all generated step dicts into schema conformance.

### Token Budget Recovery

Adding the phase key to every step increased serialized JSON size, pushing the `drums` checklist over the 2000-char limit. To compensate, removed the verbose sentinel hint strings (`_SENTINEL_NOTE`, `_SENTINEL_CLIP`) from step descriptions. These hints were redundant -- the sentinel values (`"<track_index>"`, `"<clip_index>"`) are already present in `suggested_args` and Claude resolves them at call time.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Token budget overflow after adding phase key**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Adding `"phase"` to every step pushed `drums/house` checklist from ~1980 to ~2108 chars, failing the existing `test_json_output_under_2000_chars` test.
- **Fix:** Removed verbose sentinel description hints (`_SENTINEL_NOTE`/`_SENTINEL_CLIP`), saving ~150 chars per multi-step phase. Sentinel info is already implicit in the `suggested_args` values.
- **Files modified:** `MCP_Server/orchestration/execution.py`
- **Commit:** b0f3dfb

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 5abaaa6 | test | Add failing test for phase key in execution steps (RED) |
| b0f3dfb | feat | Include phase key in _step() dicts, trim descriptions (GREEN) |

## Verification

- `test_every_step_has_phase_key`: PASS -- all 9 phase types checked
- `test_json_output_under_2000_chars`: PASS -- all phases under budget
- All 26 orchestration tests: PASS
- Pre-existing failures in `test_arrangement.py`/`test_audio_clips.py` (unrelated mock issue): not addressed (out of scope)

## Known Stubs

None.
