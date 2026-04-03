"""Tests for MCP_Server/refinement/history.py — REFN-03 session log.

Covers:
- record_refinement / get_history round-trip
- clear_history (section and global)
- detect_conflicts: opposite signs in harmonic, timbral, dynamic fields
- detect_conflicts: mode_bias contradiction
- detect_conflicts: no conflict when same direction
- detect_conflicts: no conflict when history is empty
- detect_redundancies: same instruction detected, different instruction clear
- Integration: refine_section response includes conflicts/redundancies fields
"""

import json
import sys
import time
import types
from unittest.mock import MagicMock, patch

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
    _REFINEMENT_LOG,
    clear_history,
    detect_conflicts,
    detect_redundancies,
    get_history,
    record_refinement,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_log():
    """Clear the global log before every test to ensure isolation."""
    clear_history()
    yield
    clear_history()


def _darker_vector():
    return {
        "harmonic": {"register_shift_semitones": -3, "mode_bias": "minor", "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": -25.0, "brightness_db": -2.0, "reverb_wet_delta": 0.05},
        "dynamic": {"velocity_shift": -8, "compression_ratio_delta": 0.05},
    }


def _brighter_vector():
    return {
        "harmonic": {"register_shift_semitones": 3, "mode_bias": "major", "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": 25.0, "brightness_db": 2.0, "reverb_wet_delta": -0.05},
        "dynamic": {"velocity_shift": 5, "compression_ratio_delta": -0.03},
    }


def _neutral_vector():
    """Vector with no signed fields — no conflicts possible."""
    return {
        "harmonic": {"register_shift_semitones": 0, "density_delta": 0, "mode_bias": None},
    }


def _sample_tracks():
    return [{"track_name": "Drums"}, {"track_name": "Bass"}]


# ---------------------------------------------------------------------------
# record_refinement / get_history
# ---------------------------------------------------------------------------

class TestRecordAndGet:
    def test_history_empty_for_unknown_section(self):
        assert get_history("Intro") == []

    def test_record_adds_entry(self):
        record_refinement("Intro", "make it darker", _darker_vector(), _sample_tracks())
        history = get_history("Intro")
        assert len(history) == 1
        assert history[0]["instruction"] == "make it darker"
        assert history[0]["section"] == "Intro"

    def test_record_stores_vector(self):
        vec = _darker_vector()
        record_refinement("Intro", "darker", vec, _sample_tracks())
        assert get_history("Intro")[0]["vector"] == vec

    def test_record_stores_track_names(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        assert get_history("Intro")[0]["tracks"] == ["Drums", "Bass"]

    def test_record_stores_timestamp(self):
        before = time.time()
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        after = time.time()
        ts = get_history("Intro")[0]["timestamp"]
        assert before <= ts <= after

    def test_multiple_entries_same_section(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        record_refinement("Intro", "slower", {}, _sample_tracks())
        history = get_history("Intro")
        assert len(history) == 2
        assert history[1]["instruction"] == "slower"

    def test_separate_sections_independent(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        record_refinement("Outro", "brighter", _brighter_vector(), _sample_tracks())
        assert len(get_history("Intro")) == 1
        assert len(get_history("Outro")) == 1

    def test_section_name_case_insensitive(self):
        record_refinement("INTRO", "darker", _darker_vector(), _sample_tracks())
        assert len(get_history("intro")) == 1
        assert len(get_history("Intro")) == 1

    def test_get_history_none_returns_all(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        record_refinement("Outro", "brighter", _brighter_vector(), _sample_tracks())
        all_entries = get_history(None)
        assert len(all_entries) == 2


# ---------------------------------------------------------------------------
# clear_history
# ---------------------------------------------------------------------------

class TestClearHistory:
    def test_clear_specific_section(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        record_refinement("Outro", "brighter", _brighter_vector(), _sample_tracks())
        clear_history("Intro")
        assert get_history("Intro") == []
        assert len(get_history("Outro")) == 1

    def test_clear_all(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        record_refinement("Outro", "brighter", _brighter_vector(), _sample_tracks())
        clear_history()
        assert get_history(None) == []

    def test_clear_nonexistent_is_no_op(self):
        clear_history("Nonexistent")  # should not raise


# ---------------------------------------------------------------------------
# detect_conflicts
# ---------------------------------------------------------------------------

class TestDetectConflicts:
    def test_no_conflicts_when_history_empty(self):
        assert detect_conflicts("Intro", _darker_vector()) == []

    def test_no_conflicts_same_direction(self):
        # Apply "darker" twice — same direction, no conflict
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        assert detect_conflicts("Intro", _darker_vector()) == []

    def test_conflict_register_shift_opposite_signs(self):
        # darker sets register_shift=-3, brighter sets +3 → conflict
        record_refinement("Intro", "make it darker", _darker_vector(), _sample_tracks())
        conflicts = detect_conflicts("Intro", _brighter_vector())
        fields = [c["field"] for c in conflicts]
        assert "register_shift_semitones" in fields

    def test_conflict_mode_bias_contradiction(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())  # mode_bias=minor
        conflicts = detect_conflicts("Intro", _brighter_vector())  # mode_bias=major
        fields = [c["field"] for c in conflicts]
        assert "mode_bias" in fields

    def test_conflict_filter_cutoff_opposite(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())  # filter=-25
        conflicts = detect_conflicts("Intro", _brighter_vector())  # filter=+25
        fields = [c["field"] for c in conflicts]
        assert "filter_cutoff_delta_pct" in fields

    def test_conflict_velocity_shift_opposite(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())  # velocity=-8
        conflicts = detect_conflicts("Intro", _brighter_vector())  # velocity=+5
        fields = [c["field"] for c in conflicts]
        assert "velocity_shift" in fields

    def test_conflict_includes_previous_instruction(self):
        record_refinement("Intro", "make it darker", _darker_vector(), _sample_tracks())
        conflicts = detect_conflicts("Intro", _brighter_vector())
        assert all(c["previous_instruction"] == "make it darker" for c in conflicts)

    def test_conflict_includes_previous_and_new_values(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        conflicts = detect_conflicts("Intro", _brighter_vector())
        reg_conflict = next(c for c in conflicts if c["field"] == "register_shift_semitones")
        assert reg_conflict["previous_value"] == -3
        assert reg_conflict["new_value"] == 3

    def test_no_conflict_zero_fields_ignored(self):
        # density_delta=0 in both — should not be reported as conflict
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        conflicts = detect_conflicts("Intro", _brighter_vector())
        fields = [c["field"] for c in conflicts]
        assert "density_delta" not in fields

    def test_no_conflict_neutral_vector(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        assert detect_conflicts("Intro", _neutral_vector()) == []

    def test_conflict_across_multiple_history_entries(self):
        # First entry: darker (register=-3); second entry: warmer (register=-1)
        # New vector: brighter (register=+3) — conflicts with BOTH previous entries
        warmer_vec = {
            "harmonic": {"register_shift_semitones": -1, "mode_bias": None, "density_delta": 0},
        }
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        record_refinement("Intro", "warmer", warmer_vec, _sample_tracks())
        conflicts = detect_conflicts("Intro", _brighter_vector())
        reg_conflicts = [c for c in conflicts if c["field"] == "register_shift_semitones"]
        assert len(reg_conflicts) == 2

    def test_different_section_no_conflict(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        # Query conflicts for "Outro" — no history there
        assert detect_conflicts("Outro", _brighter_vector()) == []


# ---------------------------------------------------------------------------
# detect_redundancies
# ---------------------------------------------------------------------------

class TestDetectRedundancies:
    def test_no_redundancy_when_history_empty(self):
        assert detect_redundancies("Intro", "make it darker") == []

    def test_no_redundancy_different_instruction(self):
        record_refinement("Intro", "make it darker", _darker_vector(), _sample_tracks())
        assert detect_redundancies("Intro", "make it brighter") == []

    def test_redundancy_detected_same_instruction(self):
        record_refinement("Intro", "make it darker", _darker_vector(), _sample_tracks())
        redundancies = detect_redundancies("Intro", "make it darker")
        assert len(redundancies) == 1
        assert redundancies[0]["previous_instruction"] == "make it darker"

    def test_redundancy_case_insensitive(self):
        record_refinement("Intro", "Make It Darker", _darker_vector(), _sample_tracks())
        redundancies = detect_redundancies("Intro", "make it darker")
        assert len(redundancies) == 1

    def test_redundancy_whitespace_stripped(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        redundancies = detect_redundancies("Intro", "  darker  ")
        assert len(redundancies) == 1

    def test_redundancy_has_timestamp(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        redundancies = detect_redundancies("Intro", "darker")
        assert "timestamp" in redundancies[0]

    def test_redundancy_different_section_no_match(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        assert detect_redundancies("Outro", "darker") == []

    def test_multiple_redundancies_reported(self):
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        record_refinement("Intro", "darker", _darker_vector(), _sample_tracks())
        redundancies = detect_redundancies("Intro", "darker")
        assert len(redundancies) == 2


# ---------------------------------------------------------------------------
# Integration: refine_section response shape
# ---------------------------------------------------------------------------

class TestRefineSectionIntegration:
    """Verify refine_section includes conflicts/redundancies fields in its response."""

    def _make_conn(self, section_start=0.0, section_end=32.0):
        conn = MagicMock()
        def send_command(cmd, params=None):
            if cmd == "get_arrangement_state":
                return {
                    "tracks": [{"index": 0, "name": "Lead", "has_instrument": True}],
                    "cue_points": [{"name": "Intro", "time": section_start}],
                    "song_length": section_end,
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

    def test_response_has_conflicts_field(self):
        from MCP_Server.tools.refinement import refine_section
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            result = json.loads(refine_section(ctx, "Intro", "make it darker"))
        assert "conflicts" in result
        assert isinstance(result["conflicts"], list)

    def test_response_has_redundancies_field(self):
        from MCP_Server.tools.refinement import refine_section
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            result = json.loads(refine_section(ctx, "Intro", "make it darker"))
        assert "redundancies" in result
        assert isinstance(result["redundancies"], list)

    def test_no_conflicts_on_first_call(self):
        from MCP_Server.tools.refinement import refine_section
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            result = json.loads(refine_section(ctx, "Intro", "make it darker"))
        assert result["conflicts"] == []

    def test_redundancy_detected_on_second_identical_call(self):
        from MCP_Server.tools.refinement import refine_section
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            refine_section(ctx, "Intro", "make it darker")
            result = json.loads(refine_section(ctx, "Intro", "make it darker"))
        assert len(result["redundancies"]) >= 1

    def test_conflict_detected_when_opposite_instruction_follows(self):
        from MCP_Server.tools.refinement import refine_section
        ctx = MagicMock()
        conn = self._make_conn()
        with patch("MCP_Server.tools.refinement.get_ableton_connection", return_value=conn):
            refine_section(ctx, "Intro", "darker")
            result = json.loads(refine_section(ctx, "Intro", "brighter"))
        # Both "darker" and "brighter" produce conflicting vectors
        assert len(result["conflicts"]) > 0
