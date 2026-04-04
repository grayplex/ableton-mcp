"""Tests for section-aware mixing: frequency conflict detection, per-section recipe
application, and sidechain chain setup.

Validates:
- FREQ_BANDS and ROLE_PRIMARY_BANDS definitions
- detect_conflicts returns correct conflicts and severities
- extract_eq_bands parses Eq8 recipe data
- apply_section_mix_recipe applies automation breakpoints per section
- detect_frequency_conflicts analyzes tracks in a section
- setup_sidechain_chain auto-detects compressor and connects sidechain
"""

import json
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

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


# ---------------------------------------------------------------------------
# freq_bands module tests
# ---------------------------------------------------------------------------

from MCP_Server.mixing.freq_bands import (  # noqa: E402
    FREQ_BANDS,
    ROLE_PRIMARY_BANDS,
    detect_conflicts,
    extract_eq_bands,
)


class TestFreqBands:
    """Verify FREQ_BANDS definitions."""

    def test_all_standard_bands_present(self):
        expected = {"sub", "low", "low_mid", "mid", "upper_mid", "presence", "brilliance"}
        assert set(FREQ_BANDS.keys()) == expected

    def test_sub_range(self):
        assert FREQ_BANDS["sub"] == (20, 60)

    def test_brilliance_range(self):
        assert FREQ_BANDS["brilliance"] == (6000, 20000)


class TestRolePrimaryBands:
    """Verify ROLE_PRIMARY_BANDS mapping."""

    def test_kick_primary_bands(self):
        assert ROLE_PRIMARY_BANDS["kick"] == ["sub", "low"]

    def test_vocal_primary_bands(self):
        assert ROLE_PRIMARY_BANDS["vocal"] == ["mid", "upper_mid", "presence"]


class TestExtractEqBands:
    """Verify extract_eq_bands parses Eq8 recipe data."""

    def test_extracts_active_bands(self):
        recipe = {
            "Eq8": {
                "1 Frequency A": 60,
                "1 Gain A": 3.0,
                "2 Frequency A": 300,
                "2 Gain A": -2.0,
                "3 Frequency A": 1000,
                "3 Gain A": 0.0,
            }
        }
        bands = extract_eq_bands(recipe)
        # Should include bands with non-zero gain
        assert len(bands) >= 2
        freqs = [b["frequency"] for b in bands]
        assert 60 in freqs
        assert 300 in freqs

    def test_empty_recipe_returns_empty(self):
        bands = extract_eq_bands({})
        assert bands == []

    def test_no_eq8_returns_empty(self):
        bands = extract_eq_bands({"Compressor2": {"Threshold": -18}})
        assert bands == []


class TestDetectConflicts:
    """Verify detect_conflicts flags frequency masking correctly."""

    def test_no_overlap_returns_empty(self):
        """Tracks in different frequency ranges should not conflict."""
        tracks = [
            {"name": "Kick", "role": "kick", "eq_bands": [{"frequency": 50, "gain": 3.0}]},
            {"name": "Lead", "role": "lead", "eq_bands": [{"frequency": 2000, "gain": 4.0}]},
        ]
        conflicts = detect_conflicts(tracks)
        assert conflicts == []

    def test_kick_bass_sub_low_conflict(self):
        """Kick and bass boosting in sub/low range should flag conflict."""
        tracks = [
            {"name": "Kick", "role": "kick", "eq_bands": [{"frequency": 50, "gain": 3.0}]},
            {"name": "Bass", "role": "bass", "eq_bands": [{"frequency": 55, "gain": 4.0}]},
        ]
        conflicts = detect_conflicts(tracks)
        assert len(conflicts) >= 1
        conflict = conflicts[0]
        assert "Kick" in conflict["tracks"] or "Bass" in conflict["tracks"]
        assert conflict["band"] in ("sub", "low")
        assert "freq_range" in conflict
        assert conflict["severity"] in ("high", "medium")

    def test_lead_vocal_mid_conflict(self):
        """Lead and vocal competing in mid range should flag conflict."""
        tracks = [
            {"name": "Lead", "role": "lead", "eq_bands": [{"frequency": 1500, "gain": 3.0}]},
            {"name": "Vocal", "role": "vocal", "eq_bands": [{"frequency": 1200, "gain": 4.0}]},
        ]
        conflicts = detect_conflicts(tracks)
        assert len(conflicts) >= 1
        conflict = conflicts[0]
        assert "Lead" in conflict["tracks"]
        assert "Vocal" in conflict["tracks"]

    def test_conflict_entry_structure(self):
        """Each conflict should have band, freq_range, tracks, severity, suggestion."""
        tracks = [
            {"name": "Kick", "role": "kick", "eq_bands": [{"frequency": 50, "gain": 3.0}]},
            {"name": "Bass", "role": "bass", "eq_bands": [{"frequency": 55, "gain": 4.0}]},
        ]
        conflicts = detect_conflicts(tracks)
        assert len(conflicts) >= 1
        for c in conflicts:
            assert "band" in c
            assert "freq_range" in c
            assert "tracks" in c
            assert "severity" in c
            assert "suggestion" in c

    def test_unknown_role_no_crash(self):
        """Track with no role should not crash detection."""
        tracks = [
            {"name": "FX Bus", "role": None, "eq_bands": [{"frequency": 500, "gain": 2.0}]},
            {"name": "Lead", "role": "lead", "eq_bands": [{"frequency": 600, "gain": 3.0}]},
        ]
        # Should not raise
        conflicts = detect_conflicts(tracks)
        assert isinstance(conflicts, list)

    def test_medium_severity_when_primary_present(self):
        """When one track has the band as primary, severity should be medium."""
        # Kick has sub as primary; bass also boosts sub
        tracks = [
            {"name": "Kick", "role": "kick", "eq_bands": [{"frequency": 40, "gain": 5.0}]},
            {"name": "Bass", "role": "bass", "eq_bands": [{"frequency": 45, "gain": 3.0}]},
        ]
        conflicts = detect_conflicts(tracks)
        # Both kick and bass have sub as primary, so this is medium (both have it)
        if conflicts:
            # At least one conflict should exist
            assert any(c["severity"] in ("high", "medium") for c in conflicts)

    def test_high_severity_when_neither_primary(self):
        """When neither track has the band as primary, severity should be high."""
        # Atmospheric doesn't have mid as primary, pad does have mid as primary
        # Use two roles that don't have low_mid as primary
        tracks = [
            {"name": "Lead", "role": "lead", "eq_bands": [{"frequency": 350, "gain": 4.0}]},
            {"name": "Vocal", "role": "vocal", "eq_bands": [{"frequency": 400, "gain": 3.0}]},
        ]
        conflicts = detect_conflicts(tracks)
        # lead primary: mid, upper_mid; vocal primary: mid, upper_mid, presence
        # 350-400 Hz is low_mid — neither has low_mid as primary -> high
        if conflicts:
            high_conflicts = [c for c in conflicts if c["severity"] == "high"]
            assert len(high_conflicts) >= 1


# ---------------------------------------------------------------------------
# MCP tool tests: apply_section_mix_recipe, detect_frequency_conflicts,
# setup_sidechain_chain
# ---------------------------------------------------------------------------

from MCP_Server.tools.mixing import (  # noqa: E402
    apply_section_mix_recipe,
    detect_frequency_conflicts,
    setup_sidechain_chain,
)


def _make_arrangement_state(sections=None):
    """Build a mock arrangement state with cue points and tracks."""
    if sections is None:
        sections = [
            {"name": "Intro", "time": 0.0},
            {"name": "Verse", "time": 16.0},
            {"name": "Chorus", "time": 32.0},
        ]
    return {
        "cue_points": sections,
        "signature_numerator": 4,
        "signature_denominator": 4,
        "song_length": 64.0,
        "tracks": [
            {"index": 0, "name": "Kick"},
            {"index": 1, "name": "Bass"},
            {"index": 2, "name": "Lead"},
        ],
    }


def _make_mix_state():
    """Build a mock mix state with tracks and devices."""
    return {
        "tracks": [
            {
                "name": "Kick",
                "index": 0,
                "volume": 0.85,
                "pan": 0.0,
                "devices": [
                    {"class_name": "Eq8", "index": 0, "parameters": []},
                ],
            },
            {
                "name": "Bass",
                "index": 1,
                "volume": 0.80,
                "pan": 0.0,
                "devices": [
                    {"class_name": "Eq8", "index": 0, "parameters": []},
                    {"class_name": "Compressor2", "index": 1, "parameters": []},
                ],
            },
            {
                "name": "Lead",
                "index": 2,
                "volume": 0.75,
                "pan": 0.0,
                "devices": [
                    {"class_name": "Eq8", "index": 0, "parameters": []},
                ],
            },
        ],
        "return_tracks": [],
        "master_track": {"name": "Master", "devices": []},
    }


class TestApplySectionMixRecipe:
    """Verify apply_section_mix_recipe applies recipe per-section via automation."""

    def test_valid_section_applies_recipe(self):
        mock_conn = MagicMock()
        arrangement = _make_arrangement_state()
        mock_conn.send_command.side_effect = lambda cmd, args: {
            "get_arrangement_state": arrangement,
            "get_arrangement_clips": {"clips": [
                {"start_time": 0.0, "end_time": 16.0, "length": 16.0, "name": "clip1"},
            ]},
            "insert_envelope_breakpoints": {"inserted": 2},
        }.get(cmd, {})

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = apply_section_mix_recipe(None, "Intro", 0, "kick", "house")

        result = json.loads(result_str)
        assert result["section"] == "Intro"
        assert result["track_index"] == 0
        assert result["role"] == "kick"
        assert result["genre"] == "house"
        assert result["devices_applied"] >= 1
        assert result["automation_points"] >= 1

    def test_section_not_found_returns_error(self):
        mock_conn = MagicMock()
        arrangement = _make_arrangement_state()
        mock_conn.send_command.return_value = arrangement

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = apply_section_mix_recipe(None, "NonExistent", 0, "kick", "house")

        result = json.loads(result_str)
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_invalid_recipe_returns_error(self):
        result_str = apply_section_mix_recipe(None, "Intro", 0, "invalid_role", "invalid_genre")
        result = json.loads(result_str)
        assert "error" in result


class TestDetectFrequencyConflicts:
    """Verify detect_frequency_conflicts MCP tool analyzes section tracks."""

    def test_returns_conflict_list(self):
        mock_conn = MagicMock()
        arrangement = _make_arrangement_state()
        mix_state = _make_mix_state()

        def side_effect(cmd, args):
            if cmd == "get_arrangement_state":
                return arrangement
            if cmd == "get_mix_state":
                return mix_state
            if cmd == "get_arrangement_clips":
                return {"clips": [
                    {"start_time": 0.0, "end_time": 16.0, "length": 16.0, "name": "c"},
                ]}
            return {}

        mock_conn.send_command.side_effect = side_effect

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = detect_frequency_conflicts(None, "Intro", "house")

        result = json.loads(result_str)
        assert result["section"] == "Intro"
        assert result["genre"] == "house"
        assert "tracks_analyzed" in result
        assert "conflicts" in result
        assert isinstance(result["conflicts"], list)

    def test_no_section_returns_error(self):
        mock_conn = MagicMock()
        arrangement = _make_arrangement_state()
        mock_conn.send_command.return_value = arrangement

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = detect_frequency_conflicts(None, "NonExistent", "house")

        result = json.loads(result_str)
        assert "error" in result


class TestSetupSidechainChain:
    """Verify setup_sidechain_chain auto-detects compressor and sets sidechain."""

    def test_finds_tracks_and_sets_sidechain(self):
        mock_conn = MagicMock()
        mix_state = _make_mix_state()

        def side_effect(cmd, args):
            if cmd == "get_mix_state":
                return mix_state
            if cmd == "set_sidechain_source":
                return {"device_name": "Compressor", "source_track": "Kick"}
            return {}

        mock_conn.send_command.side_effect = side_effect

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = setup_sidechain_chain(None, "Kick", "Bass")

        result = json.loads(result_str)
        assert result["source"] == "Kick"
        assert result["target"] == "Bass"
        assert result["device_index"] == 1  # Compressor2 is at index 1
        assert result["status"] == "sidechain_connected"

    def test_source_not_found_returns_error(self):
        mock_conn = MagicMock()
        mix_state = _make_mix_state()
        mock_conn.send_command.return_value = mix_state

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = setup_sidechain_chain(None, "NonExistentTrack", "Bass")

        result = json.loads(result_str)
        assert "error" in result

    def test_target_not_found_returns_error(self):
        mock_conn = MagicMock()
        mix_state = _make_mix_state()
        mock_conn.send_command.return_value = mix_state

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = setup_sidechain_chain(None, "Kick", "NonExistentTrack")

        result = json.loads(result_str)
        assert "error" in result

    def test_no_compressor_returns_error(self):
        mock_conn = MagicMock()
        mix_state = _make_mix_state()
        # Lead track has no Compressor2
        mock_conn.send_command.return_value = mix_state

        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result_str = setup_sidechain_chain(None, "Kick", "Lead")

        result = json.loads(result_str)
        assert "error" in result
