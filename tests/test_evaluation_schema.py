"""Tests for MCP_Server/evaluation/: schema types, grade helper, and mix balance evaluator.

Covers:
- EvaluationIssue, DimensionScore, SessionScore TypedDict construction
- grade_from_score() boundary values
- evaluate_mix_balance() with mocked RS responses:
  - all-pass → score 10.0
  - all-fail → score 0.0
  - partial → 0 < score < 10
  - out-of-range param → warning issue
  - large deviation → critical issue
  - gain too hot → warning issue
  - no-role track → excluded from scoring
  - dimension field == "mix"
"""

import sys
import types
from unittest.mock import MagicMock

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

from unittest.mock import MagicMock, patch  # noqa: E402

import pytest  # noqa: E402

from MCP_Server.evaluation.schema import (  # noqa: E402
    EvaluationIssue,
    DimensionScore,
    SessionScore,
    grade_from_score,
)
from MCP_Server.evaluation.mix_balance import evaluate_mix_balance  # noqa: E402


# ---------------------------------------------------------------------------
# Canned test fixtures
# ---------------------------------------------------------------------------

def _make_mix_state(tracks=None, return_tracks=None, master=None):
    """Build a minimal get_mix_state RS response."""
    return {
        "tracks": tracks or [],
        "return_tracks": return_tracks or [],
        "master_track": master or {"name": "Master", "type": "master", "devices": []},
    }


def _make_meter_state(tracks=None, return_tracks=None, master=None):
    """Build a minimal get_track_meters RS response."""
    return {
        "tracks": tracks or [],
        "return_tracks": return_tracks or [],
        "master_track": master or {"name": "Master", "meter_level": 0.1},
    }


# A kick track with one Compressor2 device using Ratio param (no conversion, 0-1 range).
# natural_to_normalized("Compressor2", "Ratio", 0.5) == 0.5 (no conversion: clamp to [0,1])
KICK_TRACK_IN_RANGE = {
    "index": 0,
    "name": "KICK_01",
    "type": "midi",
    "devices": [
        {
            "index": 0,
            "class_name": "Compressor2",
            "device_name": "Compressor",
            "parameters": [
                {"name": "Ratio", "value": 0.5},  # recipe also 0.5 → delta=0 → in range
            ],
        }
    ],
}

# Canned recipe that exactly matches KICK_TRACK_IN_RANGE at normalized 0.5.
# Ratio has no conversion: natural_to_normalized("Compressor2", "Ratio", 0.5) == 0.5.
CANNED_RECIPE_IN_RANGE = {
    "Compressor2": {"Ratio": 0.5},
}

# Track with a large deviation: recipe wants 0.5, track has 0.0 (delta=0.5 > CRITICAL_THRESHOLD)
KICK_TRACK_OUT_OF_RANGE = {
    "index": 0,
    "name": "KICK_01",
    "type": "midi",
    "devices": [
        {
            "index": 0,
            "class_name": "Compressor2",
            "device_name": "Compressor",
            "parameters": [
                {"name": "Ratio", "value": 0.0},  # large deviation from recipe 0.5
            ],
        }
    ],
}

# Meter: kick at a normal level in GAIN_TARGETS["kick"] range (-10..-4 dBFS)
# 10^(-7/20) ≈ 0.447 → -7 dBFS → within (-10, -4)
KICK_METER_OK = {"name": "KICK_01", "meter_level": 0.447}

# Meter: kick too hot: 10^(-2/20) ≈ 0.794 → -2 dBFS → above (-10, -4)
KICK_METER_TOO_HOT = {"name": "KICK_01", "meter_level": 0.794}


# ---------------------------------------------------------------------------
# TestSchemaTypes
# ---------------------------------------------------------------------------

class TestSchemaTypes:
    """Test TypedDict construction for all evaluation schema types."""

    def test_evaluation_issue_construction(self):
        """EvaluationIssue dict can be constructed with all four required fields."""
        issue = EvaluationIssue(
            dimension="mix",
            severity="critical",
            message="Something is wrong",
            fix_hint="apply_mix_recipe(track_name='bass', genre='house', role='bass')",
        )
        assert "dimension" in issue
        assert "severity" in issue
        assert "message" in issue
        assert "fix_hint" in issue
        assert issue["dimension"] == "mix"
        assert issue["severity"] == "critical"

    def test_dimension_score_construction(self):
        """DimensionScore dict can be constructed with all four required fields."""
        ds = DimensionScore(
            dimension="mix",
            score=8.5,
            grade="B",
            issues=[],
        )
        assert "dimension" in ds
        assert "score" in ds
        assert "grade" in ds
        assert "issues" in ds
        assert ds["score"] == 8.5
        assert ds["grade"] == "B"

    def test_session_score_construction(self):
        """SessionScore dict can be constructed with all five required fields."""
        ss = SessionScore(
            score=7.0,
            grade="B",
            dimensions=[],
            issues=[],
            top_fixes=[],
        )
        assert "score" in ss
        assert "grade" in ss
        assert "dimensions" in ss
        assert "issues" in ss
        assert "top_fixes" in ss
        assert ss["score"] == 7.0


# ---------------------------------------------------------------------------
# TestGradeFromScore
# ---------------------------------------------------------------------------

class TestGradeFromScore:
    """Test letter grade thresholds for grade_from_score()."""

    def test_grade_a(self):
        """Scores >= 9.0 map to A."""
        assert grade_from_score(9.0) == "A"
        assert grade_from_score(10.0) == "A"

    def test_grade_b(self):
        """Scores in [7.0, 8.9] map to B."""
        assert grade_from_score(7.0) == "B"
        assert grade_from_score(8.9) == "B"

    def test_grade_c(self):
        """Scores in [5.0, 6.9] map to C."""
        assert grade_from_score(5.0) == "C"
        assert grade_from_score(6.9) == "C"

    def test_grade_d(self):
        """Scores in [3.0, 4.9] map to D."""
        assert grade_from_score(3.0) == "D"
        assert grade_from_score(4.9) == "D"

    def test_grade_f(self):
        """Scores < 3.0 map to F."""
        assert grade_from_score(2.9) == "F"
        assert grade_from_score(0.0) == "F"


# ---------------------------------------------------------------------------
# TestMixBalanceEvaluator
# ---------------------------------------------------------------------------

class TestMixBalanceEvaluator:
    """Test evaluate_mix_balance() with mocked connection."""

    def _make_conn(self, mix_state, meter_state):
        """Build a mock conn that returns canned RS responses."""
        mock_conn = MagicMock()

        def send_command(cmd, args):
            if cmd == "get_mix_state":
                return mix_state
            if cmd == "get_track_meters":
                return meter_state
            return {}

        mock_conn.send_command.side_effect = send_command
        return mock_conn

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_returns_dimension_score(self, mock_get_recipe):
        """evaluate_mix_balance returns a dict with dimension, score, grade, issues keys."""
        mock_get_recipe.return_value = CANNED_RECIPE_IN_RANGE
        conn = self._make_conn(
            _make_mix_state(tracks=[KICK_TRACK_IN_RANGE]),
            _make_meter_state(tracks=[KICK_METER_OK]),
        )
        result = evaluate_mix_balance("house", conn)
        assert "dimension" in result
        assert "score" in result
        assert "grade" in result
        assert "issues" in result

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_all_params_in_range_scores_ten(self, mock_get_recipe):
        """When all params are at recipe target, score == 10.0."""
        # natural_to_normalized("Compressor2", "Ratio", 0.5) returns 0.5 (no conversion)
        # KICK_TRACK_IN_RANGE also has Ratio=0.5 → delta=0 < DIFF_THRESHOLD
        mock_get_recipe.return_value = CANNED_RECIPE_IN_RANGE
        conn = self._make_conn(
            _make_mix_state(tracks=[KICK_TRACK_IN_RANGE]),
            _make_meter_state(tracks=[KICK_METER_OK]),
        )
        result = evaluate_mix_balance("house", conn)
        assert result["score"] == 10.0

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_out_of_range_param_creates_issue(self, mock_get_recipe):
        """A param deviating by 0.10 (>DIFF_THRESHOLD, <CRITICAL_THRESHOLD) creates a warning."""
        # Ratio has no conversion: natural_to_normalized("Compressor2", "Ratio", 0.6) == 0.6
        # Current value=0.5, recipe_norm=0.6 → delta=0.1 → warning (0.03 < 0.1 < 0.15)
        recipe = {"Compressor2": {"Ratio": 0.6}}
        mock_get_recipe.return_value = recipe
        track = {
            "index": 0,
            "name": "KICK_01",
            "type": "midi",
            "devices": [
                {
                    "index": 0,
                    "class_name": "Compressor2",
                    "device_name": "Compressor",
                    "parameters": [{"name": "Ratio", "value": 0.5}],
                }
            ],
        }
        conn = self._make_conn(
            _make_mix_state(tracks=[track]),
            _make_meter_state(tracks=[KICK_METER_OK]),
        )
        result = evaluate_mix_balance("house", conn)
        assert len(result["issues"]) >= 1
        # Find a param issue (not gain)
        param_issues = [
            i for i in result["issues"]
            if "Compressor2" in i["message"] or "deviates" in i["message"]
        ]
        assert any(i["severity"] == "warning" for i in param_issues)

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_large_deviation_creates_critical_issue(self, mock_get_recipe):
        """A param deviating by >= CRITICAL_THRESHOLD (0.15) creates a critical issue."""
        # KICK_TRACK_OUT_OF_RANGE has Threshold=0.0, recipe is 0.5 → delta=0.5 → critical
        mock_get_recipe.return_value = CANNED_RECIPE_IN_RANGE
        conn = self._make_conn(
            _make_mix_state(tracks=[KICK_TRACK_OUT_OF_RANGE]),
            _make_meter_state(tracks=[KICK_METER_OK]),
        )
        result = evaluate_mix_balance("house", conn)
        critical_issues = [i for i in result["issues"] if i["severity"] == "critical"]
        assert len(critical_issues) >= 1

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_gain_too_hot_creates_warning(self, mock_get_recipe):
        """Track gain significantly above GAIN_TARGETS creates at least one warning issue."""
        mock_get_recipe.return_value = CANNED_RECIPE_IN_RANGE
        conn = self._make_conn(
            _make_mix_state(tracks=[KICK_TRACK_IN_RANGE]),
            _make_meter_state(tracks=[KICK_METER_TOO_HOT]),
        )
        result = evaluate_mix_balance("house", conn)
        warning_issues = [i for i in result["issues"] if i["severity"] == "warning"]
        assert len(warning_issues) >= 1

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_all_params_out_of_range_scores_zero(self, mock_get_recipe):
        """When every compared param deviates beyond DIFF_THRESHOLD, param_score falls to 0."""
        # KICK_TRACK_OUT_OF_RANGE: Threshold=0.0, recipe_norm=0.5 → delta=0.5 → out of range
        mock_get_recipe.return_value = CANNED_RECIPE_IN_RANGE
        conn = self._make_conn(
            _make_mix_state(tracks=[KICK_TRACK_OUT_OF_RANGE]),
            _make_meter_state(tracks=[KICK_METER_OK]),
        )
        result = evaluate_mix_balance("house", conn)
        assert result["score"] == 0.0

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_partial_params_score_between_zero_and_ten(self, mock_get_recipe):
        """With one in-range and one out-of-range param, score is between 0 and 10."""
        # Both Ratio and S/C Mix have no conversion: natural_to_normalized returns value directly
        # Ratio: current=0.5, recipe=0.5 → delta=0 → in range
        # S/C Mix: current=0.1, recipe=0.9 → delta=0.8 → out of range (critical)
        recipe = {
            "Compressor2": {
                "Ratio": 0.5,       # current=0.5 → in range (delta=0)
                "S/C Mix": 0.9,     # current=0.1 → out of range (delta=0.8)
            }
        }
        mock_get_recipe.return_value = recipe
        track = {
            "index": 0,
            "name": "KICK_01",
            "type": "midi",
            "devices": [
                {
                    "index": 0,
                    "class_name": "Compressor2",
                    "device_name": "Compressor",
                    "parameters": [
                        {"name": "Ratio", "value": 0.5},
                        {"name": "S/C Mix", "value": 0.1},
                    ],
                }
            ],
        }
        conn = self._make_conn(
            _make_mix_state(tracks=[track]),
            _make_meter_state(tracks=[KICK_METER_OK]),
        )
        result = evaluate_mix_balance("house", conn)
        assert 0.0 < result["score"] < 10.0

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_no_recipe_track_excluded(self, mock_get_recipe):
        """Track with no role match is excluded from scoring — no issues raised for it."""
        mock_get_recipe.return_value = None  # no recipe
        unknown_track = {
            "index": 0,
            "name": "TRACK_UNKNOWN_42",
            "type": "midi",
            "devices": [
                {
                    "index": 0,
                    "class_name": "Compressor2",
                    "device_name": "Compressor",
                    "parameters": [{"name": "Threshold", "value": 0.0}],
                }
            ],
        }
        conn = self._make_conn(
            _make_mix_state(tracks=[unknown_track]),
            _make_meter_state(tracks=[{"name": "TRACK_UNKNOWN_42", "meter_level": 0.0}]),
        )
        result = evaluate_mix_balance("house", conn)
        # Unknown role → excluded from scoring → score stays 10.0 (no params compared)
        assert result["score"] == 10.0
        assert result["issues"] == []

    @patch("MCP_Server.evaluation.mix_balance.get_recipe")
    def test_dimension_is_mix(self, mock_get_recipe):
        """The dimension field of the returned DimensionScore is 'mix'."""
        mock_get_recipe.return_value = CANNED_RECIPE_IN_RANGE
        conn = self._make_conn(
            _make_mix_state(tracks=[KICK_TRACK_IN_RANGE]),
            _make_meter_state(tracks=[KICK_METER_OK]),
        )
        result = evaluate_mix_balance("house", conn)
        assert result["dimension"] == "mix"
