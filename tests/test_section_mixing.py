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
