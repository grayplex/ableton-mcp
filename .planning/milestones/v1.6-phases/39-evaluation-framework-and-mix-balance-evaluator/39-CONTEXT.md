# Phase 39 Context: Evaluation Framework and Mix Balance Evaluator

**Phase:** 39
**Milestone:** v1.6 Self-evaluation
**Mode:** --auto (Claude-selected defaults)
**Created:** 2026-03-31

## Phase Goal

The `MCP_Server/evaluation/` package exists with a working issue schema, score model, and dimension protocol. The mix balance evaluator runs against a live session and returns a populated `DimensionScore`.

## Requirements In Scope

- EVAL-01: Evaluation issue schema — dimension, severity, message, fix_hint
- EVAL-02: Score model — DimensionScore and SessionScore
- MIX-01: Mix balance evaluator comparing device params vs. recipe targets
- MIX-02: Mix balance DimensionScore 0-10 derived from in-range percentage + gain staging

## Codebase Assets to Reuse

| Asset | Location | Reuse |
|-------|----------|-------|
| `_infer_role()` | `tools/analysis.py:29` | Infer role from track name for per-track evaluation |
| `DIFF_THRESHOLD = 0.03` | `tools/intelligence.py:14` | Same threshold for mix balance diff |
| `get_mix_state` RS command | `tools/analysis.py:47` | Call via `conn.send_command("get_mix_state", {})` not via MCP wrapper |
| `get_track_meters` RS command | `tools/analysis.py:100` | Call via `conn.send_command("get_track_meters", {})` for gain staging |
| `get_recipe(role, genre)` | `mixing/catalog.py:108` | Fetch recipe targets |
| `natural_to_normalized()` | `devices/convert.py` | Convert recipe natural values to normalized for comparison |
| `GAIN_TARGETS` | `devices/gain_targets.py` | dBFS range per role for gain staging issues |
| `_normalize()` pattern | `mixing/catalog.py:54` | Same normalization pattern for schema IDs |
| pkgutil auto-discovery | `sounds/catalog.py:32` | Same pattern for future evaluator discovery (Phase 41 prep) |

## Locked Decisions

### D-01: Package structure
`MCP_Server/evaluation/` with three files for Phase 39:
- `__init__.py` — empty / re-exports
- `schema.py` — `EvaluationIssue`, `DimensionScore`, `SessionScore` as TypedDicts (consistent with existing `genres/schema.py` TypedDict pattern)
- `mix_balance.py` — `evaluate_mix_balance(genre: str, conn) -> DimensionScore`

**Rationale:** Mirrors `sounds/` and `mixing/` structure. Phase 40 adds `arrangement.py`, `sounds_coverage.py`, `harmonic.py` to the same package.

### D-02: Schema types — TypedDicts, not dataclasses
Use `TypedDict` for all schema objects (`EvaluationIssue`, `DimensionScore`, `SessionScore`). Consistent with how PROFILE, RECIPE, BlueprintSchema are defined across the codebase. JSON-serializable without `.asdict()`.

```python
class EvaluationIssue(TypedDict):
    dimension: str          # "mix" | "arrangement" | "harmony" | "sounds"
    severity: str           # "critical" | "warning" | "info"
    message: str            # Plain-language description
    fix_hint: str           # MCP tool name + args that resolves this issue

class DimensionScore(TypedDict):
    dimension: str
    score: float            # 0.0–10.0
    grade: str              # "A" | "B" | "C" | "D" | "F"
    issues: list[EvaluationIssue]

class SessionScore(TypedDict):
    score: float            # composite 0.0–10.0, weighted average of dimensions
    grade: str              # overall letter grade
    dimensions: list[DimensionScore]
    issues: list[EvaluationIssue]   # all issues merged and sorted by severity
    top_fixes: list[dict]   # up to 3 highest-severity fix suggestions
```

### D-03: Letter grade thresholds
| Score | Grade |
|-------|-------|
| 9.0–10.0 | A |
| 7.0–8.9 | B |
| 5.0–6.9 | C |
| 3.0–4.9 | D |
| 0.0–2.9 | F |

`grade_from_score(score: float) -> str` is a module-level helper in `schema.py`.

### D-04: Genre is required for mix balance evaluation
The mix balance evaluator needs a genre to fetch recipe targets. `evaluate_mix_balance(genre, conn)` takes genre as a required argument. Phase 41's `evaluate_session()` MCP tool signature:

```python
def evaluate_session(ctx, genre: str) -> str
```

Genre is required — without it, device parameter comparison is not possible. Gain staging check is always run regardless of genre (it uses GAIN_TARGETS which are role-based, not genre-based).

**Rationale:** All recipe lookups require role×genre (see `get_recipe(role, genre)`). Cannot evaluate mix balance without a genre target to compare against.

### D-05: Mix balance scoring formula
```
score = (in_range_params / total_params) * 10.0
```
- `total_params` = count of all params compared across all tracks
- `in_range_params` = params where `|current_norm - recipe_norm| < DIFF_THRESHOLD (0.03)`
- Gain staging deviations (too_hot / too_quiet) each reduce score by 0.5, clamped to 0.0
- Tracks with unrecognized role are excluded from scoring (same as DIFF_THRESHOLD approach in intelligence.py)

### D-06: Severity mapping for mix balance issues
| Condition | Severity |
|-----------|----------|
| `|delta| >= 0.15` (large deviation) | `"critical"` |
| `0.03 <= |delta| < 0.15` | `"warning"` |
| Gain "too_hot" | `"warning"` |
| Gain "too_quiet" | `"warning"` |
| Gain "no_signal" with loaded instrument | `"info"` |

### D-07: fix_hint format
Plain tool call string showing exactly what Claude should run:
```
"apply_mix_recipe(track_name='bass_synth', genre='techno', role='bass')"
```
For gain issues:
```
"check_gain_staging() — reduce volume on 'KICK_01' (currently +2.3 dB above target)"
```

### D-08: Tracks to skip in mix balance evaluation
- Tracks with no devices loaded → skip device param comparison (no recipe to compare)
- MIDI scaffold tracks with no instrument → skip entirely (same as GAIN-02 exclusion in analysis.py)
- Master track → only check against "master" role recipe, skip if no genre master recipe found
- Return tracks → check against "return" recipe role if available

### D-09: No MCP tool in Phase 39
Phase 39 delivers only the evaluation package + internal evaluator functions. No MCP tool is registered yet — that is Phase 41's scope. This keeps the phase focused on correctness-testable logic before wiring it to the MCP layer.

## What the Planner Must NOT Do

- Do not create `evaluate_session()` MCP tool in this phase — that's Phase 41
- Do not implement arrangement, harmonic, or sounds evaluators — that's Phase 40
- Do not auto-discover evaluator modules via pkgutil in this phase — static imports in Phase 41
- Do not require Ableton connection in schema.py — schema is pure Python, no imports from connection.py

## Test Requirements

Tests in `tests/test_evaluation_schema.py`:
1. `EvaluationIssue`, `DimensionScore`, `SessionScore` construction with all fields
2. `grade_from_score()` — boundary values: 9.0→A, 7.0→B, 5.0→C, 3.0→D, 2.9→F
3. Mix balance evaluator with mocked `get_mix_state` + `get_track_meters` responses
   - All-pass case: all params in range → score 10.0, no issues
   - All-fail case: all params out of range → score 0.0, issues populated
   - Partial case: mixed params → score between 0 and 10
4. No Ableton connection required in tests — inject mock conn

## Files to Create

```
MCP_Server/evaluation/__init__.py
MCP_Server/evaluation/schema.py
MCP_Server/evaluation/mix_balance.py
tests/test_evaluation_schema.py
```

## Dependencies

- `MCP_Server.devices.convert` (natural_to_normalized)
- `MCP_Server.devices.catalog` (ROLES, CATALOG)
- `MCP_Server.devices.gain_targets` (GAIN_TARGETS)
- `MCP_Server.mixing.catalog` (get_recipe)
- `MCP_Server.tools.analysis` (_infer_role, _meter_to_db)
- `MCP_Server.connection` (only in mix_balance.py, injected as parameter)

## Next Phase Preview

Phase 40 adds `arrangement.py`, `sounds_coverage.py`, `harmonic.py` to `MCP_Server/evaluation/`. Each follows the same signature: `evaluate_X(conn) -> DimensionScore`. Phase 41 wires them all into `evaluate_session()`.
