"""Evaluation schema: issue types, dimension scores, and session score model.

All types are TypedDicts for JSON-serializable construction without .asdict().
grade_from_score() is a module-level helper used by all evaluators.
"""

from typing import TypedDict


class EvaluationIssue(TypedDict):
    """A single identified issue in a specific evaluation dimension."""
    dimension: str   # "mix" | "arrangement" | "harmony" | "sounds"
    severity: str    # "critical" | "warning" | "info"
    message: str     # Plain-language description of the problem
    fix_hint: str    # MCP tool name + args that directly resolves this issue


class DimensionScore(TypedDict):
    """Evaluation result for one production dimension."""
    dimension: str
    score: float          # 0.0–10.0
    grade: str            # "A" | "B" | "C" | "D" | "F"
    issues: list          # list[EvaluationIssue]


class SessionScore(TypedDict):
    """Composite evaluation result across all dimensions."""
    score: float          # composite 0.0–10.0 (weighted average)
    grade: str            # overall letter grade
    dimensions: list      # list[DimensionScore]
    issues: list          # all issues merged and sorted: critical first, then warning, then info
    top_fixes: list       # up to 3 dicts: {issue: EvaluationIssue, tool_call: str}


_GRADE_THRESHOLDS = [
    (9.0, "A"),
    (7.0, "B"),
    (5.0, "C"),
    (3.0, "D"),
]


def grade_from_score(score: float) -> str:
    """Convert a numeric score (0.0–10.0) to a letter grade.

    Thresholds: A >= 9.0, B >= 7.0, C >= 5.0, D >= 3.0, F < 3.0.
    """
    for threshold, grade in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"
