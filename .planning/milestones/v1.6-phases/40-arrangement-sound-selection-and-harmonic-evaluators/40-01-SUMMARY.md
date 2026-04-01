---
phase: 40-arrangement-sound-selection-and-harmonic-evaluators
plan: 01
subsystem: evaluation
tags: [evaluation, arrangement, sounds, harmonic, tdd]
dependency_graph:
  requires:
    - "MCP_Server/evaluation/schema.py"
    - "MCP_Server/devices/catalog.py (ROLES)"
    - "MCP_Server/sounds/catalog.py (list_profiles, get_profile)"
  provides:
    - "MCP_Server/evaluation/arrangement.py (evaluate_arrangement)"
    - "MCP_Server/evaluation/sounds_coverage.py (evaluate_sounds_coverage)"
    - "MCP_Server/evaluation/harmonic.py (evaluate_harmonic)"
  affects:
    - "Phase 41: evaluate_session() composite tool"
tech_stack:
  added: []
  patterns:
    - "TDD RED-GREEN: tests committed RED, then all 3 modules created, 14/14 GREEN"
    - "Inject conn pattern: all evaluators take conn as sole parameter (no genre)"
    - "Role affinity map: _build_role_to_instrument() pre-computes role->instrument from sounds catalog"
    - "Pitch class set: pure integer arithmetic (no music21) from root_note + cumsum(intervals)"
key_files:
  created:
    - MCP_Server/evaluation/arrangement.py
    - MCP_Server/evaluation/sounds_coverage.py
    - MCP_Server/evaluation/harmonic.py
    - tests/test_evaluation_phase40.py
  modified: []
decisions:
  - "D-03 scoring (arrangement): weighted clean = 1.0 for has_devices+clips, 0.5 for has_devices-no-clips, 0 for no-devices"
  - "D-04 device matching (sounds): device_name (display name) used, not class_name"
  - "D-06 harmonic fallback: empty scale_name or empty scale_intervals -> score=10.0 with info issue"
  - "D-09 harmonic scoring: in_key_notes/total_notes * 10; 0 notes -> 10.0"
metrics:
  duration_seconds: 238
  completed_date: "2026-03-31"
  tasks_completed: 5
  tasks_total: 5
  files_created: 4
  files_modified: 0
---

# Phase 40 Plan 01: Arrangement, Sound Selection, and Harmonic Evaluators Summary

**One-liner:** Three standalone evaluators (arrangement completeness, sound-selection coverage, harmonic coherence) each returning a `DimensionScore` via injected `conn` with no genre dependency.

## What Was Built

Three evaluation modules completing the evaluator set needed for Phase 41's `evaluate_session()` tool:

1. **`MCP_Server/evaluation/arrangement.py`** — `evaluate_arrangement(conn)`: checks every regular track for an instrument (critical if missing) and arrangement clips (warning if none). Score = weighted clean-track fraction × 10.

2. **`MCP_Server/evaluation/sounds_coverage.py`** — `evaluate_sounds_coverage(conn)`: pre-builds a role→instrument map from the sounds catalog (highest-affinity instrument per role tag), then checks each named track's `device_name` against the expected instrument. Mismatch = warning.

3. **`MCP_Server/evaluation/harmonic.py`** — `evaluate_harmonic(conn)`: reads `get_scale_info`, computes pitch-class set via pure integer arithmetic (no music21), iterates Session-view clips via `get_session_state` + `get_notes`, flags out-of-key notes as warnings. Empty scale → score=10.0 + info issue.

## Test Results

- **Phase 40 tests:** 14/14 passed (GREEN)
- **Full evaluation suite:** 96/96 passed (test_evaluation_schema.py + test_evaluation_phase40.py + test_sounds.py)
- **Pre-existing failures:** test_genre_quality.py (missing tiktoken), MCP tool registration tests (missing mcp package) — unrelated to Phase 40

## Commits

| Hash | Message |
|------|---------|
| 2370b90 | test(40): add failing tests for arrangement, sounds, harmonic evaluators (RED) |
| c81750d | feat(40-01): implement arrangement, sounds_coverage, and harmonic evaluators |

## Deviations from Plan

None — plan executed exactly as written. All three implementations match the design decisions in 40-CONTEXT.md (D-01 through D-10).

## Known Stubs

None. All three evaluators are fully wired to live RS commands via the injected `conn` parameter.

## Self-Check: PASSED

- [x] `MCP_Server/evaluation/arrangement.py` exists and contains `evaluate_arrangement`
- [x] `MCP_Server/evaluation/sounds_coverage.py` exists and contains `evaluate_sounds_coverage`
- [x] `MCP_Server/evaluation/harmonic.py` exists and contains `evaluate_harmonic`
- [x] Commit c81750d exists in git log
- [x] 14/14 Phase 40 tests GREEN
