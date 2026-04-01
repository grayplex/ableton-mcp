---
phase: 39-evaluation-framework-and-mix-balance-evaluator
plan: 01
subsystem: evaluation
tags: [evaluation, schema, mix-balance, typeddict, tdd]
dependency_graph:
  requires:
    - MCP_Server.devices.catalog (ROLES)
    - MCP_Server.devices.convert (natural_to_normalized)
    - MCP_Server.devices.gain_targets (GAIN_TARGETS)
    - MCP_Server.mixing.catalog (get_recipe)
  provides:
    - MCP_Server.evaluation (package)
    - MCP_Server.evaluation.schema (EvaluationIssue, DimensionScore, SessionScore, grade_from_score)
    - MCP_Server.evaluation.mix_balance (evaluate_mix_balance)
  affects: []
tech_stack:
  added: []
  patterns:
    - TypedDict schema pattern (consistent with genres/schema.py)
    - TDD: RED commit before GREEN commit
    - Mock conn injection for evaluator unit tests
key_files:
  created:
    - MCP_Server/evaluation/__init__.py
    - MCP_Server/evaluation/schema.py
    - MCP_Server/evaluation/mix_balance.py
    - tests/test_evaluation_schema.py
  modified: []
decisions:
  - TypedDict used for all schema types (EvaluationIssue, DimensionScore, SessionScore) per D-02 — JSON-serializable without .asdict()
  - grade_from_score thresholds applied as iterable threshold list — A>=9.0, B>=7.0, C>=5.0, D>=3.0, F<3.0
  - Test fixtures use Compressor2.Ratio (no conversion param) rather than Threshold (linear_db conversion) to get predictable normalized values in tests
metrics:
  duration: 20m
  completed: 2026-03-31
  tasks: 4
  files: 4
---

# Phase 39 Plan 01: Evaluation Framework and Mix Balance Evaluator Summary

Delivered `MCP_Server/evaluation/` package with TypedDict schema types, grade helper, and a fully tested mix balance evaluator function using DIFF_THRESHOLD/CRITICAL_THRESHOLD severity mapping and gain-staging integration.

## What Was Built

### MCP_Server/evaluation/__init__.py
Empty package marker. Mirrors `sounds/` and `mixing/` package structure.

### MCP_Server/evaluation/schema.py
Three TypedDicts for the v1.6 evaluation framework:
- `EvaluationIssue` — dimension, severity, message, fix_hint
- `DimensionScore` — dimension, score (0-10), grade (A-F), issues list
- `SessionScore` — composite score, grade, per-dimension breakdown, all issues, top_fixes

`grade_from_score(score: float) -> str` helper with thresholds: A>=9.0, B>=7.0, C>=5.0, D>=3.0, F<3.0.

### MCP_Server/evaluation/mix_balance.py
`evaluate_mix_balance(genre: str, conn) -> DimensionScore` — compares current device params against role×genre recipe targets.

Scoring formula (D-05):
- `score = (in_range_params / total_params) * 10.0`
- Each gain staging deviation (too_hot / too_quiet) deducts 0.5, clamped to 0.0

Severity mapping (D-06):
- `|delta| >= 0.15` → `"critical"`
- `0.03 <= |delta| < 0.15` → `"warning"`
- Gain too_hot / too_quiet → `"warning"`
- No meter signal (with loaded instrument) → `"info"`

Track exclusions (D-08):
- Scaffold tracks with no devices → skip entirely
- Tracks whose name matches no role → excluded from scoring

### tests/test_evaluation_schema.py
17 tests across 3 classes:
- `TestSchemaTypes` (3 tests): TypedDict construction for all three schema types
- `TestGradeFromScore` (5 tests): Boundary value tests for all grade thresholds
- `TestMixBalanceEvaluator` (9 tests): all-pass (10.0), all-fail (0.0), partial (0 < x < 10), warning/critical severity, gain too hot, no-role exclusion, dimension field

## Test Results

```
17 passed, 0 failed
```

All 17 evaluation tests green. No regressions in the 171 tests covering related modules (test_analysis, test_intelligence, test_sounds, test_mixing).

Note: 407 pre-existing test failures in the repo relate to missing `mcp` module and async infrastructure — these are out of scope and unaffected by this phase.

## Key Decisions Applied

1. **TypedDicts, not dataclasses** (D-02): Consistent with `genres/schema.py`; JSON-serializable without `.asdict()` call.

2. **genre is required** (D-04): `evaluate_mix_balance(genre, conn)` takes genre as required arg — recipe comparison is impossible without it.

3. **Scoring formula** (D-05): `(in_range / total) * 10 - (gain_deductions * 0.5)`, clamped to 0.

4. **No MCP tool in Phase 39** (D-09): Pure evaluation logic only; Phase 41 wires into `evaluate_session()`.

5. **Test fixture correction** (Rule 1 auto-fix): Original tests used `Compressor2.Threshold` which has a `linear_db` conversion causing `natural_to_normalized(0.5) -> 1.0`, not 0.5. Fixed by using `Compressor2.Ratio` (no conversion, 0-1 range) and `S/C Mix` for multi-param tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test fixtures used wrong Compressor2 parameter**
- **Found during:** Task 4 (run tests — 3 failures)
- **Issue:** `Compressor2.Threshold` has `linear_db` conversion (`natural_min=-40, natural_max=0`). `natural_to_normalized("Compressor2", "Threshold", 0.5)` returns `1.0`, not `0.5` — test_all_params_in_range_scores_ten expected delta=0 but got delta=0.5
- **Fix:** Changed test fixtures to use `Ratio` param (no conversion, 0-1 range) and `S/C Mix` (no conversion, 0-1 range) where two no-conversion params were needed
- **Files modified:** `tests/test_evaluation_schema.py`
- **Commit:** d1010c0

## Self-Check: PASSED

Files created:
- FOUND: MCP_Server/evaluation/__init__.py
- FOUND: MCP_Server/evaluation/schema.py
- FOUND: MCP_Server/evaluation/mix_balance.py
- FOUND: tests/test_evaluation_schema.py

Commits:
- FOUND: 37da067 (RED tests)
- FOUND: 683b0fa (schema.py)
- FOUND: 7e33d8b (mix_balance.py)
- FOUND: d1010c0 (fixture fix)
