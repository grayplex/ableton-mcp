"""Tests for MCP_Server/prompt/ phase 42: schema, lexicon, and parser.

Covers:
- ProductionBrief and SignalSet TypedDict construction and JSON serializability
- Lexicon coverage: 12 genres, 25+ mood adjectives, 15+ instruments, 10+ effects
- parser.classify_prompt():
  - "lo-fi hip hop beat" → genre_signals=["lo_fi"], structural_hints includes "beat"
  - multi-word alias matching (drum and bass, neo soul)
  - mixed-case input normalization
  - unknown tokens passed through as raw_descriptors
  - empty prompt → empty SignalSet with confidence 0.0
  - explicit mood signal extraction
  - instrument signal extraction
  - effect signal extraction (vinyl crackle, sidechain)
  - multiple genres not double-counted
"""

import json
import sys
import types
from unittest.mock import MagicMock

# Mock mcp so imports work without the package installed
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

from MCP_Server.prompt.schema import ProductionBrief, SignalSet  # noqa: E402
from MCP_Server.prompt.lexicon import (  # noqa: E402
    GENRE_MAP, MOOD_MAP, INSTRUMENT_MAP, EFFECT_MAP, TEMPO_MAP,
)
from MCP_Server.prompt.parser import classify_prompt  # noqa: E402


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchema:
    def test_signal_set_construction(self):
        ss = SignalSet(
            genre_signals=["lo_fi"],
            mood_signals=[{"term": "chill", "energy_level": 3, "scale_bias": None}],
            instrument_signals=[],
            effect_signals=["vinyl_crackle"],
            tempo_signals=[],
            structural_hints=["beat"],
            raw_descriptors=[],
            confidence=0.82,
        )
        assert ss["genre_signals"] == ["lo_fi"]
        assert ss["confidence"] == 0.82

    def test_production_brief_construction(self):
        brief = ProductionBrief(
            raw_prompt="lo-fi hip hop beat",
            primary_genre="lo_fi",
            tempo_range={"min_bpm": 60, "max_bpm": 95},
            key_feel={"scale": "dorian", "mode": "minor"},
            groove_feel={"pattern_type": "boom_bap", "swing_pct": 65},
            energy_level=3,
            instrument_hints=[{"role": "piano", "descriptor": "warm"}],
            effect_hints=["vinyl_crackle"],
            velocity_style="laid_back",
            confidence=0.82,
            reasoning=["lo_fi detected"],
        )
        assert brief["primary_genre"] == "lo_fi"
        assert brief["velocity_style"] == "laid_back"

    def test_production_brief_json_serializable(self):
        brief = ProductionBrief(
            raw_prompt="test",
            primary_genre="techno",
            tempo_range={"min_bpm": 125, "max_bpm": 150},
            key_feel={"scale": "natural_minor", "mode": "minor"},
            groove_feel={"pattern_type": "four_on_floor", "swing_pct": 0},
            energy_level=7,
            instrument_hints=[],
            effect_hints=[],
            velocity_style="driving",
            confidence=0.75,
            reasoning=["techno detected"],
        )
        # Must not raise
        dumped = json.dumps(brief)
        loaded = json.loads(dumped)
        assert loaded["primary_genre"] == "techno"

    def test_production_brief_primary_genre_nullable(self):
        brief = ProductionBrief(
            raw_prompt="unknown",
            primary_genre=None,
            tempo_range={"min_bpm": 80, "max_bpm": 140},
            key_feel={"scale": "natural_minor", "mode": "minor"},
            groove_feel={"pattern_type": "four_on_floor", "swing_pct": 0},
            energy_level=5,
            instrument_hints=[],
            effect_hints=[],
            velocity_style="medium",
            confidence=0.1,
            reasoning=["no genre detected"],
        )
        assert brief["primary_genre"] is None
        # JSON serializable with None → null
        dumped = json.loads(json.dumps(brief))
        assert dumped["primary_genre"] is None


# ---------------------------------------------------------------------------
# Lexicon coverage tests
# ---------------------------------------------------------------------------

class TestLexicon:
    def test_all_12_genres_in_genre_map(self):
        expected_genres = {
            "lo_fi", "hip_hop_trap", "house", "techno", "drum_and_bass",
            "dubstep", "trance", "ambient", "synthwave", "future_bass",
            "neo_soul_rnb", "disco_funk",
        }
        registered = set(GENRE_MAP.values())
        assert expected_genres == registered

    def test_genre_aliases_present(self):
        assert GENRE_MAP.get("lofi") == "lo_fi"
        assert GENRE_MAP.get("dnb") == "drum_and_bass"
        assert GENRE_MAP.get("trap") == "hip_hop_trap"
        assert GENRE_MAP.get("rnb") == "neo_soul_rnb"
        assert GENRE_MAP.get("funk") == "disco_funk"

    def test_mood_map_has_25_plus_entries(self):
        assert len(MOOD_MAP) >= 25

    def test_mood_entries_have_required_keys(self):
        for term, val in MOOD_MAP.items():
            assert "energy_level" in val, f"Missing energy_level: {term}"
            assert "scale_bias" in val, f"Missing scale_bias: {term}"
            assert 1 <= val["energy_level"] <= 10, f"energy_level out of range: {term}"

    def test_instrument_map_has_15_plus_entries(self):
        assert len(INSTRUMENT_MAP) >= 15

    def test_instrument_entries_have_required_keys(self):
        for term, val in INSTRUMENT_MAP.items():
            assert "role" in val, f"Missing role: {term}"
            assert "descriptor" in val, f"Missing descriptor: {term}"

    def test_effect_map_has_10_plus_entries(self):
        assert len(EFFECT_MAP) >= 10

    def test_tempo_map_has_5_plus_entries(self):
        assert len(TEMPO_MAP) >= 5


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestClassifyPrompt:
    def test_lo_fi_hip_hop_beat(self):
        """Core test: 'lo-fi hip hop beat' → lo_fi genre, beat structural hint."""
        result = classify_prompt("lo-fi hip hop beat")
        assert "lo_fi" in result["genre_signals"]
        assert "beat" in result["structural_hints"]
        assert result["mood_signals"] == []
        assert result["instrument_signals"] == []
        assert result["effect_signals"] == []
        # hip_hop_trap should NOT be a duplicate genre signal since lo_fi_hip_hop matched
        assert "hip_hop_trap" not in result["genre_signals"]

    def test_empty_prompt_returns_empty_signal_set(self):
        result = classify_prompt("")
        assert result["genre_signals"] == []
        assert result["mood_signals"] == []
        assert result["confidence"] == 0.0

    def test_whitespace_only_returns_empty(self):
        result = classify_prompt("   ")
        assert result["confidence"] == 0.0

    def test_mixed_case_normalization(self):
        result = classify_prompt("LO-FI HIP HOP BEAT")
        assert "lo_fi" in result["genre_signals"]

    def test_multi_word_alias_drum_and_bass(self):
        result = classify_prompt("drum and bass track")
        assert "drum_and_bass" in result["genre_signals"]

    def test_multi_word_alias_neo_soul(self):
        result = classify_prompt("neo soul groove")
        assert "neo_soul_rnb" in result["genre_signals"]

    def test_single_genre_techno(self):
        result = classify_prompt("dark minimal techno")
        assert "techno" in result["genre_signals"]

    def test_mood_signal_extraction(self):
        result = classify_prompt("dark minimal techno")
        mood_terms = [m["term"] for m in result["mood_signals"]]
        assert "dark" in mood_terms

    def test_mood_energy_levels(self):
        result = classify_prompt("euphoric trance anthem")
        moods = result["mood_signals"]
        euphoric = next((m for m in moods if m["term"] == "euphoric"), None)
        assert euphoric is not None
        assert euphoric["energy_level"] >= 7
        assert euphoric["scale_bias"] == "major"

    def test_instrument_signal_extraction(self):
        result = classify_prompt("rhodes piano and 808 bass")
        roles = [i["role"] for i in result["instrument_signals"]]
        assert "keys" in roles or "piano" in roles
        assert "bass" in roles

    def test_effect_vinyl_crackle(self):
        result = classify_prompt("lo-fi beat with vinyl crackle")
        assert "vinyl_crackle" in result["effect_signals"]

    def test_effect_sidechain(self):
        result = classify_prompt("house track with sidechain compression")
        assert "sidechain_compression" in result["effect_signals"]

    def test_unknown_tokens_become_raw_descriptors(self):
        result = classify_prompt("zubzub blorp fizzquux")
        assert len(result["raw_descriptors"]) > 0
        # Confidence low when no real signals
        assert result["confidence"] <= 0.3

    def test_genre_not_double_counted(self):
        result = classify_prompt("house house house")
        assert result["genre_signals"].count("house") == 1

    def test_confidence_high_with_genre(self):
        result = classify_prompt("deep techno")
        assert result["confidence"] >= 0.60

    def test_confidence_boosted_with_mood(self):
        basic = classify_prompt("techno")
        with_mood = classify_prompt("dark techno")
        assert with_mood["confidence"] >= basic["confidence"]

    def test_explicit_genre_alias_lofi(self):
        result = classify_prompt("lofi beats")
        assert "lo_fi" in result["genre_signals"]

    def test_trap_resolves_to_hip_hop_trap(self):
        result = classify_prompt("trap beat 808 bass")
        assert "hip_hop_trap" in result["genre_signals"]

    def test_genre_dnb_alias(self):
        result = classify_prompt("dnb jungle")
        assert "drum_and_bass" in result["genre_signals"]

    def test_multiple_effects_extracted(self):
        result = classify_prompt("lo-fi with vinyl, reverb, and sidechain")
        effects = result["effect_signals"]
        assert "vinyl_crackle" in effects
        assert "reverb" in effects
        assert "sidechain_compression" in effects
