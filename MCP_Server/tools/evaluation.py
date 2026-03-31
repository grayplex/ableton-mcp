"""Session evaluation tool: composite self-evaluation across all production dimensions."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.evaluation.arrangement import evaluate_arrangement
from MCP_Server.evaluation.harmonic import evaluate_harmonic
from MCP_Server.evaluation.mix_balance import evaluate_mix_balance
from MCP_Server.evaluation.schema import SessionScore, grade_from_score
from MCP_Server.evaluation.sounds_coverage import evaluate_sounds_coverage
from MCP_Server.server import mcp

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _run_evaluator(name: str, fn, *args):
    """Run an evaluator, returning a fallback DimensionScore on failure."""
    try:
        return fn(*args)
    except Exception as e:
        return {
            "dimension": name,
            "score": 0.0,
            "grade": "F",
            "issues": [{
                "dimension": name,
                "severity": "critical",
                "message": f"{name} evaluator failed: {e}",
                "fix_hint": "Verify Ableton connection with get_connection_status",
            }],
        }


@mcp.tool()
def evaluate_session(ctx: Context, genre: str) -> str:
    """Evaluate the current Ableton session across four production dimensions.

    Runs mix balance, arrangement completeness, sound selection coverage,
    and harmonic coherence checks in one call. Returns a composite score
    (0-10 with letter grade), per-dimension breakdown, all issues ranked
    by severity, and up to 3 top_fixes with the specific MCP tool call
    to resolve each issue.

    After reviewing the result, call the tool_call in each top_fix to
    address the highest-priority issues.

    Parameters:
    - genre: Genre for mix recipe comparison (e.g. "house", "techno",
      "ambient"). Use list_recipes() to see all available genres.

    Returns JSON with:
    - score: composite 0.0-10.0
    - grade: "A" | "B" | "C" | "D" | "F"
    - dimensions: list of per-dimension scores (mix, arrangement, sounds, harmony)
    - issues: all issues merged and sorted by severity (critical first)
    - top_fixes: up to 3 highest-priority fixes with tool_call strings
    """
    try:
        conn = get_ableton_connection()

        # Run all four evaluators
        mix_dim = _run_evaluator("mix", evaluate_mix_balance, genre, conn)
        arr_dim = _run_evaluator("arrangement", evaluate_arrangement, conn)
        snd_dim = _run_evaluator("sounds", evaluate_sounds_coverage, conn)
        hrm_dim = _run_evaluator("harmony", evaluate_harmonic, conn)

        dimensions = [mix_dim, arr_dim, snd_dim, hrm_dim]

        # Composite score: simple average
        composite = sum(d["score"] for d in dimensions) / len(dimensions)
        composite = round(composite, 2)

        # Merge and sort all issues: critical first, warning second, info last
        all_issues = []
        for dim in dimensions:
            all_issues.extend(dim.get("issues", []))
        all_issues.sort(key=lambda i: _SEVERITY_ORDER.get(i.get("severity", "info"), 99))

        # Top fixes: up to 3 highest-severity issues with tool_call
        top_fixes = [
            {
                "severity": issue["severity"],
                "dimension": issue["dimension"],
                "message": issue["message"],
                "tool_call": issue["fix_hint"],
            }
            for issue in all_issues[:3]
        ]

        result = SessionScore(
            score=composite,
            grade=grade_from_score(composite),
            dimensions=dimensions,
            issues=all_issues,
            top_fixes=top_fixes,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        return format_error(
            "evaluate_session failed",
            detail=str(e),
            suggestion="Verify Ableton connection with get_connection_status",
        )
