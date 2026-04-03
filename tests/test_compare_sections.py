"""Tests for compare_sections tool.

Covers:
- Two valid sections with overlapping tracks: per-track diffs
- Tracks only in one section appear in only_in_a / only_in_b
- Section A not found: error with section_a populated
- Section B not found: error with section_b populated
- Identical sections: diff with no changes
- Genre parameter passed through to get_section_state calls
"""

import json
import sys
import types
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Mock mcp module hierarchy so imports work without mcp installed
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

# ---------------------------------------------------------------------------
# Mock _Framework so AbletonMCP_Remote_Script handlers can be imported
# ---------------------------------------------------------------------------
_fw = types.ModuleType("_Framework")
_fw_cs = types.ModuleType("_Framework.ControlSurface")
_fw_cs.ControlSurface = type("ControlSurface", (), {"__init__": lambda self, *a, **kw: None})
_fw.ControlSurface = _fw_cs
sys.modules.setdefault("_Framework", _fw)
sys.modules.setdefault("_Framework.ControlSurface", _fw_cs)

import pytest  # noqa: E402

from MCP_Server.tools.refinement import compare_sections  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers: build canned SectionState JSON
# ---------------------------------------------------------------------------

_GET_SECTION_STATE_PATCH = "MCP_Server.tools.refinement.get_section_state"


def _section_state(section_name, start_bar, end_bar, tracks, error=None):
    """Build a SectionState dict and return its JSON string."""
    return json.dumps({
        "section": section_name,
        "start_bar": start_bar,
        "end_bar": end_bar,
        "tracks": tracks,
        "error": error,
    })


def _track_entry(name, index, role, clips, volume=0.8, pan=0.5, devices=None):
    """Build a TrackStateEntry dict."""
    return {
        "track_name": name,
        "track_index": index,
        "role": role,
        "clips": clips,
        "mix_context": {
            "volume": volume,
            "pan": pan,
            "devices": devices or [],
            "recipe_delta": [],
        },
    }


def _clip(name, start_bar, end_bar, is_audio=False, note_count=None,
          pitch_min=None, pitch_max=None, dominant_octave=None, rhythm_density=None):
    return {
        "name": name,
        "start_bar": start_bar,
        "end_bar": end_bar,
        "length_bars": end_bar - start_bar,
        "is_audio": is_audio,
        "note_count": note_count,
        "pitch_min": pitch_min,
        "pitch_max": pitch_max,
        "dominant_octave": dominant_octave,
        "rhythm_density": rhythm_density,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCompareSections:

    def test_overlapping_tracks_per_track_diffs(self):
        """Two valid sections with overlapping tracks returns per-track diffs."""
        verse_tracks = [
            _track_entry("Bass", 0, "bass", [
                _clip("Bass 1", 1, 5, note_count=16, pitch_min=36, pitch_max=48, rhythm_density=4.0),
            ], volume=0.75, pan=0.5, devices=[
                {"device_name": "Compressor", "class_name": "Compressor2", "prominent_params": {}},
            ]),
            _track_entry("Pad", 1, "pad", [
                _clip("Pad 1", 1, 5, note_count=8, pitch_min=60, pitch_max=72, rhythm_density=2.0),
            ], volume=0.6, pan=0.4, devices=[
                {"device_name": "Auto Filter", "class_name": "AutoFilter", "prominent_params": {}},
            ]),
        ]
        chorus_tracks = [
            _track_entry("Bass", 0, "bass", [
                _clip("Bass 2", 5, 9, note_count=24, pitch_min=36, pitch_max=52, rhythm_density=6.0),
                _clip("Bass 2b", 9, 13, note_count=20, pitch_min=38, pitch_max=50, rhythm_density=5.0),
            ], volume=0.85, pan=0.5, devices=[
                {"device_name": "Compressor", "class_name": "Compressor2", "prominent_params": {}},
                {"device_name": "Saturator", "class_name": "Saturator", "prominent_params": {}},
            ]),
            _track_entry("Pad", 1, "pad", [
                _clip("Pad 2", 5, 9, note_count=12, pitch_min=60, pitch_max=84, rhythm_density=3.0),
            ], volume=0.7, pan=0.6, devices=[
                {"device_name": "Auto Filter", "class_name": "AutoFilter", "prominent_params": {}},
            ]),
        ]

        verse_json = _section_state("Verse", 1, 5, verse_tracks)
        chorus_json = _section_state("Chorus", 5, 13, chorus_tracks)

        def mock_get(ctx, section_name, genre=None):
            if section_name == "Verse":
                return verse_json
            return chorus_json

        with patch(_GET_SECTION_STATE_PATCH, side_effect=mock_get):
            result_str = compare_sections(None, "Verse", "Chorus")

        result = json.loads(result_str)
        assert result["error"] is None
        assert result["section_a"] == "Verse"
        assert result["section_b"] == "Chorus"
        assert result["only_in_a"] == []
        assert result["only_in_b"] == []

        # Find Bass track diff
        bass_diff = next(d for d in result["track_diffs"] if d["track_name"] == "Bass")
        assert bass_diff["clips"]["a"] == 1
        assert bass_diff["clips"]["b"] == 2
        assert bass_diff["total_notes"]["a"] == 16
        assert bass_diff["total_notes"]["b"] == 44  # 24 + 20
        assert bass_diff["mix"]["volume"]["a"] == 0.75
        assert bass_diff["mix"]["volume"]["b"] == 0.85
        # Devices: Compressor2 in both, Saturator only in b
        assert "Compressor2" in bass_diff["devices_both"]
        assert "Saturator" in bass_diff["devices_b_only"]

        # Find Pad track diff
        pad_diff = next(d for d in result["track_diffs"] if d["track_name"] == "Pad")
        assert pad_diff["pitch_range"]["a"]["min"] == 60
        assert pad_diff["pitch_range"]["b"]["max"] == 84

    def test_tracks_only_in_one_section(self):
        """Track present in A but not B appears in only_in_a, and vice versa."""
        verse_tracks = [
            _track_entry("Bass", 0, "bass", [_clip("B1", 1, 5, note_count=8, pitch_min=36, pitch_max=48)]),
            _track_entry("Vocal", 2, None, [_clip("V1", 1, 5, is_audio=True)]),
        ]
        chorus_tracks = [
            _track_entry("Bass", 0, "bass", [_clip("B2", 5, 9, note_count=12, pitch_min=36, pitch_max=48)]),
            _track_entry("Lead", 3, "lead", [_clip("L1", 5, 9, note_count=16, pitch_min=72, pitch_max=84)]),
        ]

        verse_json = _section_state("Verse", 1, 5, verse_tracks)
        chorus_json = _section_state("Chorus", 5, 9, chorus_tracks)

        def mock_get(ctx, section_name, genre=None):
            if section_name == "Verse":
                return verse_json
            return chorus_json

        with patch(_GET_SECTION_STATE_PATCH, side_effect=mock_get):
            result_str = compare_sections(None, "Verse", "Chorus")

        result = json.loads(result_str)
        assert "Vocal" in result["only_in_a"]
        assert "Lead" in result["only_in_b"]
        # Bass should be in track_diffs, not in only_in lists
        track_diff_names = [d["track_name"] for d in result["track_diffs"]]
        assert "Bass" in track_diff_names
        assert "Vocal" not in track_diff_names
        assert "Lead" not in track_diff_names

    def test_section_a_not_found(self):
        """Section A not found returns error with section_a populated, no diff."""
        error_json = _section_state("Missing", 0, 0, [], error="Section 'Missing' not found in arrangement")
        chorus_json = _section_state("Chorus", 5, 9, [])

        def mock_get(ctx, section_name, genre=None):
            if section_name == "Missing":
                return error_json
            return chorus_json

        with patch(_GET_SECTION_STATE_PATCH, side_effect=mock_get):
            result_str = compare_sections(None, "Missing", "Chorus")

        result = json.loads(result_str)
        assert result["error"] is not None
        assert "Missing" in result["error"]
        assert result["section_a"] == "Missing"
        assert result["diff"] is None

    def test_section_b_not_found(self):
        """Section B not found returns error with section_b populated, no diff."""
        verse_json = _section_state("Verse", 1, 5, [])
        error_json = _section_state("Missing", 0, 0, [], error="Section 'Missing' not found in arrangement")

        def mock_get(ctx, section_name, genre=None):
            if section_name == "Missing":
                return error_json
            return verse_json

        with patch(_GET_SECTION_STATE_PATCH, side_effect=mock_get):
            result_str = compare_sections(None, "Verse", "Missing")

        result = json.loads(result_str)
        assert result["error"] is not None
        assert "Missing" in result["error"]
        assert result["section_b"] == "Missing"
        assert result["diff"] is None

    def test_identical_sections(self):
        """Both sections identical returns diff with all track diffs showing no changes."""
        tracks = [
            _track_entry("Bass", 0, "bass", [
                _clip("B1", 1, 5, note_count=16, pitch_min=36, pitch_max=48, rhythm_density=4.0),
            ], volume=0.8, pan=0.5, devices=[
                {"device_name": "Compressor", "class_name": "Compressor2", "prominent_params": {}},
            ]),
        ]
        state_a = _section_state("Verse1", 1, 5, tracks)
        state_b = _section_state("Verse2", 5, 9, tracks)

        def mock_get(ctx, section_name, genre=None):
            if section_name == "Verse1":
                return state_a
            return state_b

        with patch(_GET_SECTION_STATE_PATCH, side_effect=mock_get):
            result_str = compare_sections(None, "Verse1", "Verse2")

        result = json.loads(result_str)
        assert result["error"] is None
        assert result["only_in_a"] == []
        assert result["only_in_b"] == []
        assert len(result["track_diffs"]) == 1
        bass = result["track_diffs"][0]
        assert bass["clips"]["a"] == bass["clips"]["b"]
        assert bass["total_notes"]["a"] == bass["total_notes"]["b"]
        assert bass["mix"]["volume"]["a"] == bass["mix"]["volume"]["b"]
        assert bass["devices_a_only"] == []
        assert bass["devices_b_only"] == []

    def test_genre_passed_through(self):
        """Genre parameter passed through to get_section_state calls."""
        state = _section_state("Verse", 1, 5, [])

        calls_made = []

        def mock_get(ctx, section_name, genre=None):
            calls_made.append({"section": section_name, "genre": genre})
            return state

        with patch(_GET_SECTION_STATE_PATCH, side_effect=mock_get):
            compare_sections(None, "Verse", "Chorus", genre="techno")

        assert len(calls_made) == 2
        assert calls_made[0]["genre"] == "techno"
        assert calls_made[1]["genre"] == "techno"
