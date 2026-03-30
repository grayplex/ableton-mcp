"""Tests for analysis MCP tools: get_mix_state and check_gain_staging.

Covers:
- GAIN_TARGETS data module validation (TestGainTargets)
- _meter_to_db private helper (TestMeterToDb)
- _infer_role private helper (TestInferRole)
- get_mix_state MCP tool (TestGetMixState)
- check_gain_staging MCP tool (TestCheckGainStaging)
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
from unittest.mock import MagicMock, patch  # noqa: E402

import pytest  # noqa: E402

from MCP_Server.devices.catalog import ROLES  # noqa: E402
from MCP_Server.devices.gain_targets import GAIN_TARGETS  # noqa: E402
from MCP_Server.tools.analysis import (  # noqa: E402
    _infer_role,
    _meter_to_db,
    check_gain_staging,
    get_mix_state,
)


# ---------------------------------------------------------------------------
# Helpers / canned fixtures
# ---------------------------------------------------------------------------

def _make_meters_response(tracks=None, return_tracks=None, master=None):
    """Build a canned get_track_meters RS response."""
    return {
        "tracks": tracks or [],
        "return_tracks": return_tracks or [],
        "master_track": master or {"name": "Master", "type": "master", "meter_level": 0.5},
    }


def _make_mix_state_response():
    """Build a canned get_mix_state RS response."""
    return {
        "tracks": [
            {
                "index": 0,
                "name": "KICK_01",
                "type": "midi",
                "devices": [
                    {
                        "index": 0,
                        "class_name": "Simpler",
                        "device_name": "Simpler",
                        "parameters": [{"name": "Volume", "value": 0.85}],
                    }
                ],
            }
        ],
        "return_tracks": [],
        "master_track": {
            "index": 0,
            "name": "Master",
            "type": "master",
            "devices": [],
        },
    }


# ---------------------------------------------------------------------------
# TestGainTargets
# ---------------------------------------------------------------------------

class TestGainTargets:
    def test_gain_targets_covers_all_roles(self):
        assert GAIN_TARGETS.keys() == set(ROLES)

    def test_all_targets_have_float_tuples(self):
        for role, tgt in GAIN_TARGETS.items():
            assert isinstance(tgt, tuple), f"{role} target is not a tuple"
            assert len(tgt) == 2, f"{role} target does not have 2 elements"
            assert isinstance(tgt[0], float), f"{role} low bound is not float"
            assert isinstance(tgt[1], float), f"{role} high bound is not float"

    def test_all_low_less_than_high(self):
        for role, (lo, hi) in GAIN_TARGETS.items():
            assert lo < hi, f"{role}: low ({lo}) >= high ({hi})"

    def test_kick_target_is_correct(self):
        assert GAIN_TARGETS["kick"] == (-10.0, -4.0)

    def test_master_target_is_correct(self):
        assert GAIN_TARGETS["master"] == (-6.0, -1.0)


# ---------------------------------------------------------------------------
# TestMeterToDb
# ---------------------------------------------------------------------------

class TestMeterToDb:
    def test_zero_returns_none(self):
        assert _meter_to_db(0.0) is None

    def test_negative_returns_none(self):
        assert _meter_to_db(-0.1) is None

    def test_one_returns_zero_db(self):
        assert _meter_to_db(1.0) == 0.0

    def test_known_value(self):
        # 0.316 ≈ 10^(-0.5) → -10 dBFS
        result = _meter_to_db(0.316)
        assert result is not None
        assert abs(result - (-10.0)) < 0.1

    def test_half_amplitude(self):
        result = _meter_to_db(0.5)
        assert result is not None
        assert abs(result - (-6.02)) < 0.1


# ---------------------------------------------------------------------------
# TestInferRole
# ---------------------------------------------------------------------------

class TestInferRole:
    def test_kick_uppercase(self):
        assert _infer_role("KICK_01") == "kick"

    def test_bass_substring(self):
        assert _infer_role("bass_synth") == "bass"

    def test_no_match_returns_none(self):
        assert _infer_role("snare_top") is None

    def test_master_track(self):
        assert _infer_role("Master") == "master"

    def test_return_track(self):
        assert _infer_role("Reverb Return A") == "return"

    def test_first_match_wins(self):
        # "pad" is at index 3 in ROLES, "atmospheric" at index 6
        assert _infer_role("pad_atmo") == "pad"


# ---------------------------------------------------------------------------
# TestGetMixState
# ---------------------------------------------------------------------------

class TestGetMixState:
    def test_calls_get_mix_state_command(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state_response()
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            get_mix_state(None)
        mock_conn.send_command.assert_called_once_with("get_mix_state", {})

    def test_returns_json_string(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state_response()
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = get_mix_state(None)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_response_has_required_keys(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_mix_state_response()
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = get_mix_state(None)
        parsed = json.loads(result)
        assert "tracks" in parsed
        assert "return_tracks" in parsed
        assert "master_track" in parsed


# ---------------------------------------------------------------------------
# TestCheckGainStaging
# ---------------------------------------------------------------------------

class TestCheckGainStaging:
    def test_calls_get_track_meters_command(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 0.316}]
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            check_gain_staging(None)
        mock_conn.send_command.assert_called_once_with("get_track_meters", {})

    def test_returns_json_string(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response()
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_ok_track_flagged_correctly(self):
        # KICK_01 with meter_level=0.316 → ~-10 dBFS; kick target is (-10.0, -4.0) → ok
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 0.316}],
            master={"name": "Master", "type": "master", "meter_level": 0.316},
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        kick_entry = next(t for t in parsed["tracks"] if t["name"] == "KICK_01")
        assert kick_entry["status"] == "ok"
        assert kick_entry["role"] == "kick"

    def test_too_hot_track(self):
        # meter_level=1.0 → 0 dBFS; kick target is (-10.0, -4.0) → too_hot
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 1.0}],
            master={"name": "Master", "type": "master", "meter_level": 1.0},
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        kick_entry = next(t for t in parsed["tracks"] if t["name"] == "KICK_01")
        assert kick_entry["status"] == "too_hot"

    def test_too_quiet_track(self):
        # meter_level=0.032 → ~-30 dBFS; kick target is (-10.0, -4.0) → too_quiet
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 0.032}],
            master={"name": "Master", "type": "master", "meter_level": 0.032},
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        kick_entry = next(t for t in parsed["tracks"] if t["name"] == "KICK_01")
        assert kick_entry["status"] == "too_quiet"

    def test_no_signal_track(self):
        # meter_level=0.0 → no_signal
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 0.0}],
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        kick_entry = next(t for t in parsed["tracks"] if t["name"] == "KICK_01")
        assert kick_entry["status"] == "no_signal"

    def test_unknown_role_track(self):
        # "snare_top" doesn't match any role → role=null, status=unknown
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "snare_top", "type": "midi", "meter_level": 0.316}],
            master={"name": "Master", "type": "master", "meter_level": 0.316},
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        snare_entry = next(t for t in parsed["tracks"] if t["name"] == "snare_top")
        assert snare_entry["role"] is None
        assert snare_entry["status"] == "unknown"

    def test_all_zero_warning(self):
        # All meter_levels are 0.0 → warning field present
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 0.0}],
            master={"name": "Master", "type": "master", "meter_level": 0.0},
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        assert "warning" in parsed
        assert "All meters are 0" in parsed["warning"]

    def test_no_warning_when_playing(self):
        # At least one meter > 0 → no warning
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 0.316}],
            master={"name": "Master", "type": "master", "meter_level": 0.5},
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        assert "warning" not in parsed

    def test_tracks_appear_in_output(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = _make_meters_response(
            tracks=[{"index": 0, "name": "KICK_01", "type": "midi", "meter_level": 0.316}],
            master={"name": "Master", "type": "master", "meter_level": 0.5},
        )
        with patch("MCP_Server.tools.analysis.get_ableton_connection", return_value=mock_conn):
            result = check_gain_staging(None)
        parsed = json.loads(result)
        assert len(parsed["tracks"]) > 0
