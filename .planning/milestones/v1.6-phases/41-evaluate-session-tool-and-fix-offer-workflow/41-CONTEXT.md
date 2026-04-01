# Phase 41 Context: evaluate_session() Tool and Fix Offer Workflow

**Phase:** 41
**Milestone:** v1.6 Self-evaluation
**Mode:** --auto (Claude-selected defaults)
**Created:** 2026-03-31

## Phase Goal

Claude can call a single `evaluate_session()` MCP tool and receive a complete `SessionScore` with composite score, per-dimension breakdown, ranked issues, and up to 3 `top_fixes` — completing the full self-evaluation loop.

## Requirements In Scope

- SESS-01: `evaluate_session()` MCP tool — runs all 4 evaluators, returns composite SessionScore
- SESS-02: `top_fixes` — up to 3 highest-priority fixes with specific MCP tool call to resolve each

## Evaluators Available (from Phases 39–40)

| Evaluator | Module | Signature |
|-----------|--------|-----------|
| Mix balance | `MCP_Server.evaluation.mix_balance` | `evaluate_mix_balance(genre, conn)` |
| Arrangement | `MCP_Server.evaluation.arrangement` | `evaluate_arrangement(conn)` |
| Sound selection | `MCP_Server.evaluation.sounds_coverage` | `evaluate_sounds_coverage(conn)` |
| Harmonic | `MCP_Server.evaluation.harmonic` | `evaluate_harmonic(conn)` |

All return `DimensionScore` TypedDict from `MCP_Server.evaluation.schema`.

## Locked Decisions

### D-01: Single MCP tool in tools/evaluation.py
Create `MCP_Server/tools/evaluation.py` containing only `evaluate_session()`. Register in `tools/__init__.py` by adding `evaluation` to the import list. Add `MCP_Server.evaluation` to `pyproject.toml` packages.

### D-02: evaluate_session() signature
```python
@mcp.tool()
def evaluate_session(ctx: Context, genre: str) -> str:
```
`genre` is required — needed by `evaluate_mix_balance`. All other evaluators ignore genre.

### D-03: Composite score = simple average of 4 dimension scores
```python
composite = sum(d["score"] for d in dimensions) / len(dimensions)
```
No weighting — all 4 dimensions are equally important for v1.6. Weighted scoring deferred to future.

### D-04: Issue severity sort order
Merged issues list sorted: critical first, warning second, info last.
```python
_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}
merged_issues.sort(key=lambda i: _SEVERITY_ORDER.get(i["severity"], 99))
```

### D-05: top_fixes format
Take the first 3 issues from the severity-sorted merged list. Each `top_fix` is:
```python
{
    "severity": issue["severity"],
    "dimension": issue["dimension"],
    "message": issue["message"],
    "tool_call": issue["fix_hint"],   # the specific MCP tool call string
}
```
`top_fixes` is empty list if no issues. Maximum 3 entries.

### D-06: Return JSON string (consistent with all other MCP tools)
Serialize `SessionScore` dict to JSON with `json.dumps(result, indent=2)`.

### D-07: Error handling
Wrap each evaluator call in try/except. If an evaluator fails (e.g., no Ableton connection for arrangement check), return a DimensionScore with score=0 and a single critical issue describing the failure. This prevents one broken evaluator from blocking the whole evaluation.

### D-08: pyproject.toml already has genres, mixing, sounds — add evaluation
```toml
packages = ["MCP_Server", "MCP_Server.tools", "MCP_Server.theory", "MCP_Server.sounds", "MCP_Server.genres", "MCP_Server.mixing", "MCP_Server.evaluation"]
```

## Files to Create/Modify

```
MCP_Server/tools/evaluation.py          ← NEW: evaluate_session() MCP tool
MCP_Server/tools/__init__.py            ← MODIFY: add evaluation to import list
pyproject.toml                          ← MODIFY: add MCP_Server.evaluation to packages
tests/test_evaluate_session.py          ← NEW: integration tests for evaluate_session tool
```

## Test Strategy

`tests/test_evaluate_session.py`:

**class TestEvaluateSessionTool:**
- `test_evaluate_session_importable`: `from MCP_Server.tools.evaluation import evaluate_session` succeeds
- `test_returns_json_string`: result is a valid JSON string
- `test_session_score_structure`: parsed JSON has keys: score, grade, dimensions, issues, top_fixes
- `test_dimensions_has_four_entries`: `len(result["dimensions"]) == 4`
- `test_composite_score_is_average`: mock all 4 evaluators returning score=8.0 → composite score == 8.0
- `test_issues_sorted_critical_first`: mix critical + warning issues → critical appears first in result["issues"]
- `test_top_fixes_max_three`: 5+ issues → `len(result["top_fixes"]) <= 3`
- `test_top_fixes_have_tool_call_key`: each top_fix has "tool_call" key
- `test_dimension_names_all_present`: dimensions list contains "mix", "arrangement", "sounds", "harmony"

Mock strategy: patch all 4 evaluator functions with `unittest.mock.patch` to return canned `DimensionScore` dicts. No Ableton connection needed.
