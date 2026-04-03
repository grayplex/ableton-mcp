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


def _make_track(name, has_instrument=True, index=0, device_classes=None):
    return {"name": name, "has_instrument": has_instrument, "index": index, "device_classes": device_classes or [], "clips": [], "clip_count": 0, "has_clips": False}


def _make_conn(tracks, master_device_classes=None, clips_by_track=None):
    clips_by_track = clips_by_track or {}
    master_device_classes = master_device_classes or []
    # Inject real clips into each track dict so get_arrangement_state carries them
    enriched_tracks = []
    for t in tracks:
        tc = dict(t)
        tc["clips"] = clips_by_track.get(tc["name"], [])
        tc["clip_count"] = len(tc["clips"])
        tc["has_clips"] = len(tc["clips"]) > 0
        enriched_tracks.append(tc)
    arr_state = {"tracks": enriched_tracks, "cue_points": [], "song_length": 32.0}
    device_classes_state = {
        "tracks": [{"index": i, "name": tc["name"],
                    "device_classes": tc.get("device_classes", [])}
                   for i, tc in enumerate(enriched_tracks)],
        "return_tracks": [],
        "master_track": {"name": "Master", "device_classes": master_device_classes}
    }
    mock_conn = MagicMock()
    def send_command(cmd, params=None):
        if cmd == "get_arrangement_state":
            return arr_state
        elif cmd == "get_device_classes":
            return device_classes_state
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


class TestHistStepSkipping:
    """HIST-01: active_phase_progress used to skip already-completed steps."""

    def _checkpoint(self, active_phase, progress, genre="house"):
        return {
            "genre": genre,
            "completed_phases": [],
            "active_phase": active_phase,
            "active_phase_progress": progress,
            "pending_steps": [],
            "session_stats": {},
            "next_phase": "bass",
            "resume_hint": "continue",
        }

    def test_progress_zero_returns_from_step_1(self):
        """progress=0.0 → no steps skipped, first step_number is 1."""
        cp = self._checkpoint("drums", 0.0)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        assert result["steps"][0]["step_number"] == 1
        assert result.get("steps_skipped", 0) == 0

    def test_progress_0_3_skips_steps(self):
        """progress=0.3 → int(0.3 * total_steps) steps skipped, first returned step > 1."""
        cp = self._checkpoint("drums", 0.3)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        # Drums has 7 steps; skip_count = int(0.3 * 7) = 2 → first step number = 3
        assert result["steps"][0]["step_number"] > 1
        assert result["steps_skipped"] == 2

    def test_steps_skipped_key_present_when_progress_above_threshold(self):
        cp = self._checkpoint("drums", 0.3)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        assert "steps_skipped" in result
        assert result["steps_skipped"] > 0

    def test_steps_skipped_key_absent_when_progress_zero(self):
        cp = self._checkpoint("drums", 0.0)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        assert "steps_skipped" not in result

    def test_always_returns_at_least_one_step(self):
        """Even at very high progress, at least 1 step is always returned."""
        cp = self._checkpoint("master", 0.95)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        assert len(result["steps"]) >= 1

    def test_explicit_phase_not_affected_by_progress(self):
        """phase_name=explicit → always full checklist from step 1 regardless of progress."""
        cp = self._checkpoint("drums", 0.3)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", phase_name="drums", n=25)
        assert result["steps"][0]["step_number"] == 1
        assert result.get("steps_skipped", 0) == 0

    def test_n_still_limits_steps_after_skipping(self):
        """n parameter caps the returned steps count even after skipping."""
        cp = self._checkpoint("drums", 0.0)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=2)
        assert len(result["steps"]) <= 2

    def test_returned_steps_are_contiguous_after_skip(self):
        """Step numbers in returned list are sequential after the skip offset."""
        cp = self._checkpoint("drums", 0.3)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        nums = [s["step_number"] for s in result["steps"]]
        # Step numbers should increase by 1 each time
        for i in range(1, len(nums)):
            assert nums[i] == nums[i - 1] + 1

    def test_skip_count_matches_steps_skipped_field(self):
        """steps_skipped value is consistent with the first returned step number."""
        cp = self._checkpoint("drums", 0.3)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        skipped = result["steps_skipped"]
        first_step = result["steps"][0]["step_number"]
        assert first_step == skipped + 1

    def test_high_progress_arrangement_skips_proportionally(self):
        """Arrangement with progress=0.75 skips 3 of 4 steps."""
        cp = self._checkpoint("arrangement", 0.75)
        with patch("MCP_Server.orchestration.next_actions.get_checkpoint", return_value=cp):
            result = get_next_actions_result("house", n=25)
        # Arrangement has 4 steps; skip_count = int(0.75 * 4) = 3
        assert result.get("steps_skipped", 0) == 3
        assert len(result["steps"]) == 1


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
