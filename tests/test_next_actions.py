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
    return {"name": name, "has_instrument": has_instrument, "index": index, "devices": [], "clips": [], "clip_count": 0, "has_clips": False}


def _make_conn(tracks, master_devices=None, clips_by_track=None):
    clips_by_track = clips_by_track or {}
    master_devices = master_devices or []
    # Inject real clips into each track dict so get_arrangement_state carries them
    enriched_tracks = []
    for t in tracks:
        tc = dict(t)
        tc["clips"] = clips_by_track.get(tc["name"], [])
        tc["clip_count"] = len(tc["clips"])
        tc["has_clips"] = len(tc["clips"]) > 0
        enriched_tracks.append(tc)
    arr_state = {"tracks": enriched_tracks, "cue_points": [], "song_length": 32.0}
    mix_state = {"tracks": [], "return_tracks": [], "master_track": {"devices": master_devices}}
    mock_conn = MagicMock()
    def send_command(cmd, params=None):
        if cmd == "get_arrangement_state":
            return arr_state
        elif cmd == "get_mix_state":
            return mix_state
        elif cmd == "get_arrangement_clips":
            idx = (params or {}).get("track_index", 0)
            name = next((t["name"] for t in enriched_tracks if t.get("index") == idx), "")
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
    def test_arrangement_steps_all_callable(self):
        """All arrangement checklist steps have real (callable) tool names."""
        result = get_next_actions_result("house", phase_name="arrangement")
        assert "error" not in result
        for step in result["steps"]:
            assert step["tool_name"] not in {"\u2014", "", None}, (
                f"Step {step['step_number']} has non-callable tool_name: {step['tool_name']!r}"
            )

    def test_arrangement_callable_steps_preserved(self):
        """Arrangement checklist contains exactly 4 callable steps."""
        result = get_next_actions_result("house", phase_name="arrangement")
        steps = result["steps"]
        assert len(steps) == 4
        tool_names = [s["tool_name"] for s in steps]
        assert "get_arrangement_overview" in tool_names
        assert "get_arrangement_progress" in tool_names
        assert "evaluate_session" in tool_names
        assert "get_section_checklist" in tool_names


class TestGetTransitionGuidanceToPhase:
    def test_to_phase_override(self):
        tracks = [_make_track("Kick", True, 0)]
        clips = {"Kick": [{"start_time": 0.0, "end_time": 4.0}]}
        with patch("MCP_Server.orchestration.next_actions.get_ableton_connection",
                   return_value=_make_conn(tracks, clips_by_track=clips)):
            result = get_transition_guidance("drums", "house", to_phase="mix")
        assert result["to_phase"] == "mix"
        assert result["next_phase"] == "mix"


class TestTransitionGuidancePreFetched:
    def test_prefetched_skips_ableton_connection(self):
        """When all three state params provided, no Ableton connection is made."""
        tracks = [_make_track("Kick Drums", True, 0)]
        clips_by_track = {"Kick Drums": [{"start_time": 0.0, "end_time": 8.0}]}
        master_devices = []
        with patch("MCP_Server.orchestration.next_actions.get_ableton_connection") as mock_gac:
            result = get_transition_guidance(
                "drums", "house",
                tracks=tracks, clips_by_track=clips_by_track,
                master_devices=master_devices,
            )
        mock_gac.assert_not_called()
        assert result["ready_to_advance"] is True

    def test_prefetched_incomplete_phase(self):
        """Pre-fetched data correctly reports incomplete phase."""
        tracks = [_make_track("Kick Drums", True, 0)]
        clips_by_track = {"Kick Drums": []}  # no clips
        master_devices = []
        with patch("MCP_Server.orchestration.next_actions.get_ableton_connection") as mock_gac:
            result = get_transition_guidance(
                "drums", "house",
                tracks=tracks, clips_by_track=clips_by_track,
                master_devices=master_devices,
            )
        mock_gac.assert_not_called()
        assert result["ready_to_advance"] is False
        assert len(result["blockers"]) > 0

    def test_partial_prefetch_still_queries_ableton(self):
        """If only some state params provided, falls back to Ableton query."""
        tracks = [_make_track("Kick", True, 0)]
        # Only tracks provided, not clips_by_track or master_devices
        mock_conn = _make_conn(tracks, clips_by_track={"Kick": []})
        with patch("MCP_Server.orchestration.next_actions.get_ableton_connection",
                   return_value=mock_conn):
            result = get_transition_guidance("drums", "house", tracks=tracks)
        # Should have called get_ableton_connection since clips_by_track was None
        assert "error" not in result
