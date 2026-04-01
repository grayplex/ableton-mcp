"""Tests for MCP_Server/orchestration/execution.py.

Covers all 8 EXEC-01/EXEC-02 success criteria:
1. drums/house checklist contains add_notes_to_clip step with kick note (pitch 36)
2. get_execution_plan("drums","ambient") returns {"error": ...}
3. mix/house checklist contains apply_mix_recipe step
4. master/techno checklist contains apply_master_recipe step
5. section_name="Drop" uses create_arrangement_midi_clip, not create_clip
6. setup/house set_tempo step has tempo == 125 (house BPM midpoint)
7. serialized PhaseChecklist < 2000 chars for all 9 phase types × house
8. step_number values are sequential 1,2,...N
"""

import json
import sys
import types
from unittest.mock import MagicMock

# --- Mock mcp module hierarchy (needed because tools/orchestration.py imports mcp) ---
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
from MCP_Server.orchestration.execution import get_execution_plan  # noqa: E402


class TestPhaseExecutionPlan:
    def test_drums_house_has_kick_notes(self):
        result = get_execution_plan("drums", "house")
        assert "error" not in result
        notes_steps = [s for s in result["steps"] if s["tool_name"] == "add_notes_to_clip"]
        kick_step = next(
            (s for s in notes_steps
             if any(n.get("pitch") == 36 for n in s["suggested_args"].get("notes", []))),
            None,
        )
        assert kick_step is not None

    def test_drums_ambient_returns_error(self):
        result = get_execution_plan("drums", "ambient")
        assert "error" in result

    def test_mix_phase_has_apply_recipe_step(self):
        result = get_execution_plan("mix", "house")
        assert "error" not in result
        tool_names = [s["tool_name"] for s in result["steps"]]
        assert "apply_mix_recipe" in tool_names

    def test_master_phase_has_apply_master_recipe(self):
        result = get_execution_plan("master", "techno")
        assert "error" not in result
        tool_names = [s["tool_name"] for s in result["steps"]]
        assert "apply_master_recipe" in tool_names

    def test_section_name_uses_arrangement_clip(self):
        result = get_execution_plan("drums", "house", section_name="Drop")
        assert "error" not in result
        tool_names = [s["tool_name"] for s in result["steps"]]
        assert "create_arrangement_midi_clip" in tool_names
        assert "create_clip" not in tool_names

    def test_setup_phase_has_set_tempo(self):
        result = get_execution_plan("setup", "house")
        assert "error" not in result
        tempo_step = next((s for s in result["steps"] if s["tool_name"] == "set_tempo"), None)
        assert tempo_step is not None
        assert tempo_step["suggested_args"]["tempo"] == 125  # house midpoint (120+130)//2

    def test_json_output_under_2000_chars(self):
        phase_types = [
            "setup", "drums", "bass", "harmony", "melody",
            "sound_design", "arrangement", "mix", "master",
        ]
        for pt in phase_types:
            result = get_execution_plan(pt, "house")
            if "error" not in result:
                serialized = json.dumps(result)
                assert len(serialized) < 2000, (
                    f"{pt} checklist too large: {len(serialized)} chars"
                )

    def test_step_numbers_sequential(self):
        result = get_execution_plan("drums", "house")
        assert "error" not in result
        nums = [s["step_number"] for s in result["steps"]]
        assert nums == list(range(1, len(nums) + 1))

    def test_session_clip_steps_use_sentinel_clip_index(self):
        """Session-clip steps must NOT hardcode clip_index=0."""
        for phase in ["drums", "bass", "harmony", "melody"]:
            result = get_execution_plan(phase, "house")  # no section_name
            assert "error" not in result, f"{phase} returned error"
            for step in result["steps"]:
                args = step.get("suggested_args", {})
                if "clip_index" in args:
                    assert args["clip_index"] == "<clip_index>", (
                        f"{phase} step {step['step_number']} ({step['tool_name']}) "
                        f"has hardcoded clip_index={args['clip_index']}"
                    )

    def test_every_step_has_phase_key(self):
        """Every step dict must contain a 'phase' key with a non-empty string."""
        phase_types = [
            "setup", "drums", "bass", "harmony", "melody",
            "sound_design", "arrangement", "mix", "master",
        ]
        for pt in phase_types:
            result = get_execution_plan(pt, "house")
            if "error" in result:
                continue
            for step in result["steps"]:
                assert "phase" in step, (
                    f"{pt} step {step['step_number']} missing 'phase' key"
                )
                assert isinstance(step["phase"], str) and step["phase"], (
                    f"{pt} step {step['step_number']} has empty/non-string 'phase'"
                )

    def test_arrangement_clip_steps_have_no_clip_index(self):
        """Arrangement-clip steps should not contain clip_index."""
        for phase in ["drums", "bass", "harmony", "melody"]:
            result = get_execution_plan(phase, "house", section_name="Drop")
            assert "error" not in result
            for step in result["steps"]:
                args = step.get("suggested_args", {})
                if step["tool_name"] == "create_arrangement_midi_clip":
                    assert "clip_index" not in args
