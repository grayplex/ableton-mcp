# Phase 51 Context: Next-Action Recommender and Phase Transition Gate

**Phase:** 51 — Next-Action Recommender and Phase Transition Gate
**Milestone:** v1.9 Orchestration/Agent Loop
**Requirements:** NEXT-01, NEXT-02
**Date:** 2026-03-31
**Mode:** --auto

## Goal

Two tools complete the orchestration loop:

1. `get_next_actions(genre, phase_name?, n?)` — reads checkpoint, determines active
   phase, returns next N concrete `ExecutionStep` entries ready to call.

2. `get_phase_transition_guidance(from_phase, genre?, to_phase?)` — validates whether
   the current phase is complete enough to advance, returns go/no-go with specific blockers.

Together these make Claude's agent loop self-directing: call `get_next_actions` to know
what to do, execute steps, call `get_phase_transition_guidance` to confirm done, advance.

## Codebase Scouting

### Modules available from prior phases

| Module | What it provides |
|--------|----------------|
| `MCP_Server/orchestration/execution.py` | `get_execution_plan(phase, genre, section, context)` |
| `MCP_Server/orchestration/checkpoint.py` | `get_checkpoint(genre)` → `ProductionCheckpoint` |
| `MCP_Server/orchestration/agenda.py` | `AGENDA_CATALOG`, `get_agenda(genre, brief)` |
| `MCP_Server/orchestration/schema.py` | All TypedDicts |
| `MCP_Server/evaluation/` | Evaluator classes (mix_balance, arrangement) |

### Evaluator importability check

Phase transition guidance for "mix" phase needs to check mix quality. The existing
`evaluate_session` MCP tool calls evaluators internally. We need to call the evaluator
directly. Check: `MCP_Server/evaluation/mix_balance.py` exports `MixBalanceEvaluator`
class with `evaluate(session_data, genre)` method — importable as a library function.
Use this for mix phase transition gate rather than calling the MCP tool.

For simplicity in Phase 51, the transition gate uses the same heuristics as the
checkpoint (D-05 from checkpoint CONTEXT.md) rather than full evaluator calls.
The evaluator path is noted as a future enhancement.

### `get_next_actions` logic

```
1. Call get_checkpoint(genre) to get active_phase and completed_phases
2. If phase_name provided: use that instead of active_phase
3. Call get_execution_plan(effective_phase, genre) to get full checklist
4. Filter out steps already inferred complete (based on checkpoint session_stats)
5. Return first n steps (default 10, max 25)
```

Step skip heuristics (based on checkpoint session_stats):
- If `session_stats.tracks_with_instruments > 0`: skip "create_midi_track" + "load_instrument_or_effect" steps for existing phases
- If `session_stats.track_count > 0`: skip "set_tempo" + "set_scale" if setup inferred complete
- No skipping if phase_name explicitly provided (always return full checklist for that phase)

### `get_phase_transition_guidance` logic

```
1. Resolve genre via resolve_alias
2. Get AGENDA_CATALOG[genre_id] phase order
3. Determine to_phase (next in order if not provided)
4. Run phase-specific completion checks (same heuristics as checkpoint)
5. Return {ready_to_advance, completion_pct, blockers, fix_hints, next_phase}
```

Completion check per phase_type (reuses checkpoint heuristics):
- setup: tracks_exist AND locators_exist
- drums: drum track with clips exists
- bass: bass track with clips exists  
- harmony: chord/pad track with clips exists
- melody: lead track with clips exists
- sound_design: effect device present on any track
- arrangement: no empty tracks (from get_arrangement_progress equivalent)
- mix: Compressor2 on ≥1 track
- master: GlueCompressor + Limiter2 on master

**Important:** These checks require a live Ableton connection. The tool calls RS
commands directly — same pattern as `get_production_checkpoint`.

## Locked Decisions

### D-01: New module `MCP_Server/orchestration/next_actions.py`

Contains `get_next_actions_result(genre, phase_name, n)` and
`get_transition_guidance(from_phase, genre, to_phase)` functions.
Both call RS commands via connection and call orchestration library functions.

### D-02: `get_next_actions` return shape

```python
{
    "checkpoint_summary": str,   # e.g. "House production: drums complete, working on bass"
    "active_phase": str,         # phase_id being targeted
    "genre": str,
    "steps": list[ExecutionStep] # next n steps
}
```

`checkpoint_summary` is constructed from `ProductionCheckpoint`:
- Template: "{genre} production: {completed_list} complete, next up: {active_phase}"
- If nothing complete: "{genre} production starting from scratch"
- If all complete: "{genre} production complete — ready for final review"

### D-03: Step skip logic is conservative

When `phase_name` is explicitly provided, return full checklist (no skipping).
When phase is inferred from checkpoint:
- If active_phase_progress > 0.3 (phase started), return remaining steps only
- If active_phase_progress == 0.0 (not started), return full checklist
- "Remaining" = all steps (no per-step completion tracking in Phase 51; that's HIST-01)

This keeps Phase 51 simple — the HIST-01 future requirement adds per-step tracking.

### D-04: `get_phase_transition_guidance` return shape

```python
{
    "from_phase": str,
    "to_phase": str,             # next phase in genre order, or provided to_phase
    "ready_to_advance": bool,
    "completion_pct": float,     # 0.0-1.0
    "blockers": list[str],       # e.g. ["No clips found in arrangement for Drums track"]
    "fix_hints": list[str],      # e.g. ["Call get_phase_execution_plan('drums','house')"]
    "next_phase": str            # same as to_phase
}
```

### D-05: MCP tool signatures

```python
@mcp.tool()
def get_next_actions(ctx: Context, genre: str, phase_name: str = None, n: int = 10) -> str:
    """Get the next N concrete tool calls to execute in the current production phase.
    ...
    """

@mcp.tool()
def get_phase_transition_guidance(ctx: Context, from_phase: str, genre: str = None, to_phase: str = None) -> str:
    """Check if a production phase is complete enough to advance to the next.
    ...
    """
```

Both return `json.dumps(result)` or `json.dumps({"error": "..."})`.

### D-06: `get_next_actions` without Ableton (graceful degradation)

If Ableton is not connected (connection fails), `get_next_actions` falls back to
calling `get_execution_plan(phase_name or "setup", genre)` directly and returning
the full checklist with `checkpoint_summary="No live session — showing full checklist for {phase}"`.

### D-07: Tests

`get_next_actions` and `get_phase_transition_guidance` both require Ableton state.
Tests mock `get_ableton_connection` with fixture data (same as Phase 50 fixtures).
Additionally test pure-computation paths: when phase_name is explicitly provided,
no connection needed (just calls get_execution_plan) — test this path without mocking.

### D-08: n parameter bounds

- Default: 10
- Max: 25 (clamp silently: `n = min(n, 25)`)
- Min: 1 (clamp: `n = max(n, 1)`)

## Implementation Order

1. `MCP_Server/orchestration/next_actions.py`
2. Update `MCP_Server/tools/orchestration.py` — add `get_next_actions` and `get_phase_transition_guidance`
3. Update `MCP_Server/orchestration/__init__.py` — expose new functions
4. Write `tests/test_next_actions.py` — 8 tests
5. Run tests, fix failures
6. Commit

## Test Coverage

| Test | What it verifies |
|------|-----------------|
| `test_get_next_actions_with_explicit_phase` | phase_name="drums" returns drums checklist, no connection needed |
| `test_get_next_actions_n_parameter` | n=3 returns exactly 3 steps |
| `test_get_next_actions_n_clamped` | n=100 returns at most 25 steps |
| `test_checkpoint_summary_format` | checkpoint_summary is non-empty string containing genre |
| `test_transition_drums_incomplete` | no drum clips → ready_to_advance=False, blockers non-empty |
| `test_transition_drums_complete` | drum track with clips → ready_to_advance=True |
| `test_transition_to_phase_override` | to_phase="mix" jumps directly to mix check |
| `test_get_next_actions_fallback_no_connection` | connection error → returns full checklist for setup |

## Out of Scope for Phase 51

- Per-step completion tracking (HIST-01)
- Parallel phase recommendations (PARA-01)
- Full evaluator integration for mix transition check (future enhancement)
