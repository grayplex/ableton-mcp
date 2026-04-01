---
phase: 51-next-action-recommender
plan: 01
subsystem: orchestration
tags: [next-actions, phase-transition, agent-loop, mcp-tools]
dependency_graph:
  requires: [checkpoint.get_checkpoint, execution.get_execution_plan, agenda.AGENDA_CATALOG]
  provides: [next_actions.get_next_actions_result, next_actions.get_transition_guidance]
  affects: [MCP_Server/tools/orchestration.py, MCP_Server/orchestration/__init__.py]
tech_stack:
  added: []
  patterns: [phase-completion-heuristics, checkpoint-aware-recommender, graceful-fallback]
key_files:
  created:
    - MCP_Server/orchestration/next_actions.py
    - tests/test_next_actions.py
    - .planning/milestones/v1.9-phases/51-next-action-recommender/51-01-PLAN.md
  modified:
    - MCP_Server/tools/orchestration.py
    - MCP_Server/orchestration/__init__.py
decisions:
  - "Phase completion heuristics duplicated from checkpoint.py for clarity (not re-imported)"
  - "get_next_actions falls back to setup checklist when Ableton unreachable (D-06)"
  - "n parameter clamped to 1-25 range silently (D-08)"
  - "Per-step completion tracking deferred to HIST-01 future requirement"
metrics:
  duration: "continuation of wip(51) commit"
  completed_date: 2026-04-01
  tasks: 4
  files: 5
---

# Phase 51 Plan 01: Next-Action Recommender and Phase Transition Gate Summary

## One-liner

Checkpoint-aware next-step recommender and phase-specific go/no-go gate completing the v1.9 orchestration agent loop.

## What Was Built

Two final MCP tools close the orchestration loop that phases 48-50 established:

**`get_next_actions(genre, phase_name?, n?)`**
- Calls `get_checkpoint(genre)` to infer active phase from live Ableton state
- If `phase_name` is explicitly provided, bypasses checkpoint entirely (pure computation path)
- Returns first `n` `ExecutionStep` entries from `get_execution_plan(active_phase, genre)`
- Graceful fallback: if Ableton is not connected, returns setup checklist with descriptive summary
- `n` clamped to 1-25 range; default 10

**`get_phase_transition_guidance(from_phase, genre?, to_phase?)`**
- Reads live Ableton state (tracks, devices, clips via get_arrangement_state + get_mix_state)
- Runs phase-specific completion heuristics: drums=drum track with clips, mix=Compressor2 present, master=GlueCompressor+Limiter2 on master
- Returns `{ready_to_advance, completion_pct, blockers, fix_hints, next_phase}`
- `fix_hints` map each blocker to the exact MCP tool call that resolves it
- `to_phase` auto-determined from AGENDA_CATALOG if not provided; overridable

## Deviations from Plan

None — plan executed exactly as written.

## Tests

8 tests in `tests/test_next_actions.py`, all passing:

| Test | Class | Coverage |
|------|-------|----------|
| `test_explicit_phase_no_connection_needed` | TestGetNextActions | NEXT-01 explicit path |
| `test_n_parameter_limits_steps` | TestGetNextActions | n slicing |
| `test_n_clamped_to_25` | TestGetNextActions | n max clamp |
| `test_checkpoint_summary_contains_genre` | TestGetNextActions | summary content |
| `test_fallback_no_connection` | TestGetNextActions | graceful degradation |
| `test_drums_incomplete_no_clips` | TestGetTransitionGuidance | NEXT-02 incomplete |
| `test_drums_complete_with_clips` | TestGetTransitionGuidance | NEXT-02 complete |
| `test_to_phase_override` | TestGetTransitionGuidance | to_phase override |

## Full Orchestration Tool Set (v1.9 Complete)

All 5 MCP tools now registered in `MCP_Server/tools/orchestration.py`:

| Tool | Phase | Purpose |
|------|-------|---------|
| `get_production_agenda` | 48 | Genre-specific ordered phase list |
| `get_phase_execution_plan` | 49 | Concrete step checklist for a phase |
| `get_production_checkpoint` | 50 | Live session progress snapshot |
| `get_next_actions` | 51 | Next N steps for active phase |
| `get_phase_transition_guidance` | 51 | Go/no-go verdict before advancing |

## Known Stubs

None.

## Self-Check: PASSED

- MCP_Server/orchestration/next_actions.py: FOUND
- tests/test_next_actions.py: FOUND
- MCP_Server/tools/orchestration.py has get_next_actions: FOUND
- MCP_Server/tools/orchestration.py has get_phase_transition_guidance: FOUND
- MCP_Server/orchestration/__init__.py exports both functions: FOUND
- 8 tests pass: CONFIRMED
