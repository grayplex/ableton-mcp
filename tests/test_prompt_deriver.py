"""Tests for MCP_Server/prompt/deriver.py — parameter derivation engine.

Covers all 5 DERV-* requirements:
- DERV-01: "lo-fi hip hop beat" → tempo from lo_fi blueprint [60-95]
- DERV-01: "140 BPM techno" → explicit BPM → tempo_range (135, 145)
- DERV-02: genre scale default; "euphoric trance" → major mode override
- DERV-03: lo_fi → boom_bap groove; explicit "four-on-the-floor" override
- DERV-04: "lo-fi hip hop beat" instrument_hints includes vinyl_noise + piano/keys + bass + drums
- DERV-05: energy 1-3 → laid_back; 7-10 → driving; mood override
- Reasoning list ≥ 5 entries for genre-only prompt
- Unknown prompt → primary_genre=None, confidence < 0.3
"""

import sys
import types
from unittest.mock import MagicMock

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

from MCP_Server.prompt.deriver import derive  # noqa: E402


class TestLoFiHipHopBeat:
    """DERV-01..05 all satisfied for the canonical lo-fi test case."""

    def setup_method(self):
        self.brief = derive("lo-fi hip hop beat")

    def test_primary_genre_is_lo_fi(self):
        assert self.brief["primary_genre"] == "lo_fi"

    def test_tempo_range_matches_lo_fi_blueprint(self):
        # lo_fi blueprint bpm_range is [60, 95]
        assert self.brief["tempo_range"]["min_bpm"] == 60
        assert self.brief["tempo_range"]["max_bpm"] == 95

    def test_key_feel_is_dorian_minor(self):
        kf = self.brief["key_feel"]
        assert kf["scale"] == "dorian"
        assert kf["mode"] == "minor"

    def test_groove_feel_is_boom_bap(self):
        gf = self.brief["groove_feel"]
        assert gf["pattern_type"] == "boom_bap"
        assert 60 <= gf["swing_pct"] <= 70

    def test_energy_level_is_neutral_default(self):
        # No mood signals → energy_level = 5
        assert self.brief["energy_level"] == 5

    def test_velocity_style_medium_for_neutral_energy(self):
        # energy 4-6 → medium (no mood override)
        assert self.brief["velocity_style"] == "medium"

    def test_instrument_hints_include_key_lo_fi_roles(self):
        roles = [h["role"] for h in self.brief["instrument_hints"]]
        assert "vinyl_noise" in roles
        # Piano/keys role present
        assert "piano" in roles or "keys" in roles
        # Bass role present
        assert "bass" in roles

    def test_reasoning_has_at_least_5_entries(self):
        assert len(self.brief["reasoning"]) >= 5

    def test_confidence_above_0_6(self):
        assert self.brief["confidence"] >= 0.60


class TestExplicitBPM:
    """DERV-01: explicit BPM number overrides genre blueprint range."""

    def test_140_bpm_techno(self):
        brief = derive("140 BPM techno")
        assert brief["tempo_range"]["min_bpm"] == 135
        assert brief["tempo_range"]["max_bpm"] == 145

    def test_80_bpm_lo_fi(self):
        brief = derive("80 BPM lo-fi")
        assert brief["tempo_range"]["min_bpm"] == 75
        assert brief["tempo_range"]["max_bpm"] == 85

    def test_explicit_bpm_clamped_to_200(self):
        brief = derive("220 BPM frantic techno")
        assert brief["tempo_range"]["max_bpm"] <= 200


class TestMoodKeyOverride:
    """DERV-02: mood signal overrides default genre key feel."""

    def test_euphoric_trance_shifts_to_major(self):
        brief = derive("euphoric trance anthem")
        assert brief["key_feel"]["mode"] == "major"

    def test_dark_house_stays_minor(self):
        brief = derive("dark house")
        assert brief["key_feel"]["mode"] == "minor"

    def test_dreamy_ambient_shifts_to_lydian(self):
        brief = derive("dreamy ambient")
        kf = derive("dreamy ambient")["key_feel"]
        # dreamy → lydian bias → major mode
        assert kf["mode"] == "major"

    def test_no_mood_trance_is_minor(self):
        # trance default scale is natural_minor → mode minor
        brief = derive("trance track")
        assert brief["key_feel"]["mode"] == "minor"

    def test_funky_disco_uses_dorian(self):
        brief = derive("funky disco")
        # funky → dorian scale_bias
        assert brief["key_feel"]["scale"] == "dorian"


class TestGrooveFeel:
    """DERV-03: groove feel from genre and structural hint overrides."""

    def test_lo_fi_boom_bap(self):
        assert derive("lo-fi")["groove_feel"]["pattern_type"] == "boom_bap"

    def test_house_four_on_floor(self):
        assert derive("house music")["groove_feel"]["pattern_type"] == "four_on_floor"

    def test_dnb_breakbeat(self):
        assert derive("drum and bass")["groove_feel"]["pattern_type"] == "breakbeat"

    def test_ambient_minimal(self):
        assert derive("ambient")["groove_feel"]["pattern_type"] == "minimal"

    def test_structural_hint_overrides_genre_groove(self):
        # "four-on-the-floor" as structural hint should override hip-hop boom_bap
        brief = derive("hip hop four_on_the_floor")
        assert brief["groove_feel"]["pattern_type"] == "four_on_floor"


class TestInstrumentHints:
    """DERV-04: instrument hints merged from prompt + genre blueprint."""

    def test_explicit_instrument_present(self):
        brief = derive("lo-fi with rhodes piano and bass")
        roles = [h["role"] for h in brief["instrument_hints"]]
        assert "keys" in roles or "piano" in roles
        assert "bass" in roles

    def test_genre_roles_fill_gaps(self):
        # No explicit instruments in prompt → genre blueprint fills all
        brief = derive("techno track")
        assert len(brief["instrument_hints"]) > 0

    def test_no_duplicate_roles(self):
        brief = derive("lo-fi hip hop beat with piano")
        roles = [h["role"] for h in brief["instrument_hints"]]
        assert len(roles) == len(set(roles))

    def test_808_bass_detected(self):
        brief = derive("trap beat with 808 bass")
        roles = [h["role"] for h in brief["instrument_hints"]]
        assert "bass" in roles


class TestVelocityStyle:
    """DERV-05: velocity style from energy level and mood override."""

    def test_energy_1_to_3_is_laid_back(self):
        brief = derive("sad melancholic ambient")
        assert brief["velocity_style"] == "laid_back"

    def test_energy_7_to_10_is_driving(self):
        brief = derive("aggressive hard techno")
        assert brief["velocity_style"] == "driving"

    def test_euphoric_mood_drives_energy_up(self):
        brief = derive("euphoric trance")
        assert brief["energy_level"] >= 7

    def test_chill_mood_lowers_energy(self):
        brief = derive("chill lo-fi")
        assert brief["energy_level"] <= 5

    def test_soft_mood_overrides_to_laid_back(self):
        brief = derive("soft ambient")
        assert brief["velocity_style"] == "laid_back"

    def test_aggressive_mood_overrides_to_driving(self):
        brief = derive("aggressive house")
        assert brief["velocity_style"] == "driving"


class TestEffectHints:
    """Effect hints are collected from effect signals."""

    def test_vinyl_effect_extracted(self):
        brief = derive("lo-fi with vinyl crackle")
        assert "vinyl_crackle" in brief["effect_hints"]

    def test_no_effect_signals_gives_empty_list(self):
        brief = derive("techno track")
        assert isinstance(brief["effect_hints"], list)

    def test_multiple_effects_collected(self):
        brief = derive("reverb sidechain delay techno")
        effects = brief["effect_hints"]
        assert "reverb" in effects
        assert "sidechain_compression" in effects


class TestUnknownPrompt:
    """Low-confidence parsing for unrecognized prompts."""

    def test_unknown_prompt_has_none_primary_genre(self):
        brief = derive("zubzub florp bloing")
        assert brief["primary_genre"] is None

    def test_unknown_prompt_confidence_below_0_3(self):
        brief = derive("zubzub florp bloing")
        assert brief["confidence"] < 0.3

    def test_unknown_prompt_does_not_raise(self):
        # Must not raise any exception
        brief = derive("")
        assert brief["primary_genre"] is None

    def test_unknown_prompt_reasoning_explains_low_confidence(self):
        brief = derive("unknown random words xyz")
        assert any("no genre" in r.lower() for r in brief["reasoning"])


class TestReasoningCompleteness:
    """Each derivation step produces a reasoning entry."""

    def test_reasoning_covers_all_parameters(self):
        brief = derive("dark techno")
        reasoning_text = " ".join(brief["reasoning"]).lower()
        # Each major parameter should appear in reasoning
        assert "genre" in reasoning_text
        assert "tempo" in reasoning_text or "bpm" in reasoning_text
        assert "scale" in reasoning_text or "key" in reasoning_text
        assert "groove" in reasoning_text or "pattern" in reasoning_text
        assert "velocity" in reasoning_text

    def test_reasoning_has_at_least_5_entries_for_genre_prompt(self):
        brief = derive("techno")
        assert len(brief["reasoning"]) >= 5


class TestSignalConflicts:
    """PARS-03: contradictory signals are surfaced in signal_conflicts list."""

    def test_no_conflict_gives_empty_list(self):
        # Single genre, single mood — no conflict
        brief = derive("dark techno")
        assert brief["signal_conflicts"] == []

    def test_scale_bias_conflict_detected(self):
        # "euphoric" → scale_bias=major, "dark" → scale_bias=minor
        brief = derive("euphoric dark techno")
        conflict_fields = [c["field"] for c in brief["signal_conflicts"]]
        assert "scale_bias" in conflict_fields

    def test_scale_bias_conflict_terms_and_values(self):
        brief = derive("euphoric dark techno")
        conflict = next(c for c in brief["signal_conflicts"] if c["field"] == "scale_bias")
        assert "euphoric" in conflict["terms"]
        assert "dark" in conflict["terms"]
        assert "major" in conflict["values"]
        assert "minor" in conflict["values"]

    def test_scale_bias_conflict_resolved_to_first(self):
        # "euphoric" appears before "dark" → major wins (first-wins)
        brief = derive("euphoric dark techno")
        conflict = next(c for c in brief["signal_conflicts"] if c["field"] == "scale_bias")
        assert conflict["resolved_to"] == "major"

    def test_scale_bias_resolved_to_matches_actual_key_feel(self):
        # The resolved_to value must match the actual key_feel selected
        brief = derive("euphoric dark techno")
        conflict = next(c for c in brief["signal_conflicts"] if c["field"] == "scale_bias")
        resolved_scale = conflict["resolved_to"]
        # "major" scale_bias → major mode; "minor" → minor mode
        from MCP_Server.prompt.deriver import _SCALE_BIAS_MAP, _MINOR_SCALES
        expected_scale = _SCALE_BIAS_MAP.get(resolved_scale, "natural_minor")
        assert brief["key_feel"]["scale"] == expected_scale

    def test_multi_genre_conflict_detected(self):
        # Two genre signals in one prompt
        brief = derive("techno house")
        conflict_fields = [c["field"] for c in brief["signal_conflicts"]]
        assert "primary_genre" in conflict_fields

    def test_multi_genre_conflict_resolved_to_first(self):
        brief = derive("techno house")
        conflict = next(c for c in brief["signal_conflicts"] if c["field"] == "primary_genre")
        # First matched genre wins
        assert conflict["resolved_to"] == brief["primary_genre"]

    def test_energy_conflict_detected_wide_span(self):
        # "euphoric" energy=8, "melancholic" energy=3 → span=5 ≥ 4
        brief = derive("euphoric melancholic")
        conflict_fields = [c["field"] for c in brief["signal_conflicts"]]
        assert "energy_level" in conflict_fields

    def test_energy_conflict_resolved_to_is_averaged(self):
        brief = derive("euphoric melancholic")
        conflict = next(c for c in brief["signal_conflicts"] if c["field"] == "energy_level")
        assert conflict["resolved_to"] == brief["energy_level"]

    def test_energy_no_conflict_small_span(self):
        # "euphoric" energy=8, "dark" energy=5 → span=3 < 4, no energy conflict
        brief = derive("euphoric dark techno")
        conflict_fields = [c["field"] for c in brief["signal_conflicts"]]
        assert "energy_level" not in conflict_fields

    def test_conflicts_appear_in_reasoning(self):
        # Each detected conflict must add a reasoning entry
        brief = derive("euphoric dark techno")
        reasoning_text = " ".join(brief["reasoning"]).lower()
        assert "conflict" in reasoning_text

    def test_signal_conflicts_field_always_present(self):
        # signal_conflicts must be present even when empty
        brief = derive("techno")
        assert "signal_conflicts" in brief
        assert isinstance(brief["signal_conflicts"], list)
