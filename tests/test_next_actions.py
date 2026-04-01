"""Tests for MCP_Server/orchestration/next_actions.py — NEXT-01, NEXT-02."""

import json
import sys
import types
from unittest.mock import MagicMock, patch

# --- Mock mcp module hierarchy (same as test_production_agenda.py) ---
_mock_mcp = types.ModuleType("mcp")
_mock_fastmcp = types.ModuleType("mcp.server.fastmcp")
_mock_server_mod = types.ModuleType("mcp.server")
_mock_fastmcp.Context = type("Context", (), {})
_mock_mcp.server = _mock_server_mod
_mock_server_mod.fastmcp = _mock_fastmcp
sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", _mock_server_mod)
sys.modules.setdefault("mcp.server.fastmcp", _mock_fastmcp)

if "MCP_Server.server" not in sys.modules:
    _mock_app_server = types.ModuleType("MCP_Server.server")
    _mcp_instance = MagicMock()
    _mcp_instance.tool.return_value = lambda fn: fn
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server

import pytest
from MCP_Server.orchestration.next_actions import get_next_actions_result, get_transition_guidance


def _make_track(name, has_instrument=True, index=0):
    return {"name": name, "has_instrument": has_instrument, "index": index, "devices": []}


def _make_conn(tracks, master_devices=None, clips_by_track=None):
    clips_by_track = clips_by_track or {}
    master_devices = master_devices or []
    arr_state = {"tracks": tracks, "cue_points": [], "song_length": 32.0}
    mix_state = {"tracks": [], "return_tracks": [], "master_track": {"devices": master_devices}}
    mock_conn = MagicMock()
    def send_command(cmd, params=None):
        if cmd == "get_arrangement_state":
            return arr_state
        elif cmd == "get_mix_state":
            return mix_state
        elif cmd == "get_arrangement_clips":
            idx = (params or {}).get("track_index", 0)
            name = next((t["name"] for t in tracks if t.get("index") == idx), "")
            return {"clips": clips_by_track.get(name, [])}
        return {}
    mock_conn.send_command.side_effect = send_command
    return mock_conn


class TestGetNextActions:
    def test_explicit_phase_no_connection_needed(self):
        """phase_name provided -> pure computation, no Ableton connection."""
        result = get_next_actions_result("house", phase_name="drums")
        assert "error" not in result
        assert result["active_phase"] == "drums"
        assert len(result["steps"]) > 0
        assert "explicitly specified" in result["checkpoint_summary"]

    def test_n_parameter_limits_steps(self):
        result = get_next_actions_result("house", phase_name="drums", n=3)
        assert len(result["steps"]) <= 3

    def test_n_clamped_to_25(self):
        result = get_next_actions_result("house", phase_name="setup", n=100)
        assert len(result["steps"]) <= 25

    def test_checkpoint_summary_contains_genre(self):
        result = get_next_actions_result("house", phase_name="bass")
        assert "house" in result["checkpoint_summary"].lower() or "house" in result["genre"]

    def test_fallback_no_connection(self):
        """When Ableton not connected and no phase_name, falls back to setup checklist."""
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint",
                   side_effect=Exception("connection refused")):
            result = get_next_actions_result("techno")
        assert result["active_phase"] == "setup"
        assert "No live session" in result["checkpoint_summary"]


class TestGetTransitionGuidance:
    def test_drums_incomplete_no_clips(self):
        tracks = [_make_track("Kick Drums", True, 0), _make_track("Bass", True, 1)]
        # No clips -> drums not complete
        with patch("MCP_Server.orchestration.next_actions.get_ableton_connection",
                   return_value=_make_conn(tracks)):
            result = get_transition_guidance("drums", "house")
        assert result["ready_to_advance"] is False
        assert len(result["blockers"]) > 0

    def test_drums_complete_with_clips(self):
        tracks = [_make_track("Kick Drums", True, 0), _make_track("Bass", True, 1)]
        clips = {"Kick Drums": [{"start_time": 0.0, "end_time": 8.0}]}
        with patch("MCP_Server.orchestration.next_actions.get_ableton_connection",
                   return_value=_make_conn(tracks, clips_by_track=clips)):
            result = get_transition_guidance("drums", "house")
        assert result["ready_to_advance"] is True
        assert result["blockers"] == []

class TestArrangementStepFiltering:
    def test_arrangement_steps_exclude_non_callable(self):
        """Arrangement checklist steps returned by get_next_actions_result
        never include non-callable placeholder tool names."""
        result = get_next_actions_result("house", phase_name="arrangement")
        assert "error" not in result
        steps = result["steps"]
        # All returned steps must have a real tool_name
        for step in steps:
            assert step["tool_name"] not in {"\u2014", "\u2014", "", None}, (
                f"Step {step['step_number']} has non-callable tool_name: {step['tool_name']!r}"
            )
        # The placeholder description should appear in notes
        assert len(result.get("notes", [])) >= 1
        assert any("top_fixes" in n for n in result["notes"])

    def test_arrangement_callable_steps_preserved(self):
        """Arrangement checklist preserves the 4 callable steps."""
        result = get_next_actions_result("house", phase_name="arrangement")
        steps = result["steps"]
        assert len(steps) == 4
        tool_names = [s["tool_name"] for s in steps]
        assert "get_arrangement_overview" in tool_names
        assert "get_arrangement_progress" in tool_names
        assert "evaluate_session" in tool_names
        assert "get_section_checklist" in tool_names


class TestGetTransitionGuidance:
    def test_to_phase_override(self):
        tracks = [_make_track("Kick", True, 0)]
        clips = {"Kick": [{"start_time": 0.0, "end_time": 4.0}]}
        with patch("MCP_Server.orchestration.next_actions.get_ableton_connection",
                   return_value=_make_conn(tracks, clips_by_track=clips)):
            result = get_transition_guidance("drums", "house", to_phase="mix")
        assert result["to_phase"] == "mix"
        assert result["next_phase"] == "mix"
