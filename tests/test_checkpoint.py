"""Tests for MCP_Server/orchestration/checkpoint.py.

Covers all 7 CHKP-01/CHKP-02 success criteria:
1. Empty session: completed_phases=[], active_phase="setup", resume_hint mentions "empty"
2. Setup complete + drums active (2 tracks, no drum clips)
3. Drums complete (drum track with clips)
4. No genre: active_phase=None, session_stats populated
5. Master complete (GlueCompressor + Limiter2 on master)
6. Resume hint is a single sentence (no newlines, len > 10)
7. Session stats correctly populated
"""

import json
import sys
import types
from unittest.mock import MagicMock, patch

# --- Mock mcp module hierarchy ---
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

import pytest  # noqa: E402
from MCP_Server.orchestration.checkpoint import get_checkpoint  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

EMPTY_ARRANGEMENT = {"tracks": [], "cue_points": [], "song_length": 0}
EMPTY_DEVICE_CLASSES = {"tracks": [], "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}


def _make_track(name, has_instrument=True, index=0, device_classes=None, has_clips=False):
    return {"name": name, "has_instrument": has_instrument, "index": index,
            "device_classes": device_classes or [], "has_clips": has_clips}


def _make_conn(arrangement_state, device_classes_state, clips_by_track=None):
    """Build a mock connection that returns fixture data."""
    clips_by_track = clips_by_track or {}
    # Inject real clip lists into each track (simulates get_arrangement_state RS output)
    for t in arrangement_state.get("tracks", []):
        t_clips = clips_by_track.get(t["name"], t.get("clips", []))
        t["clips"] = t_clips
        t["clip_count"] = len(t_clips)
        t["has_clips"] = len(t_clips) > 0
    mock_conn = MagicMock()

    def send_command(cmd, params=None):
        if cmd == "get_arrangement_state":
            return arrangement_state
        elif cmd == "get_device_classes":
            return device_classes_state
        return {}

    mock_conn.send_command.side_effect = send_command
    return mock_conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCheckpoint:
    def setup_method(self):
        """Clear checkpoint cache before each test to avoid cross-test leakage."""
        from MCP_Server.orchestration.checkpoint import _checkpoint_cache
        _checkpoint_cache.clear()

    def test_empty_session(self):
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(EMPTY_ARRANGEMENT, EMPTY_DEVICE_CLASSES)):
            result = get_checkpoint("house")
        assert result["completed_phases"] == []
        assert result["active_phase"] == "setup"
        assert result["active_phase_progress"] == 0.0
        assert "empty" in result["resume_hint"].lower()

    def test_setup_complete_drums_active(self):
        arr = {
            "tracks": [
                _make_track("Kick", True, 0),
                _make_track("Bass", True, 1),
            ],
            "cue_points": [{"name": "Intro", "time": 0.0}],
            "song_length": 32.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Kick", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        # Kick has no clips → drums not complete
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc, clips_by_track={})):
            result = get_checkpoint("house")
        assert "setup" in result["completed_phases"]
        assert result["active_phase"] == "drums"

    def test_drums_complete(self):
        arr = {
            "tracks": [_make_track("Kick Drums", True, 0, has_clips=True), _make_track("Bass", True, 1)],
            "cue_points": [{"name": "Intro", "time": 0.0}],
            "song_length": 32.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Kick Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        clips = {"Kick Drums": [{"start_time": 0.0, "end_time": 8.0}]}
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc, clips)):
            result = get_checkpoint("house")
        assert "drums" in result["completed_phases"]

    def test_no_genre_returns_none_active_phase(self):
        arr = {
            "tracks": [_make_track("Track1", True, 0)],
            "cue_points": [],
            "song_length": 16.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Track1", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc)):
            result = get_checkpoint(None)
        assert result["active_phase"] is None
        assert result["session_stats"]["track_count"] == 1

    def test_master_complete(self):
        arr = {
            "tracks": [
                _make_track("Kick", True, 0, device_classes=["Compressor2"], has_clips=True),
                _make_track("Bass", True, 1, has_clips=True),
            ],
            "cue_points": [{"name": "Intro", "time": 0.0}],
            "song_length": 32.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Kick", "device_classes": ["Compressor2"]},
                         {"index": 1, "name": "Bass", "device_classes": []}],
              "return_tracks": [],
              "master_track": {"name": "Master", "device_classes": ["GlueCompressor", "Limiter2"]}}
        clips = {
            "Kick": [{"start_time": 0.0, "end_time": 8.0}],
            "Bass": [{"start_time": 0.0, "end_time": 8.0}],
        }
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc, clips)):
            result = get_checkpoint("techno")
        assert "master" in result["completed_phases"]

    def test_master_shortcircuit_requires_production_work(self):
        """Master bus template (GlueCompressor + Limiter2) with no real tracks
        should NOT short-circuit to all-phases-complete."""
        arr = {
            "tracks": [_make_track("Master Template", False, 0)],
            "cue_points": [],
            "song_length": 0,
        }
        dc = {"tracks": [{"index": 0, "name": "Master Template", "device_classes": []}],
              "return_tracks": [],
              "master_track": {"name": "Master", "device_classes": ["GlueCompressor", "Limiter2"]}}
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc)):
            result = get_checkpoint("house")
        # Should NOT report all phases complete
        from MCP_Server.orchestration.agenda import AGENDA_CATALOG
        all_phases = list(AGENDA_CATALOG.get("house", []))
        assert result["completed_phases"] != all_phases
        # With only 1 track, setup is incomplete so active_phase should be "setup"
        assert result["active_phase"] == "setup"

    def test_resume_hint_is_single_sentence(self):
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(EMPTY_ARRANGEMENT, EMPTY_DEVICE_CLASSES)):
            result = get_checkpoint("house")
        hint = result["resume_hint"]
        assert "\n" not in hint
        assert len(hint) > 10

    def test_session_stats_populated(self):
        arr = {
            "tracks": [
                _make_track("Drums", True, 0),
                _make_track("Bass", False, 1),
            ],
            "cue_points": [],
            "song_length": 16.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc)):
            result = get_checkpoint("house")
        assert result["session_stats"]["track_count"] == 2
        assert result["session_stats"]["tracks_with_instruments"] == 1

    def test_arrangement_single_clip_not_complete(self):
        """Arrangement phase is NOT complete when each track has only one clip.

        A single intro clip (even if every instrument track has one) must not
        satisfy the arrangement phase — clips must span all defined sections.
        """
        # techno: setup→drums→bass→sound_design→arrangement→mix→master
        arr = {
            "tracks": [
                _make_track("Kick Drums", True, 0),
                _make_track("Bass", True, 1),
                _make_track("Synth", True, 2, device_classes=["AutoFilter"]),
            ],
            "cue_points": [{"name": "Intro", "time": 0.0}, {"name": "Drop", "time": 32.0}],
            "song_length": 64.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Kick Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []},
                         {"index": 2, "name": "Synth", "device_classes": ["AutoFilter"]}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        # One clip per track — fewer than the 2 defined sections
        single_clips = {t: [{"start_time": 0.0, "length": 8.0}]
                        for t in ("Kick Drums", "Bass", "Synth")}
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc, single_clips)):
            result = get_checkpoint("techno")
        assert "arrangement" not in result["completed_phases"]

    def test_arrangement_multi_section_clips_complete(self):
        """Arrangement phase IS complete when each track has one clip per section."""
        arr = {
            "tracks": [
                _make_track("Kick Drums", True, 0),
                _make_track("Bass", True, 1),
                _make_track("Synth", True, 2, device_classes=["AutoFilter"]),
            ],
            "cue_points": [{"name": "Intro", "time": 0.0}, {"name": "Drop", "time": 32.0}],
            "song_length": 64.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Kick Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []},
                         {"index": 2, "name": "Synth", "device_classes": ["AutoFilter"]}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        # Two clips per track — one per defined section
        multi_clips = {
            t: [{"start_time": 0.0, "length": 8.0}, {"start_time": 32.0, "length": 8.0}]
            for t in ("Kick Drums", "Bass", "Synth")
        }
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc, multi_clips)):
            result = get_checkpoint("techno")
        assert "arrangement" in result["completed_phases"]

    def test_no_per_track_clip_queries(self):
        """Checkpoint must not issue per-track get_arrangement_clips calls."""
        arr = {
            "tracks": [
                _make_track("Drums", True, 0, has_clips=True),
                _make_track("Bass", True, 1, has_clips=True),
                _make_track("Chords", True, 2, has_clips=False),
            ],
            "cue_points": [], "song_length": 32.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []},
                         {"index": 2, "name": "Chords", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        mock = _make_conn(arr, dc)
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=mock):
            get_checkpoint("house")
        commands = [call.args[0] for call in mock.send_command.call_args_list]
        assert "get_arrangement_clips" not in commands
        assert commands == ["get_arrangement_state", "get_device_classes"]


class TestCheckpointCache:
    def setup_method(self):
        """Clear cache before each test."""
        from MCP_Server.orchestration.checkpoint import _checkpoint_cache
        _checkpoint_cache.clear()

    def test_second_call_uses_cache(self):
        """Second get_checkpoint call within TTL should not call send_command again."""
        arr = {
            "tracks": [
                _make_track("Drums", True, 0, has_clips=True),
                _make_track("Bass", True, 1),
            ],
            "cue_points": [], "song_length": 32.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        mock = _make_conn(arr, dc)
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=mock):
            result1 = get_checkpoint("house")
            count_after_first = mock.send_command.call_count
            result2 = get_checkpoint("house")
            count_after_second = mock.send_command.call_count
        # Second call should add zero send_command calls
        assert count_after_second == count_after_first
        assert result1 == result2

    def test_different_genre_not_cached(self):
        """Different genre keys should get independent cache entries."""
        arr = {
            "tracks": [
                _make_track("Drums", True, 0, has_clips=True),
                _make_track("Bass", True, 1),
            ],
            "cue_points": [], "song_length": 32.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        mock = _make_conn(arr, dc)
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=mock):
            get_checkpoint("house")
            count_after_first = mock.send_command.call_count
            get_checkpoint("techno")
            count_after_second = mock.send_command.call_count
        # Second call with different genre should make additional send_command calls
        assert count_after_second > count_after_first

    def test_invalidate_forces_refresh(self):
        """invalidate_checkpoint_cache should force a fresh query."""
        from MCP_Server.orchestration.checkpoint import invalidate_checkpoint_cache
        arr = {
            "tracks": [
                _make_track("Drums", True, 0, has_clips=True),
                _make_track("Bass", True, 1),
            ],
            "cue_points": [], "song_length": 32.0,
        }
        dc = {"tracks": [{"index": 0, "name": "Drums", "device_classes": []},
                         {"index": 1, "name": "Bass", "device_classes": []}],
              "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
        mock = _make_conn(arr, dc)
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=mock):
            get_checkpoint("house")
            count_after_first = mock.send_command.call_count
            invalidate_checkpoint_cache("house")
            get_checkpoint("house")
            count_after_second = mock.send_command.call_count
        # After invalidation, should make fresh calls
        assert count_after_second > count_after_first

    def test_error_not_cached(self):
        """Connection errors should not be cached."""
        from MCP_Server.orchestration.checkpoint import _checkpoint_cache
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   side_effect=Exception("connection refused")):
            result = get_checkpoint("house")
        assert "error" in result
        assert "house" not in _checkpoint_cache


class TestNonCanonicalTrackNames:
    """Test phase detection with non-standard track names commonly used in real Ableton sessions."""

    def setup_method(self):
        from MCP_Server.orchestration.checkpoint import _checkpoint_cache
        _checkpoint_cache.clear()

    def _check_phase(self, track_name, expected_phase, has_instrument=True):
        """Helper: create a session with one named track (with clips) and verify expected phase is detected."""
        arr = {
            "tracks": [
                _make_track(track_name, has_instrument, 0, has_clips=True),
                _make_track("Pad", True, 1),  # second track so setup is complete
            ],
            "cue_points": [{"name": "Intro", "time": 0.0}],
            "song_length": 32.0,
        }
        dc = {
            "tracks": [
                {"index": 0, "name": track_name, "device_classes": []},
                {"index": 1, "name": "Pad", "device_classes": []},
            ],
            "return_tracks": [],
            "master_track": {"name": "Master", "device_classes": []},
        }
        clips = {track_name: [{"start_time": 0.0, "end_time": 8.0}]}
        with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
                   return_value=_make_conn(arr, dc, clips)):
            result = get_checkpoint("house")
        return result

    # --- Drum name variants ---

    def test_808_kit_detected_as_drums(self):
        result = self._check_phase("808 Kit", "drums")
        assert "drums" in result["completed_phases"]

    def test_hi_hat_detected_as_drums(self):
        result = self._check_phase("Hi Hat", "drums")
        assert "drums" in result["completed_phases"]

    def test_tom_fill_detected_as_drums(self):
        result = self._check_phase("Tom Fill", "drums")
        assert "drums" in result["completed_phases"]

    def test_clap_detected_as_drums(self):
        result = self._check_phase("Clap", "drums")
        assert "drums" in result["completed_phases"]

    # --- Bass name variants ---

    def test_sub_bass_detected_as_bass(self):
        result = self._check_phase("Sub Bass", "bass")
        assert "bass" in result["completed_phases"]

    # --- Harmony name variants ---

    def test_keys_detected_as_harmony(self):
        result = self._check_phase("Keys", "harmony")
        assert "harmony" in result["completed_phases"]

    def test_rhodes_chords_detected_as_harmony(self):
        result = self._check_phase("Rhodes Chords", "harmony")
        assert "harmony" in result["completed_phases"]

    # --- Melody name variants ---

    def test_lead_synth_detected_as_melody(self):
        result = self._check_phase("Lead Synth", "melody")
        assert "melody" in result["completed_phases"]

    def test_arp_sequence_detected_as_melody(self):
        result = self._check_phase("Arp Sequence", "melody")
        assert "melody" in result["completed_phases"]

    # --- Negative case ---

    def test_fx_riser_not_detected_as_instrument(self):
        """FX Riser should NOT match any instrument name set (sound_design uses device classes)."""
        from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES
        from MCP_Server.orchestration.checkpoint import _has_name_match
        assert not _has_name_match("FX Riser", _DRUM_NAMES)
        assert not _has_name_match("FX Riser", _BASS_NAMES)
        assert not _has_name_match("FX Riser", _HARMONY_NAMES)
        assert not _has_name_match("FX Riser", _MELODY_NAMES)

    # --- Regression guard: canonical names still work ---

    def test_canonical_names_still_match(self):
        """Existing canonical names must not regress."""
        from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES
        from MCP_Server.orchestration.checkpoint import _has_name_match
        assert _has_name_match("Drums", _DRUM_NAMES)
        assert _has_name_match("Bass", _BASS_NAMES)
        assert _has_name_match("Chords", _HARMONY_NAMES)
        assert _has_name_match("Lead", _MELODY_NAMES)
