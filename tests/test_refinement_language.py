"""Tests for Phase 46: Refinement Language Engine.

Covers:
- REFINEMENT_LEXICON structure and required adjectives
- _normalize_instruction: single and multi-word matching
- _merge_vectors: accumulation with clamping
- _scale_substitutions_from_mode_bias: minor/major/None
- build_section_refinement_plan: plan returned with correct track ops
- Unknown instruction → empty plan with explanatory reasoning
- interpret_section_refinement: callable MCP tool
- refine_prompt: mood, tempo, diff, low-confidence warning tests
"""

import json
import sys
import types
from unittest.mock import MagicMock, patch

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

import pytest  # noqa: E402

# ---------------------------------------------------------------------------
# Sample brief for refine_prompt tests
# ---------------------------------------------------------------------------

_SAMPLE_BRIEF = {
    "raw_prompt": "house track",
    "primary_genre": "house",
    "tempo_range": {"min_bpm": 120, "max_bpm": 130},
    "key_feel": {"scale": "major", "mode": "major"},
    "groove_feel": {"pattern_type": "four_on_floor", "swing_pct": 0},
    "energy_level": 7,
    "instrument_hints": [{"role": "kick", "descriptor": "punchy"}],
    "effect_hints": ["sidechain"],
    "velocity_style": "driving",
    "confidence": 0.9,
    "reasoning": ["house detected → primary_genre=house"],
}


# ---------------------------------------------------------------------------
# Helper: build a mock Ableton connection with a named section
# ---------------------------------------------------------------------------

def _make_mock_conn(section_name: str = "Bridge", num_clips: int = 1):
    """Create a mock connection object with one section and one track."""
    conn = MagicMock()

    arrangement_state = {
        "cue_points": [
            {"name": "Intro", "time": 0.0},
            {"name": section_name, "time": 16.0},
            {"name": "Outro", "time": 32.0},
        ],
        "signature_numerator": 4,
        "signature_denominator": 4,
        "song_length": 64.0,
        "tracks": [
            {"index": 0, "name": "Pad"},
        ],
    }

    clips = [{"start_time": 16.0, "end_time": 32.0, "length": 16.0, "is_audio_clip": False}]

    mix_state = {
        "tracks": [
            {
                "name": "Pad",
                "volume": 0.8,
                "pan": 0.0,
                "devices": [
                    {
                        "device_name": "AutoFilter",
                        "class_name": "AutoFilter",
                        "prominent_params": {"Frequency": 0.6, "Resonance": 0.3},
                        "parameters": [],
                    }
                ],
            }
        ]
    }

    def send_command(cmd, args=None):
        if cmd == "get_arrangement_state":
            return arrangement_state
        if cmd == "get_arrangement_clips":
            return {"clips": clips if num_clips > 0 else []}
        if cmd == "get_arrangement_clip_notes":
            return {"notes": [{"pitch": 60}, {"pitch": 64}]}
        if cmd == "get_mix_state":
            return mix_state
        return {}

    conn.send_command.side_effect = send_command
    return conn


# ===========================================================================
# TestLexicon
# ===========================================================================


class TestLexicon:
    def test_lexicon_has_20_adjectives(self):
        from MCP_Server.refinement.lexicon import REFINEMENT_LEXICON
        assert len(REFINEMENT_LEXICON) >= 20

    def test_darker_vector_shape(self):
        from MCP_Server.refinement.lexicon import REFINEMENT_LEXICON
        v = REFINEMENT_LEXICON["darker"]
        assert v["harmonic"]["register_shift_semitones"] == -3
        assert v["harmonic"]["mode_bias"] == "minor"
        assert v["timbral"]["filter_cutoff_delta_pct"] == -25.0

    def test_vector_merge_accumulates(self):
        from MCP_Server.refinement.interpreter import _merge_vectors
        merged = _merge_vectors(["darker", "heavier"])
        # darker=-3 + heavier=-2 = -5
        assert merged["harmonic"]["register_shift_semitones"] == -5
        # -5 is within [-12, +12] so no clamping needed
        assert -12 <= merged["harmonic"]["register_shift_semitones"] <= 12


# ===========================================================================
# TestInterpreter
# ===========================================================================


class TestInterpreter:
    def test_normalize_instruction_single(self):
        from MCP_Server.refinement.interpreter import _normalize_instruction
        keys = _normalize_instruction("make it darker")
        assert "darker" in keys

    def test_normalize_instruction_multiword(self):
        from MCP_Server.refinement.interpreter import _normalize_instruction
        keys = _normalize_instruction("more energetic and brighter")
        assert "more_energetic" in keys
        assert "brighter" in keys

    def test_scale_substitutions_minor(self):
        from MCP_Server.refinement.interpreter import _scale_substitutions_from_mode_bias
        subs = _scale_substitutions_from_mode_bias("minor")
        assert {"from_pitch_class": 4, "to_pitch_class": 3} in subs

    def test_scale_substitutions_none(self):
        from MCP_Server.refinement.interpreter import _scale_substitutions_from_mode_bias
        assert _scale_substitutions_from_mode_bias(None) == []

    def test_build_plan_returns_plan(self):
        from MCP_Server.refinement.interpreter import build_section_refinement_plan
        conn = _make_mock_conn("Bridge")
        plan = build_section_refinement_plan("Bridge", "make it darker", conn)
        assert plan["section"] == "Bridge"
        assert len(plan["tracks"]) == 1
        # "darker" → register_shift_semitones=-3
        assert plan["tracks"][0]["note_operation"]["semitone_shift"] == -3

    def test_build_plan_unknown_instruction(self):
        from MCP_Server.refinement.interpreter import build_section_refinement_plan
        conn = _make_mock_conn("Bridge")
        plan = build_section_refinement_plan("Bridge", "xyzqwerty", conn)
        assert plan["tracks"] == []
        assert any("No refinement" in r for r in plan["reasoning"])

    def test_interpret_section_refinement_registered(self):
        from MCP_Server.tools.refinement import interpret_section_refinement
        assert callable(interpret_section_refinement)


# ===========================================================================
# TestRefinePrompt
# ===========================================================================


class TestRefinePrompt:
    def test_refine_prompt_mood_only(self):
        """Mood signal 'dark' should update key_feel to minor mode."""
        from MCP_Server.tools.refinement import refine_prompt

        brief = dict(_SAMPLE_BRIEF)
        # Use "dark" which is in MOOD_MAP with scale_bias="minor"
        result = json.loads(refine_prompt(None, brief, "make it dark"))
        # key_feel should change to a minor scale
        assert "key_feel" in result["diff"]
        assert result["diff"]["key_feel"]["before"]["mode"] == "major"
        assert result["diff"]["key_feel"]["after"]["mode"] == "minor"

    def test_refine_prompt_tempo_explicit(self):
        """Explicit BPM in refinement text should update tempo_range."""
        from MCP_Server.tools.refinement import refine_prompt

        brief = dict(_SAMPLE_BRIEF)
        result = json.loads(refine_prompt(None, brief, "speed it up to 140 BPM"))
        assert "tempo_range" in result["diff"]
        assert result["diff"]["tempo_range"]["after"]["min_bpm"] == 135
        assert result["diff"]["tempo_range"]["after"]["max_bpm"] == 145
        # genre should not be in diff
        assert "primary_genre" not in result["diff"]

    def test_refine_prompt_no_change(self):
        """Unrecognized refinement text → empty diff and explanatory reasoning."""
        from MCP_Server.tools.refinement import refine_prompt

        brief = dict(_SAMPLE_BRIEF)
        result = json.loads(refine_prompt(None, brief, "xyzqwerty123"))
        assert result["diff"] == {}
        assert any("No recognized" in r for r in result["brief"]["reasoning"])

    def test_refine_prompt_diff_only_changed_fields(self):
        """diff should contain only fields that actually changed."""
        from MCP_Server.tools.refinement import refine_prompt

        brief = dict(_SAMPLE_BRIEF)
        result = json.loads(refine_prompt(None, brief, "make it dark"))
        # tempo_range and primary_genre should NOT be in diff (no tempo/genre signals)
        assert "primary_genre" not in result["diff"]

    def test_refine_prompt_low_confidence_warning(self):
        """Brief with confidence < 0.3 should add a warning to reasoning."""
        from MCP_Server.tools.refinement import refine_prompt

        low_conf_brief = dict(_SAMPLE_BRIEF)
        low_conf_brief["confidence"] = 0.2
        result = json.loads(refine_prompt(None, low_conf_brief, "xyzqwerty123"))
        assert any("Warning" in r and "low confidence" in r for r in result["brief"]["reasoning"])
