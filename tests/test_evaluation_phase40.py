"""Tests for Phase 40 evaluators: arrangement, sound selection, and harmonic coherence.

Covers:
- evaluate_arrangement(conn) -> DimensionScore
- evaluate_sounds_coverage(conn) -> DimensionScore
- evaluate_harmonic(conn) -> DimensionScore

All three evaluators take only `conn` as parameter (no genre needed).
Uses mock conn pattern from test_evaluation_schema.py.
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

import pytest  # noqa: E402

from MCP_Server.evaluation.arrangement import evaluate_arrangement  # noqa: E402
from MCP_Server.evaluation.sounds_coverage import evaluate_sounds_coverage  # noqa: E402
from MCP_Server.evaluation.harmonic import evaluate_harmonic  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn(**responses):
    """Build a mock conn whose send_command dispatches by cmd key."""
    mock_conn = MagicMock()

    def send_command(cmd, args=None):
        return responses.get(cmd, {})

    mock_conn.send_command.side_effect = send_command
    return mock_conn


def _make_conn_fn(fn):
    """Build a mock conn whose send_command calls fn(cmd, args)."""
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = fn
    return mock_conn


# ---------------------------------------------------------------------------
# class TestArrangementEvaluator
# ---------------------------------------------------------------------------

class TestArrangementEvaluator:
    """Tests for evaluate_arrangement(conn) -> DimensionScore."""

    def _make_arrangement_conn(self, tracks, clips_by_index=None):
        """Build conn for arrangement tests.

        Args:
            tracks: list of {name, has_devices} dicts for get_arrangement_state
            clips_by_index: dict mapping track_index -> list of clip dicts
        """
        clips_by_index = clips_by_index or {}

        def send_command(cmd, args=None):
            if args is None:
                args = {}
            if cmd == "get_arrangement_state":
                return {"tracks": tracks, "cue_points": [], "song_length": 32.0}
            if cmd == "get_arrangement_clips":
                idx = args.get("track_index", 0)
                clips = clips_by_index.get(idx, [])
                track_name = tracks[idx]["name"] if idx < len(tracks) else "unknown"
                return {"track_name": track_name, "clips": clips}
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = send_command
        return mock_conn

    def test_returns_dimension_arrangement(self):
        """evaluate_arrangement returns dict with dimension == 'arrangement'."""
        tracks = [{"name": "KICK_01", "has_devices": True}]
        clips_by_index = {0: [{"name": "clip1", "start_time": 0.0, "end_time": 4.0}]}
        conn = self._make_arrangement_conn(tracks, clips_by_index)
        result = evaluate_arrangement(conn)
        assert result["dimension"] == "arrangement"

    def test_all_tracks_clean_scores_ten(self):
        """Two tracks, both has_devices=True and have clips -> score == 10.0, no issues."""
        tracks = [
            {"name": "KICK_01", "has_devices": True},
            {"name": "BASS_01", "has_devices": True},
        ]
        clips_by_index = {
            0: [{"name": "kick_clip", "start_time": 0.0, "end_time": 4.0}],
            1: [{"name": "bass_clip", "start_time": 0.0, "end_time": 4.0}],
        }
        conn = self._make_arrangement_conn(tracks, clips_by_index)
        result = evaluate_arrangement(conn)
        assert result["score"] == 10.0
        assert result["issues"] == []

    def test_all_tracks_empty_scores_zero(self):
        """Two tracks, both has_devices=False -> score == 0.0, 2 critical issues."""
        tracks = [
            {"name": "KICK_01", "has_devices": False},
            {"name": "BASS_01", "has_devices": False},
        ]
        conn = self._make_arrangement_conn(tracks, {})
        result = evaluate_arrangement(conn)
        assert result["score"] == 0.0
        critical = [i for i in result["issues"] if i["severity"] == "critical"]
        assert len(critical) == 2

    def test_no_devices_is_critical(self):
        """Track with has_devices=False generates at least one issue with severity 'critical'."""
        tracks = [{"name": "KICK_01", "has_devices": False}]
        conn = self._make_arrangement_conn(tracks, {})
        result = evaluate_arrangement(conn)
        critical = [i for i in result["issues"] if i["severity"] == "critical"]
        assert len(critical) >= 1

    def test_has_devices_no_clips_is_warning(self):
        """Track with has_devices=True but empty clips list -> at least one warning issue."""
        tracks = [{"name": "PAD_01", "has_devices": True}]
        clips_by_index = {0: []}  # empty clips
        conn = self._make_arrangement_conn(tracks, clips_by_index)
        result = evaluate_arrangement(conn)
        warnings = [i for i in result["issues"] if i["severity"] == "warning"]
        assert len(warnings) >= 1


# ---------------------------------------------------------------------------
# class TestSoundsCoverageEvaluator
# ---------------------------------------------------------------------------

class TestSoundsCoverageEvaluator:
    """Tests for evaluate_sounds_coverage(conn) -> DimensionScore."""

    def _make_sounds_conn(self, tracks):
        """Build conn for sounds coverage tests."""
        def send_command(cmd, args=None):
            if cmd == "get_mix_state":
                return {"tracks": tracks, "return_tracks": [], "master_track": None}
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = send_command
        return mock_conn

    def test_returns_dimension_sounds(self):
        """evaluate_sounds_coverage returns dict with dimension == 'sounds'."""
        conn = self._make_sounds_conn(tracks=[])
        result = evaluate_sounds_coverage(conn)
        assert result["dimension"] == "sounds"

    def test_correct_instrument_no_issue(self):
        """KICK_01 track with 'Drum Rack' device -> no issues (Drum Rack is best for kick)."""
        tracks = [
            {
                "name": "KICK_01",
                "devices": [
                    {"class_name": "DrumGroupDevice", "device_name": "Drum Rack"},
                ],
            }
        ]
        conn = self._make_sounds_conn(tracks)
        result = evaluate_sounds_coverage(conn)
        assert len(result["issues"]) == 0

    def test_wrong_instrument_creates_warning(self):
        """PAD_01 track with 'Drum Rack' device -> warning (Wavetable expected for pad)."""
        tracks = [
            {
                "name": "PAD_01",
                "devices": [
                    {"class_name": "DrumGroupDevice", "device_name": "Drum Rack"},
                ],
            }
        ]
        conn = self._make_sounds_conn(tracks)
        result = evaluate_sounds_coverage(conn)
        warnings = [i for i in result["issues"] if i["severity"] == "warning"]
        assert len(warnings) >= 1

    def test_unknown_role_track_skipped(self):
        """Track with name 'ambient_fx_01' where role inference fails -> no issues."""
        tracks = [
            {
                "name": "ambient_fx_01",
                "devices": [
                    {"class_name": "DrumGroupDevice", "device_name": "Drum Rack"},
                ],
            }
        ]
        conn = self._make_sounds_conn(tracks)
        result = evaluate_sounds_coverage(conn)
        assert result["issues"] == []


# ---------------------------------------------------------------------------
# class TestHarmonicEvaluator
# ---------------------------------------------------------------------------

class TestHarmonicEvaluator:
    """Tests for evaluate_harmonic(conn) -> DimensionScore."""

    def _make_harmonic_conn(self, scale_info, session_state=None, notes_by_track_clip=None):
        """Build conn for harmonic tests.

        Args:
            scale_info: dict returned by get_scale_info
            session_state: dict returned by get_session_state
            notes_by_track_clip: dict mapping (track_index, clip_index) -> list of note dicts
        """
        session_state = session_state or {"tracks": []}
        notes_by_track_clip = notes_by_track_clip or {}

        def send_command(cmd, args=None):
            if args is None:
                args = {}
            if cmd == "get_scale_info":
                return scale_info
            if cmd == "get_session_state":
                return session_state
            if cmd == "get_notes":
                key = (args.get("track_index", 0), args.get("clip_index", 0))
                notes = notes_by_track_clip.get(key, [])
                return {"notes": notes}
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = send_command
        return mock_conn

    def test_returns_dimension_harmony(self):
        """evaluate_harmonic returns dict with dimension == 'harmony'."""
        scale_info = {"root_note": 0, "scale_name": "", "scale_intervals": [], "scale_mode": 0}
        conn = self._make_harmonic_conn(scale_info)
        result = evaluate_harmonic(conn)
        assert result["dimension"] == "harmony"

    def test_no_scale_set_returns_ten_with_info(self):
        """Empty scale_name -> score == 10.0, at least one info severity issue."""
        scale_info = {"root_note": 0, "scale_name": "", "scale_intervals": [], "scale_mode": 0}
        conn = self._make_harmonic_conn(scale_info)
        result = evaluate_harmonic(conn)
        assert result["score"] == 10.0
        info_issues = [i for i in result["issues"] if i["severity"] == "info"]
        assert len(info_issues) >= 1

    def test_all_notes_in_key_scores_ten(self):
        """C major scale, all notes are in key (C/D/E/F/G/A/B) -> score == 10.0.

        C major: root=0, intervals=[2,2,1,2,2,2,1]
        Pitch classes: {0(C), 2(D), 4(E), 5(F), 7(G), 9(A), 11(B)}
        """
        scale_info = {
            "root_note": 0,
            "scale_name": "major",
            "scale_intervals": [2, 2, 1, 2, 2, 2, 1],
            "scale_mode": 0,
        }
        # C major pitch classes: 0, 2, 4, 5, 7, 9, 11
        session_state = {
            "tracks": [
                {"name": "LEAD_01", "index": 0, "type": "midi",
                 "clips": [{"scene_index": 0, "name": "melody"}]},
            ]
        }
        notes_by_track_clip = {
            (0, 0): [
                {"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100},  # C4
                {"pitch": 62, "start_time": 0.5, "duration": 0.5, "velocity": 100},  # D4
                {"pitch": 64, "start_time": 1.0, "duration": 0.5, "velocity": 100},  # E4
                {"pitch": 65, "start_time": 1.5, "duration": 0.5, "velocity": 100},  # F4
                {"pitch": 67, "start_time": 2.0, "duration": 0.5, "velocity": 100},  # G4
            ]
        }
        conn = self._make_harmonic_conn(scale_info, session_state, notes_by_track_clip)
        result = evaluate_harmonic(conn)
        assert result["score"] == 10.0

    def test_out_of_key_note_creates_warning(self):
        """C major scale, one C# note (pitch=1 mod 12, out of key) -> score < 10.0, warning."""
        scale_info = {
            "root_note": 0,
            "scale_name": "major",
            "scale_intervals": [2, 2, 1, 2, 2, 2, 1],
            "scale_mode": 0,
        }
        session_state = {
            "tracks": [
                {"name": "LEAD_01", "index": 0, "type": "midi",
                 "clips": [{"scene_index": 0, "name": "melody"}]},
            ]
        }
        notes_by_track_clip = {
            (0, 0): [
                {"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100},  # C4 - in key
                {"pitch": 61, "start_time": 0.5, "duration": 0.5, "velocity": 100},  # C#4 - OUT of key
            ]
        }
        conn = self._make_harmonic_conn(scale_info, session_state, notes_by_track_clip)
        result = evaluate_harmonic(conn)
        assert result["score"] < 10.0
        warnings = [i for i in result["issues"] if i["severity"] == "warning"]
        assert len(warnings) >= 1

    def test_no_clips_scores_ten(self):
        """Session with tracks but no clips -> score == 10.0 (no notes to check)."""
        scale_info = {
            "root_note": 0,
            "scale_name": "major",
            "scale_intervals": [2, 2, 1, 2, 2, 2, 1],
            "scale_mode": 0,
        }
        session_state = {
            "tracks": [
                {"name": "LEAD_01", "index": 0, "type": "midi", "clips": []},
            ]
        }
        conn = self._make_harmonic_conn(scale_info, session_state)
        result = evaluate_harmonic(conn)
        assert result["score"] == 10.0
