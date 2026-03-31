"""Tests for MCP_Server/tools/evaluation.py: evaluate_session() MCP tool.

Covers:
- evaluate_session importable and callable
- Returns valid JSON string with SessionScore structure
- Composite score is average of 4 dimension scores
- Issues merged and sorted critical-first
- top_fixes capped at 3 entries, each with tool_call key
- 4 dimensions present with correct names
"""

import json
import sys
import types
from unittest.mock import MagicMock, patch

# Mock the mcp module hierarchy so tool imports work without mcp installed
_mock_mcp = types.ModuleType("mcp")
_mock_fastmcp = types.ModuleType("mcp.server.fastmcp")
_mock_server = types.ModuleType("mcp.server")
_mock_fastmcp.Context = type("Context", (), {})
_mock_mcp.server = _mock_server
_mock_server.fastmcp = _mock_fastmcp
sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", _mock_server)
sys.modules.setdefault("mcp.server.fastmcp", _mock_fastmcp)

if "MCP_Server.server" not in sys.modules:
    _mock_app_server = types.ModuleType("MCP_Server.server")
    _mcp_instance = MagicMock()
    _mcp_instance.tool.return_value = lambda fn: fn
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server

import pytest  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dim(dimension: str, score: float, issues=None):
    """Build a canned DimensionScore dict."""
    return {
        "dimension": dimension,
        "score": score,
        "grade": "B" if score >= 7.0 else "C",
        "issues": issues or [],
    }


def _make_issue(dimension: str, severity: str, message: str = "test issue", fix_hint: str = "some_tool()"):
    """Build a canned EvaluationIssue dict."""
    return {
        "dimension": dimension,
        "severity": severity,
        "message": message,
        "fix_hint": fix_hint,
    }


def _all_four_dims(score=8.0, issues_map=None):
    """Return a list of 4 DimensionScore dicts — one per evaluator."""
    issues_map = issues_map or {}
    return [
        _make_dim("mix", score, issues_map.get("mix")),
        _make_dim("arrangement", score, issues_map.get("arrangement")),
        _make_dim("sounds", score, issues_map.get("sounds")),
        _make_dim("harmony", score, issues_map.get("harmony")),
    ]


_PATCH_MIX = "MCP_Server.tools.evaluation.evaluate_mix_balance"
_PATCH_ARR = "MCP_Server.tools.evaluation.evaluate_arrangement"
_PATCH_SND = "MCP_Server.tools.evaluation.evaluate_sounds_coverage"
_PATCH_HRM = "MCP_Server.tools.evaluation.evaluate_harmonic"
_PATCH_CONN = "MCP_Server.tools.evaluation.get_ableton_connection"


def _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm, score=8.0, issues_map=None):
    """Wire up all 4 evaluator mocks with canned DimensionScore returns."""
    issues_map = issues_map or {}
    mock_mix.return_value = _make_dim("mix", score, issues_map.get("mix"))
    mock_arr.return_value = _make_dim("arrangement", score, issues_map.get("arrangement"))
    mock_snd.return_value = _make_dim("sounds", score, issues_map.get("sounds"))
    mock_hrm.return_value = _make_dim("harmony", score, issues_map.get("harmony"))


# ---------------------------------------------------------------------------
# TestEvaluateSessionTool
# ---------------------------------------------------------------------------

class TestEvaluateSessionTool:
    """Tests for the evaluate_session() MCP tool."""

    def test_evaluate_session_importable(self):
        """evaluate_session can be imported from MCP_Server.tools.evaluation and is callable."""
        from MCP_Server.tools.evaluation import evaluate_session
        assert callable(evaluate_session)

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_returns_json_string(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """evaluate_session() returns a str that is valid JSON."""
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        result = evaluate_session(ctx, "house")

        assert isinstance(result, str)
        parsed = json.loads(result)  # must not raise
        assert parsed is not None

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_session_score_structure(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """Parsed JSON has keys: score, grade, dimensions, issues, top_fixes."""
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        parsed = json.loads(evaluate_session(ctx, "house"))

        assert "score" in parsed
        assert "grade" in parsed
        assert "dimensions" in parsed
        assert "issues" in parsed
        assert "top_fixes" in parsed

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_dimensions_has_four_entries(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """Dimensions list has exactly 4 entries."""
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        parsed = json.loads(evaluate_session(ctx, "house"))

        assert len(parsed["dimensions"]) == 4

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_dimension_names_all_present(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """Dimensions list contains entries for 'mix', 'arrangement', 'sounds', 'harmony'."""
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        parsed = json.loads(evaluate_session(ctx, "house"))

        names = {d["dimension"] for d in parsed["dimensions"]}
        assert names == {"mix", "arrangement", "sounds", "harmony"}

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_composite_score_is_average(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """When all 4 evaluators return score=8.0, composite score == 8.0."""
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm, score=8.0)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        parsed = json.loads(evaluate_session(ctx, "house"))

        assert parsed["score"] == 8.0

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_issues_sorted_critical_first(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """When mix has a warning and arrangement has a critical, critical appears first in issues."""
        issues_map = {
            "mix": [_make_issue("mix", "warning", "mix warning")],
            "arrangement": [_make_issue("arrangement", "critical", "arrangement critical")],
        }
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm, score=5.0, issues_map=issues_map)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        parsed = json.loads(evaluate_session(ctx, "house"))

        issues = parsed["issues"]
        assert len(issues) >= 2
        # Find positions
        severities = [i["severity"] for i in issues]
        critical_idx = severities.index("critical")
        warning_idx = severities.index("warning")
        assert critical_idx < warning_idx, f"Expected critical before warning, got {severities}"

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_top_fixes_max_three(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """When there are 5+ issues, top_fixes has at most 3 entries."""
        issues_map = {
            "mix": [
                _make_issue("mix", "critical", f"critical issue {i}")
                for i in range(3)
            ],
            "arrangement": [
                _make_issue("arrangement", "warning", f"warning issue {i}")
                for i in range(3)
            ],
        }
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm, score=4.0, issues_map=issues_map)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        parsed = json.loads(evaluate_session(ctx, "house"))

        assert len(parsed["top_fixes"]) <= 3

    @patch(_PATCH_CONN)
    @patch(_PATCH_HRM)
    @patch(_PATCH_SND)
    @patch(_PATCH_ARR)
    @patch(_PATCH_MIX)
    def test_top_fixes_have_tool_call_key(self, mock_mix, mock_arr, mock_snd, mock_hrm, mock_conn):
        """Each entry in top_fixes has a 'tool_call' key."""
        fix_hint = "apply_mix_recipe(track_name='kick', genre='house', role='kick')"
        issues_map = {
            "mix": [_make_issue("mix", "critical", "a critical issue", fix_hint=fix_hint)],
        }
        _mock_evaluators(mock_mix, mock_arr, mock_snd, mock_hrm, score=5.0, issues_map=issues_map)
        mock_conn.return_value = MagicMock()

        from MCP_Server.tools.evaluation import evaluate_session
        ctx = MagicMock()
        parsed = json.loads(evaluate_session(ctx, "house"))

        assert len(parsed["top_fixes"]) >= 1
        for fix in parsed["top_fixes"]:
            assert "tool_call" in fix
