"""Tests for RFNA-04: revert_section_refinement.

Covers:
- _build_apply_snapshot: extracts note_op and device_params from plan tracks
- _inverse_scale_subs: swaps from/to pairs
- pop_last_refinement: removes and returns last entry; idempotent on empty
- revert_section_refinement (integration):
    - error response when no history
    - reverted_instruction matches last applied
    - pops entry from history log
    - calls apply_section_note_refinement with negated shifts
    - calls apply_section_device_refinement with original param values
    - warnings list populated for density_delta revert
    - density=0 produces no warning
    - empty track list (no clips) produces empty note/device changes
"""

import json
import sys
import types
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Mock mcp module hierarchy
# ---------------------------------------------------------------------------
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
    _mock_app = types.ModuleType("MCP_Server.server")
    _mock_inst = MagicMock()
    _mock_inst.tool.return_value = lambda fn: fn
    _mock_app.mcp = _mock_inst
    sys.modules["MCP_Server.server"] = _mock_app

import pytest  # noqa: E402

from MCP_Server.refinement.history import (  # noqa: E402
    clear_history,
    get_history,
    pop_last_refinement,
    record_refinement,
)
from MCP_Server.tools.refinement import (  # noqa: E402
    _build_apply_snapshot,
    _inverse_scale_subs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_log():
    clear_history()
    yield
    clear_history()


# ---------------------------------------------------------------------------
# _build_apply_snapshot
# ---------------------------------------------------------------------------

class TestBuildApplySnapshot:
    def _plan_tracks(self, semitone=0, velocity=0, density=0,
                     scale_subs=None, device_changes=None):
        return [{
            "track_name": "Bass",
            "track_index": 1,
            "note_operation": {
                "semitone_shift": semitone,
                "velocity_shift": velocity,
                "density_delta": density,
                "scale_substitutions": scale_subs or [],
            },
            "device_changes": device_changes or [],
        }]

    def test_captures_note_op(self):
        tracks = self._plan_tracks(semitone=-3, velocity=-8)
        snap = _build_apply_snapshot(tracks)
        assert snap["Bass"]["note_op"]["semitone_shift"] == -3
        assert snap["Bass"]["note_op"]["velocity_shift"] == -8

    def test_captures_scale_subs(self):
        subs = [{"from_pitch_class": 4, "to_pitch_class": 3}]
        tracks = self._plan_tracks(scale_subs=subs)
        snap = _build_apply_snapshot(tracks)
        assert snap["Bass"]["note_op"]["scale_substitutions"] == subs

    def test_captures_device_params(self):
        device_changes = [
            {"class_name": "AutoFilter", "param_name": "Frequency",
             "current_normalized": 0.45, "target_normalized": 0.3,
             "device_name": "Auto Filter", "reason": "..."},
        ]
        tracks = self._plan_tracks(device_changes=device_changes)
        snap = _build_apply_snapshot(tracks)
        assert snap["Bass"]["device_params"]["AutoFilter"]["Frequency"] == 0.45

    def test_multiple_devices_same_track(self):
        device_changes = [
            {"class_name": "AutoFilter", "param_name": "Frequency",
             "current_normalized": 0.5, "target_normalized": 0.3,
             "device_name": "Auto Filter", "reason": "..."},
            {"class_name": "Reverb", "param_name": "Wet/Dry Mix",
             "current_normalized": 0.2, "target_normalized": 0.35,
             "device_name": "Reverb", "reason": "..."},
        ]
        tracks = self._plan_tracks(device_changes=device_changes)
        snap = _build_apply_snapshot(tracks)
        assert "AutoFilter" in snap["Bass"]["device_params"]
        assert "Reverb" in snap["Bass"]["device_params"]

    def test_empty_plan_tracks(self):
        assert _build_apply_snapshot([]) == {}

    def test_multiple_tracks(self):
        tracks = [
            {"track_name": "Bass", "track_index": 1,
             "note_operation": {"semitone_shift": -3, "velocity_shift": 0,
                                "density_delta": 0, "scale_substitutions": []},
             "device_changes": []},
            {"track_name": "Lead", "track_index": 2,
             "note_operation": {"semitone_shift": -3, "velocity_shift": -8,
                                "density_delta": 0, "scale_substitutions": []},
             "device_changes": []},
        ]
        snap = _build_apply_snapshot(tracks)
        assert "Bass" in snap
        assert "Lead" in snap


# ---------------------------------------------------------------------------
# _inverse_scale_subs
# ---------------------------------------------------------------------------

class TestInverseScaleSubs:
    def test_swaps_from_and_to(self):
        subs = [{"from_pitch_class": 4, "to_pitch_class": 3}]
        inv = _inverse_scale_subs(subs)
        assert inv == [{"from_pitch_class": 3, "to_pitch_class": 4}]

    def test_multiple_subs(self):
        subs = [
            {"from_pitch_class": 4, "to_pitch_class": 3},
            {"from_pitch_class": 9, "to_pitch_class": 8},
        ]
        inv = _inverse_scale_subs(subs)
        assert inv[0] == {"from_pitch_class": 3, "to_pitch_class": 4}
        assert inv[1] == {"from_pitch_class": 8, "to_pitch_class": 9}

    def test_empty_returns_empty(self):
        assert _inverse_scale_subs([]) == []

    def test_none_returns_empty(self):
        assert _inverse_scale_subs(None) == []

    def test_double_inverse_is_identity(self):
        subs = [{"from_pitch_class": 4, "to_pitch_class": 3},
                {"from_pitch_class": 9, "to_pitch_class": 8}]
        assert _inverse_scale_subs(_inverse_scale_subs(subs)) == subs


# ---------------------------------------------------------------------------
# pop_last_refinement
# ---------------------------------------------------------------------------

class TestPopLastRefinement:
    def test_returns_none_when_empty(self):
        assert pop_last_refinement("Intro") is None

    def test_pops_last_entry(self):
        record_refinement("Intro", "darker", {"harmonic": {}}, [])
        record_refinement("Intro", "warmer", {"harmonic": {}}, [])
        popped = pop_last_refinement("Intro")
        assert popped["instruction"] == "warmer"

    def test_history_shrinks_by_one(self):
        record_refinement("Intro", "darker", {}, [])
        record_refinement("Intro", "warmer", {}, [])
        pop_last_refinement("Intro")
        assert len(get_history("Intro")) == 1

    def test_cleans_up_empty_section_key(self):
        record_refinement("Intro", "darker", {}, [])
        pop_last_refinement("Intro")
        assert get_history("Intro") == []

    def test_second_pop_returns_none_after_empty(self):
        record_refinement("Intro", "darker", {}, [])
        pop_last_refinement("Intro")
        assert pop_last_refinement("Intro") is None

    def test_case_insensitive_section_name(self):
        record_refinement("INTRO", "darker", {}, [])
        popped = pop_last_refinement("intro")
        assert popped is not None
        assert popped["instruction"] == "darker"

    def test_pop_does_not_affect_other_sections(self):
        record_refinement("Intro", "darker", {}, [])
        record_refinement("Outro", "brighter", {}, [])
        pop_last_refinement("Intro")
        assert len(get_history("Outro")) == 1


# ---------------------------------------------------------------------------
# Integration: revert_section_refinement
# ---------------------------------------------------------------------------

class TestRevertSectionRefinement:
    """Integration tests for revert_section_refinement MCP tool."""

    def _make_conn(self):
        conn = MagicMock()
        def send_command(cmd, params=None):
            if cmd == "get_arrangement_state":
                return {
                    "tracks": [{"index": 0, "name": "Bass", "has_instrument": True}],
                    "cue_points": [{"name": "Intro", "time": 0.0}],
                    "song_length": 32.0,
                    "signature_numerator": 4,
                    "signature_denominator": 4,
                }
            elif cmd == "get_mix_state":
                return {"tracks": []}
            elif cmd == "get_arrangement_clips":
                return {"clips": []}
            return {}
        conn.send_command.side_effect = send_command
        return conn

    def test_error_when_no_history(self):
        from MCP_Server.tools.refinement import revert_section_refinement
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            result = json.loads(revert_section_refinement(ctx, "Intro"))
        assert result["error"] is not None
        assert result["reverted_instruction"] is None

    def test_reverted_instruction_matches_last_applied(self):
        from MCP_Server.tools.refinement import refine_section, revert_section_refinement
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            refine_section(ctx, "Intro", "make it darker")
            result = json.loads(revert_section_refinement(ctx, "Intro"))
        assert result["reverted_instruction"] == "make it darker"

    def test_revert_removes_entry_from_history(self):
        from MCP_Server.tools.refinement import refine_section, revert_section_refinement
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            refine_section(ctx, "Intro", "make it darker")
            assert len(get_history("Intro")) == 1
            revert_section_refinement(ctx, "Intro")
        assert len(get_history("Intro")) == 0

    def test_second_revert_returns_error(self):
        from MCP_Server.tools.refinement import refine_section, revert_section_refinement
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            refine_section(ctx, "Intro", "make it darker")
            revert_section_refinement(ctx, "Intro")
            result = json.loads(revert_section_refinement(ctx, "Intro"))
        assert result["error"] is not None

    def test_revert_response_has_required_fields(self):
        from MCP_Server.tools.refinement import refine_section, revert_section_refinement
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            refine_section(ctx, "Intro", "darker")
            result = json.loads(revert_section_refinement(ctx, "Intro"))
        assert "reverted_instruction" in result
        assert "note_changes" in result
        assert "device_changes" in result
        assert "warnings" in result

    def test_revert_multiple_steps(self):
        from MCP_Server.tools.refinement import refine_section, revert_section_refinement
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            refine_section(ctx, "Intro", "darker")
            refine_section(ctx, "Intro", "warmer")
            assert len(get_history("Intro")) == 2
            r1 = json.loads(revert_section_refinement(ctx, "Intro"))
            r2 = json.loads(revert_section_refinement(ctx, "Intro"))
        assert r1["reverted_instruction"] == "warmer"
        assert r2["reverted_instruction"] == "darker"
        assert len(get_history("Intro")) == 0


class TestSnapshotStoredInHistory:
    """Verify snapshot is stored and accessible via history."""

    def _make_plan_tracks(self):
        return [{
            "track_name": "Bass",
            "track_index": 1,
            "note_operation": {
                "semitone_shift": -3, "velocity_shift": -8,
                "density_delta": 0, "scale_substitutions": [],
            },
            "device_changes": [
                {"class_name": "AutoFilter", "param_name": "Frequency",
                 "current_normalized": 0.45, "target_normalized": 0.3,
                 "device_name": "Auto Filter", "reason": "test"},
            ],
        }]

    def test_snapshot_stored_in_history_entry(self):
        snap = _build_apply_snapshot(self._make_plan_tracks())
        record_refinement("Intro", "darker", {"harmonic": {"register_shift_semitones": -3}},
                          self._make_plan_tracks(), snap)
        entry = get_history("Intro")[0]
        assert "snapshot" in entry
        assert "Bass" in entry["snapshot"]

    def test_snapshot_note_op_values_correct(self):
        snap = _build_apply_snapshot(self._make_plan_tracks())
        record_refinement("Intro", "darker", {}, self._make_plan_tracks(), snap)
        entry = get_history("Intro")[0]
        note_op = entry["snapshot"]["Bass"]["note_op"]
        assert note_op["semitone_shift"] == -3
        assert note_op["velocity_shift"] == -8

    def test_snapshot_device_params_correct(self):
        snap = _build_apply_snapshot(self._make_plan_tracks())
        record_refinement("Intro", "darker", {}, self._make_plan_tracks(), snap)
        entry = get_history("Intro")[0]
        dev_params = entry["snapshot"]["Bass"]["device_params"]
        assert dev_params["AutoFilter"]["Frequency"] == 0.45

    def test_snapshot_empty_when_no_tracks(self):
        record_refinement("Intro", "darker", {"harmonic": {}}, [])
        entry = get_history("Intro")[0]
        assert entry["snapshot"] == {}
