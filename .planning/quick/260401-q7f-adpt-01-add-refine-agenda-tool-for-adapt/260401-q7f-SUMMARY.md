---
phase: quick-260401-q7f
plan: 01
subsystem: orchestration
tags: [agenda, refine, mcp-tool, tdd]
dependency_graph:
  requires: []
  provides: [refine_agenda-tool]
  affects: [MCP_Server/orchestration/agenda.py, MCP_Server/tools/orchestration.py]
tech_stack:
  added: []
  patterns: [pure-function, local-import, regex-matching, tdd]
key_files:
  created: []
  modified:
    - MCP_Server/orchestration/agenda.py
    - MCP_Server/tools/orchestration.py
    - tests/test_production_agenda.py
decisions:
  - Alias map (mastering->master, mixing->mix) handles natural-language instruction variants
  - ADD pattern covers both group(1) and group(2) from alternating regex branches for duplicate
  - Local import in MCP tool wrapper avoids circular import risk (matches existing pattern)
metrics:
  duration: ~15m
  completed: 2026-04-01
  tasks_completed: 2
  files_modified: 3
---

# Quick Task 260401-q7f: Add refine_agenda MCP Tool Summary

**One-liner:** Pure `refine_agenda(agenda, instruction)` function and `@mcp.tool()` wrapper enabling iterative agenda adjustments (skip/remove phases, duplicate phases) without regenerating from scratch.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement refine_agenda pure function (TDD) | cd2b254 | MCP_Server/orchestration/agenda.py, tests/test_production_agenda.py |
| 2 | Register refine_agenda as MCP tool | 5a985de | MCP_Server/tools/orchestration.py |

## What Was Built

### `refine_agenda(agenda, instruction)` — pure function in `agenda.py`

Accepts a `ProductionAgenda` dict and natural-language instruction string. Normalises instruction to lowercase, then dispatches:

- **Skip pattern** (`skip|remove|no <phase_type>`): Removes all phases with matching `phase_type`, recomputes `total_estimated_steps`. Aliases: "mastering" -> "master", "mixing" -> "mix".
- **Add/duplicate pattern** (`add a second|another <phase_type>` / `duplicate <phase_type>`): Inserts a deep copy of the matched phase as `<phase_type>_2` immediately after the original, with `depends_on` set to the original's `phase_id`.
- **Unrecognised instruction**: Returns the original agenda dict unchanged (no mutation, no exception).

### `@mcp.tool() refine_agenda` — wrapper in `tools/orchestration.py`

Accepts `agenda` (JSON string) and `instruction` (str). Parses JSON, calls the pure function, returns modified agenda as JSON. Returns `{"error": "..."}` on invalid JSON input. Uses local import to avoid circular import risk.

### `TestRefineAgenda` — 7 tests in `tests/test_production_agenda.py`

Covers: skip mastering removes master and recomputes steps; skip drums removes drums; add second melody inserts melody_2 after melody with correct depends_on; unrecognised instruction returns agenda unchanged; case-insensitivity; total_steps recomputed after skip; total_steps recomputed after duplicate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] "mastering" alias not matched by initial skip pattern**
- **Found during:** Task 1 GREEN phase (first test run)
- **Issue:** `_SKIP_PATTERN` matched exact `phase_type` values (e.g. "master") but the plan's test case uses "skip mastering" (the human-friendly form). The word "mastering" is not in `_ESTIMATED_STEPS`.
- **Fix:** Added `_PHASE_TYPE_ALIASES` dict (`mastering->master`, `mixing->mix`, `drumming->drums`) and extended the regex word list to include alias words. The skip and add handlers resolve aliases before filtering phases.
- **Files modified:** `MCP_Server/orchestration/agenda.py`
- **Commit:** cd2b254

## Verification

All 15 tests in `test_production_agenda.py` pass (8 pre-existing + 7 new `TestRefineAgenda`).
Smoke test: `refine_agenda(get_agenda("house"), "skip mastering")` returns phases without "master", `total_estimated_steps == 70`.
291 pre-existing test failures in full suite are unchanged — no regressions introduced.

## Self-Check: PASSED

- MCP_Server/orchestration/agenda.py: FOUND (modified, refine_agenda exported)
- MCP_Server/tools/orchestration.py: FOUND (modified, @mcp.tool() refine_agenda added)
- tests/test_production_agenda.py: FOUND (modified, TestRefineAgenda class added)
- Commit cd2b254: FOUND
- Commit 5a985de: FOUND
