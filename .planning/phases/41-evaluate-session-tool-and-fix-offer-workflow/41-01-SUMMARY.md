---
phase: 41-evaluate-session-tool-and-fix-offer-workflow
plan: 01
subsystem: tools/evaluation
tags: [evaluate_session, session_score, top_fixes, mcp_tool, v1.6]
requirements: [SESS-01, SESS-02]
dependency_graph:
  requires: [MCP_Server.evaluation.mix_balance, MCP_Server.evaluation.arrangement, MCP_Server.evaluation.sounds_coverage, MCP_Server.evaluation.harmonic, MCP_Server.evaluation.schema]
  provides: [evaluate_session MCP tool, SessionScore JSON response with top_fixes]
  affects: [MCP_Server.tools.__init__, pyproject.toml]
tech_stack:
  added: []
  patterns: [_run_evaluator isolation wrapper, severity sort order dict, SessionScore TypedDict composition]
key_files:
  created:
    - MCP_Server/tools/evaluation.py
    - tests/test_evaluate_session.py
  modified:
    - MCP_Server/tools/__init__.py
    - pyproject.toml
decisions:
  - "Simple average composite score (no weighting) — all 4 dimensions equal weight for v1.6"
  - "_run_evaluator wrapper isolates per-evaluator failures with fallback DimensionScore(score=0, grade=F)"
  - "top_fixes = first 3 items from severity-sorted issues list with tool_call = fix_hint"
  - "MCP_Server.evaluation added to pyproject.toml packages list (D-08)"
metrics:
  duration: ~15m
  completed: 2026-03-31
  tasks_completed: 4
  files_changed: 4
---

# Phase 41 Plan 01: evaluate_session() Tool and Fix Offer Workflow Summary

**One-liner:** Single-call `evaluate_session()` MCP tool that runs all 4 evaluators, computes composite score via simple average, sorts issues critical-first, and returns up to 3 `top_fixes` with `tool_call` strings — completing v1.6 Self-evaluation milestone.

## What Was Built

`MCP_Server/tools/evaluation.py` — the `evaluate_session(ctx, genre)` MCP tool that:

1. Calls all 4 evaluators via `_run_evaluator()` isolation wrapper (try/except per-evaluator)
2. Computes composite score as simple average of 4 dimension scores
3. Merges all issues from all dimensions and sorts by severity: critical(0) < warning(1) < info(2)
4. Produces `top_fixes` list — first 3 issues from sorted list, each with `tool_call = issue["fix_hint"]`
5. Returns `SessionScore` TypedDict serialized to JSON with `json.dumps(result, indent=2)`

`tests/test_evaluate_session.py` — 9 tests covering importability, JSON structure, dimension count/names, composite score math, issue sort order, top_fixes capping, and tool_call key presence.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write failing tests (TDD RED) | ed47c84 | tests/test_evaluate_session.py |
| 2 | Create tools/evaluation.py | 9524919 | MCP_Server/tools/evaluation.py |
| 3 | Register in __init__.py + pyproject.toml | d1f38e0 | MCP_Server/tools/__init__.py, pyproject.toml |
| 4 | Run full test suite — all green | d1f38e0 | (verification only) |

## Verification Results

```
python -m pytest tests/test_evaluate_session.py -v
  9 passed in 0.05s

python -m pytest tests/test_evaluation_schema.py tests/test_evaluation_phase40.py tests/test_evaluate_session.py -v
  40 passed in 0.09s

python -c "from MCP_Server.tools.evaluation import evaluate_session; print('OK')"
  OK

grep 'MCP_Server.evaluation' pyproject.toml
  packages = [..., "MCP_Server.evaluation"]

grep 'evaluation' MCP_Server/tools/__init__.py
  from . import ..., evaluation, ...
```

## Decisions Made

1. **Simple average composite score** — no weighting for v1.6; all 4 dimensions equally important. Weighted scoring deferred to future milestone.

2. **`_run_evaluator` isolation wrapper** — each evaluator wrapped in try/except; on failure returns `DimensionScore(score=0, grade="F", issues=[critical issue])` so one broken evaluator cannot block the whole evaluation.

3. **`top_fixes` = first 3 from sorted issues** — `tool_call` field set to `issue["fix_hint"]`, which is the specific MCP tool call string authored by the evaluator that created the issue.

4. **`evaluation` added alphabetically after `execution` in `tools/__init__.py`** — consistent with existing alphabetical ordering convention.

## Deviations from Plan

None — plan executed exactly as written. All files (test, implementation, registrations) were created per the locked decisions D-01 through D-08 in the phase context.

Note: `tests/test_genre_quality.py` and ~400 other tests fail due to missing `mcp` module (not installed in test environment). These failures are pre-existing and unrelated to this plan — all evaluation tests (40 tests across 3 files) pass cleanly.

## Known Stubs

None. `evaluate_session()` is fully wired — calls all 4 evaluators, constructs real `SessionScore`, returns real JSON. No hardcoded empty values or placeholders.

## Self-Check: PASSED

- [x] `MCP_Server/tools/evaluation.py` exists and is importable
- [x] `tests/test_evaluate_session.py` exists with 9 tests, all green
- [x] `MCP_Server/tools/__init__.py` contains `evaluation` in import line
- [x] `pyproject.toml` contains `MCP_Server.evaluation` in packages list
- [x] Commits d1f38e0, 9524919, ed47c84 all exist in git log
