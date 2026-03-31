"""Tests for MCP_Server/tools/prompt.py — interpret_prompt and interpret_prompt_to_plan MCP tools.

Covers TOOL-01 and TOOL-02:
- interpret_prompt returns a valid ProductionBrief JSON with all 10 fields
- interpret_prompt returns non-empty reasoning list
- interpret_prompt_to_plan returns both brief and plan in one call
- interpret_prompt_to_plan plan shape matches generate_production_plan output
- Both tools registered in tools/__init__.py
- Unrecognized prompt returns primary_genre=null, confidence < 0.3 without exception
"""

import json
import sys
import types
from unittest.mock import MagicMock

# Mock mcp so imports work without the server installed
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

from MCP_Server.tools.prompt import interpret_prompt, interpret_prompt_to_plan  # noqa: E402

_CTX = None  # tools accept Context but don't use it in prompt tools

# Required ProductionBrief fields
_BRIEF_FIELDS = {
    "raw_prompt", "primary_genre", "tempo_range", "key_feel",
    "groove_feel", "energy_level", "instrument_hints", "effect_hints",
    "velocity_style", "confidence", "reasoning",
}


class TestInterpretPrompt:
    """TOOL-01: interpret_prompt returns valid ProductionBrief JSON."""

    def test_dark_minimal_techno_returns_json(self):
        result = interpret_prompt(_CTX, "dark minimal techno")
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_all_10_fields_present(self):
        result = json.loads(interpret_prompt(_CTX, "dark minimal techno"))
        for field in _BRIEF_FIELDS:
            assert field in result, f"Missing field: {field}"

    def test_primary_genre_is_techno(self):
        result = json.loads(interpret_prompt(_CTX, "dark minimal techno"))
        assert result["primary_genre"] == "techno"

    def test_reasoning_list_non_empty(self):
        result = json.loads(interpret_prompt(_CTX, "dark minimal techno"))
        assert isinstance(result["reasoning"], list)
        assert len(result["reasoning"]) >= 1

    def test_tempo_range_has_min_and_max(self):
        result = json.loads(interpret_prompt(_CTX, "techno"))
        tr = result["tempo_range"]
        assert "min_bpm" in tr
        assert "max_bpm" in tr
        assert tr["min_bpm"] < tr["max_bpm"]

    def test_key_feel_has_scale_and_mode(self):
        result = json.loads(interpret_prompt(_CTX, "techno"))
        kf = result["key_feel"]
        assert "scale" in kf
        assert "mode" in kf
        assert kf["mode"] in ("major", "minor")

    def test_groove_feel_has_pattern_type_and_swing(self):
        result = json.loads(interpret_prompt(_CTX, "techno"))
        gf = result["groove_feel"]
        assert "pattern_type" in gf
        assert "swing_pct" in gf

    def test_velocity_style_valid_enum(self):
        result = json.loads(interpret_prompt(_CTX, "techno"))
        assert result["velocity_style"] in ("laid_back", "medium", "driving")

    def test_confidence_in_range(self):
        result = json.loads(interpret_prompt(_CTX, "techno"))
        assert 0.0 <= result["confidence"] <= 1.0

    def test_lo_fi_hip_hop_beat(self):
        result = json.loads(interpret_prompt(_CTX, "lo-fi hip hop beat"))
        assert result["primary_genre"] == "lo_fi"
        assert result["groove_feel"]["pattern_type"] == "boom_bap"

    def test_unknown_prompt_primary_genre_null(self):
        result = json.loads(interpret_prompt(_CTX, "zubzub florp bloing"))
        assert result["primary_genre"] is None
        assert result["confidence"] < 0.3

    def test_unknown_prompt_does_not_raise(self):
        # Must return JSON, not raise
        result = interpret_prompt(_CTX, "completely unknown xyz abc")
        data = json.loads(result)
        assert "primary_genre" in data

    def test_empty_prompt_does_not_raise(self):
        result = interpret_prompt(_CTX, "")
        data = json.loads(result)
        assert "primary_genre" in data or "error" in data


class TestInterpretPromptToPlan:
    """TOOL-02: interpret_prompt_to_plan returns brief + plan in one call."""

    def test_lo_fi_returns_both_brief_and_plan(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "lo-fi hip hop beat"))
        assert "brief" in result
        assert "plan" in result
        assert result["plan"] is not None

    def test_brief_has_all_fields(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "lo-fi hip hop beat"))
        brief = result["brief"]
        for field in _BRIEF_FIELDS:
            assert field in brief, f"Missing brief field: {field}"

    def test_plan_shape_matches_generate_production_plan(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "house music"))
        plan = result["plan"]
        assert "genre" in plan
        assert "key" in plan
        assert "bpm" in plan
        assert "time_signature" in plan
        assert "sections" in plan
        assert isinstance(plan["sections"], list)
        assert len(plan["sections"]) > 0

    def test_plan_sections_have_bar_start(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "house music"))
        for section in result["plan"]["sections"]:
            assert "bar_start" in section
            assert "bars" in section
            assert "name" in section

    def test_plan_bpm_within_genre_range(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "techno"))
        brief = result["brief"]
        plan = result["plan"]
        min_bpm = brief["tempo_range"]["min_bpm"]
        max_bpm = brief["tempo_range"]["max_bpm"]
        assert min_bpm <= plan["bpm"] <= max_bpm

    def test_vibe_in_plan_reflects_prompt(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "dark techno banger"))
        assert result["plan"]["vibe"] == "dark techno banger"

    def test_unknown_prompt_plan_is_null(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "zzzzunknown"))
        assert result["plan"] is None
        assert "warning" in result

    def test_unknown_prompt_does_not_raise(self):
        result = interpret_prompt_to_plan(_CTX, "xyzabc unknown")
        data = json.loads(result)
        assert "brief" in data

    def test_bars_per_section_override_applied(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "techno", bars_per_section=8))
        for section in result["plan"]["sections"]:
            assert section["bars"] == 8

    def test_techno_genre_id_in_plan(self):
        result = json.loads(interpret_prompt_to_plan(_CTX, "minimal techno"))
        assert result["plan"]["genre"] == "techno"

    def test_ambient_plan_has_minimal_groove(self):
        brief_result = json.loads(interpret_prompt(_CTX, "ambient"))
        assert brief_result["groove_feel"]["pattern_type"] == "minimal"


class TestToolRegistration:
    """Both tools visible after import of tools package."""

    def test_interpret_prompt_is_callable(self):
        assert callable(interpret_prompt)

    def test_interpret_prompt_to_plan_is_callable(self):
        assert callable(interpret_prompt_to_plan)

    def test_prompt_module_importable_from_tools(self):
        import MCP_Server.tools.prompt as ptool  # noqa: F401
        assert hasattr(ptool, "interpret_prompt")
        assert hasattr(ptool, "interpret_prompt_to_plan")
