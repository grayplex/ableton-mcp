"""Tests for MCP_Server/tools/intelligence.py: suggest_mix_adjustments tool.

Covers:
- JSON output structure with track, role, genre, total_suggestions, devices
- Diff computation: normalized value comparison with threshold filtering
- Display values present when conversion is available
- Unloaded devices silently skipped
- Track not found error
- Role inference when role=None
- Role cannot be inferred error
- No recipe for role x genre error
- Read-only: no write commands issued
- Output uses display names not class names
- total_suggestions=0 returns empty devices with note
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

import json  # noqa: E402
from unittest.mock import MagicMock, patch, call  # noqa: E402

import pytest  # noqa: E402

from MCP_Server.tools.intelligence import suggest_mix_adjustments  # noqa: E402


# ---------------------------------------------------------------------------
# Canned fixtures
# ---------------------------------------------------------------------------

def _make_mix_state(tracks=None, return_tracks=None, master=None):
    """Build a canned get_mix_state RS response."""
    return {
        "tracks": tracks or [],
        "return_tracks": return_tracks or [],
        "master_track": master or {"name": "Master", "type": "master", "devices": []},
    }


CANNED_KICK_TRACK = {
    "index": 0,
    "name": "KICK_01",
    "type": "midi",
    "devices": [
        {
            "index": 0,
            "class_name": "Eq8",
            "device_name": "EQ Eight",
            "parameters": [
                {"name": "1 Frequency A", "value": 0.23},
                {"name": "1 Gain A", "value": 0.5},
                {"name": "1 Filter On A", "value": 1.0},
            ],
        }
    ],
}

# Recipe in natural units that produces different normalized values
CANNED_RECIPE = {
    "Eq8": {"1 Frequency A": 120, "1 Gain A": 3.0, "1 Filter On A": 1},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSuggestMixAdjustments:
    """Test suggest_mix_adjustments MCP tool."""

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_returns_json_with_expected_keys(self, mock_conn_fn, mock_get_recipe):
        """Output JSON has track, role, genre, total_suggestions, devices keys."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        assert "track" in data
        assert "role" in data
        assert "genre" in data
        assert "total_suggestions" in data
        assert "devices" in data

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_diff_computation_produces_suggestions(self, mock_conn_fn, mock_get_recipe):
        """When current normalized differs from recipe-derived normalized by >0.03, suggestion returned."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        # 1 Frequency A: current=0.23, recipe 120 Hz -> normalized ~0.264 -> delta ~0.034 > 0.03
        # 1 Gain A: current=0.5, recipe 3.0 dB -> depends on conversion
        # 1 Filter On A: current=1.0, recipe 1 -> normalized 1.0 -> delta=0 (filtered)
        assert data["total_suggestions"] >= 1

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_threshold_filtering(self, mock_conn_fn, mock_get_recipe):
        """Diffs below 0.03 are excluded from output."""
        # Set current value very close to recipe target so delta < 0.03
        close_track = {
            "index": 0,
            "name": "KICK_01",
            "type": "midi",
            "devices": [
                {
                    "index": 0,
                    "class_name": "Eq8",
                    "device_name": "EQ Eight",
                    "parameters": [
                        {"name": "1 Filter On A", "value": 1.0},
                    ],
                }
            ],
        }
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[close_track])
        mock_conn_fn.return_value = mock_conn
        # Recipe has 1 Filter On A = 1 -> normalized = 1.0 -> delta=0
        mock_get_recipe.return_value = {"Eq8": {"1 Filter On A": 1}}

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        assert data["total_suggestions"] == 0

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_suggestion_has_required_fields(self, mock_conn_fn, mock_get_recipe):
        """Each suggestion has parameter, current_normalized, suggested_normalized, reason."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        # Find any suggestion
        for device_name, suggestions in data["devices"].items():
            for s in suggestions:
                assert "parameter" in s
                assert "current_normalized" in s
                assert "suggested_normalized" in s
                assert "reason" in s

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_display_values_present(self, mock_conn_fn, mock_get_recipe):
        """Display values (current_display, suggested_display) present when conversion available."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        # Frequency params have Hz conversion -> display values should exist
        found_display = False
        for device_name, suggestions in data["devices"].items():
            for s in suggestions:
                if "current_display" in s and "suggested_display" in s:
                    found_display = True
        assert found_display, "Expected at least one suggestion with display values"

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_missing_device_skipped(self, mock_conn_fn, mock_get_recipe):
        """Unloaded device (recipe has it, track doesn't) is silently skipped."""
        no_eq_track = {
            "index": 0,
            "name": "KICK_01",
            "type": "midi",
            "devices": [],  # No devices loaded
        }
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[no_eq_track])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        assert data["total_suggestions"] == 0
        assert data["devices"] == {}

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_track_not_found_error(self, mock_conn_fn, mock_get_recipe):
        """Track not found returns format_error string."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[])
        mock_conn_fn.return_value = mock_conn

        result = suggest_mix_adjustments(None, "NONEXISTENT", "house", "kick")

        assert "not found" in result.lower() or "error" in result.lower()

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_role_inference(self, mock_conn_fn, mock_get_recipe):
        """When role=None, role is inferred from track name via _infer_role."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        result = suggest_mix_adjustments(None, "KICK_01", "house")  # no role
        data = json.loads(result)

        assert data["role"] == "kick"

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_role_cannot_be_inferred_error(self, mock_conn_fn, mock_get_recipe):
        """Role cannot be inferred and not provided returns error."""
        unknown_track = {
            "index": 0,
            "name": "TRACK_42",
            "type": "midi",
            "devices": [],
        }
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[unknown_track])
        mock_conn_fn.return_value = mock_conn

        result = suggest_mix_adjustments(None, "TRACK_42", "house")  # no role

        assert "cannot infer" in result.lower() or "role" in result.lower()

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_no_recipe_error(self, mock_conn_fn, mock_get_recipe):
        """No recipe for role x genre returns error."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = None

        result = suggest_mix_adjustments(None, "KICK_01", "nonexistent_genre", "kick")

        assert "no recipe" in result.lower() or "error" in result.lower()

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_no_write_commands(self, mock_conn_fn, mock_get_recipe):
        """No write commands issued (send_command called only with 'get_mix_state')."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        suggest_mix_adjustments(None, "KICK_01", "house", "kick")

        # Only get_mix_state should be called
        for c in mock_conn.send_command.call_args_list:
            assert c[0][0] == "get_mix_state", f"Unexpected command: {c[0][0]}"

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_output_uses_display_names(self, mock_conn_fn, mock_get_recipe):
        """Output uses display names (e.g., 'EQ Eight') not class names (e.g., 'Eq8')."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[CANNED_KICK_TRACK])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = CANNED_RECIPE

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        if data["devices"]:
            device_keys = list(data["devices"].keys())
            for key in device_keys:
                assert key != "Eq8", "Should use display name 'EQ Eight', not class name 'Eq8'"

    @patch("MCP_Server.tools.intelligence.get_recipe")
    @patch("MCP_Server.tools.intelligence.get_ableton_connection")
    def test_zero_suggestions_has_note(self, mock_conn_fn, mock_get_recipe):
        """total_suggestions=0 returns empty devices dict with note."""
        close_track = {
            "index": 0,
            "name": "KICK_01",
            "type": "midi",
            "devices": [
                {
                    "index": 0,
                    "class_name": "Eq8",
                    "device_name": "EQ Eight",
                    "parameters": [
                        {"name": "1 Filter On A", "value": 1.0},
                    ],
                }
            ],
        }
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state(tracks=[close_track])
        mock_conn_fn.return_value = mock_conn
        mock_get_recipe.return_value = {"Eq8": {"1 Filter On A": 1}}

        result = suggest_mix_adjustments(None, "KICK_01", "house", "kick")
        data = json.loads(result)

        assert data["total_suggestions"] == 0
        assert "note" in data
