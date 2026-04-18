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

    def test_drums_neo_soul_rnb_not_house_pattern(self):
        """neo_soul_rnb drums should use a swing/R&B pattern, not four-on-the-floor house."""
        result = get_execution_plan("drums", "neo_soul_rnb")
        assert "error" not in result
        notes_steps = [s for s in result["steps"] if s["tool_name"] == "add_notes_to_clip"]
        all_notes = []
        for step in notes_steps:
            all_notes.extend(step.get("suggested_args", {}).get("notes", []))
        # House pattern has kick (pitch 36) at start_time=2.0 — neo_soul_rnb must not
        house_kick_on_3 = any(
            n["pitch"] == 36 and n["start_time"] == 2.0 and n["velocity"] == 100
            for n in all_notes
        )
        assert not house_kick_on_3, "neo_soul_rnb should not use the house drum pattern"
        # Must have snare (pitch 38) on beat 2 (start_time=1.0) — characteristic R&B feel
        has_snare_on_2 = any(n["pitch"] == 38 and n["start_time"] == 1.0 for n in all_notes)
        assert has_snare_on_2, "neo_soul_rnb should have snare on beat 2"

    def test_bass_patterns_vary_by_genre(self):
        """Different genre groups produce different bass note patterns."""
        house = get_execution_plan("bass", "house")
        dubstep = get_execution_plan("bass", "dubstep")
        hiphop = get_execution_plan("bass", "hip_hop_trap")
        assert "error" not in house
        assert "error" not in dubstep
        assert "error" not in hiphop

        def extract_bass_notes(result):
            for s in result["steps"]:
                if s["tool_name"] == "add_notes_to_clip":
                    return s["suggested_args"].get("notes", [])
            return []

        house_notes = extract_bass_notes(house)
        dubstep_notes = extract_bass_notes(dubstep)
        hiphop_notes = extract_bass_notes(hiphop)

        # Each genre group must produce distinct patterns
        assert house_notes != dubstep_notes, "house and dubstep bass should differ"
        assert house_notes != hiphop_notes, "house and hip_hop_trap bass should differ"
        assert dubstep_notes != hiphop_notes, "dubstep and hip_hop_trap bass should differ"

    def test_bass_all_genres_no_error(self):
        """All 12 genres produce valid bass checklists."""
        genres = [
            "house", "techno", "ambient", "hip_hop_trap", "drum_and_bass",
            "dubstep", "trance", "synthwave", "future_bass", "lo_fi",
            "neo_soul_rnb", "disco_funk",
        ]
        for g in genres:
            result = get_execution_plan("bass", g)
            assert "error" not in result, f"bass/{g} returned error: {result.get('error')}"

    def test_sentinel_steps_have_depends_on_step(self):
        """Every step with a <...> sentinel in suggested_args must have depends_on_step set."""
        import re
        sentinel_re = re.compile(r"^<.*>$")
        phase_types = [
            "setup", "drums", "bass", "harmony", "melody",
            "sound_design", "arrangement", "mix", "master",
        ]
        for pt in phase_types:
            result = get_execution_plan(pt, "house")
            if "error" in result:
                continue
            for step in result["steps"]:
                args = step.get("suggested_args", {})
                has_sentinel = any(
                    isinstance(v, str) and sentinel_re.match(v)
                    for v in args.values()
                )
                if has_sentinel:
                    assert "depends_on_step" in step, (
                        f"{pt} step {step['step_number']} ({step['tool_name']}) "
                        f"uses sentinel args but has no depends_on_step"
                    )
                    assert isinstance(step["depends_on_step"], int), (
                        f"{pt} step {step['step_number']} ({step['tool_name']}) "
                        f"depends_on_step is not an int: {step['depends_on_step']}"
                    )

    def test_sound_design_starts_with_query_step(self):
        """sound_design phase should start with get_arrangement_overview query step."""
        result = get_execution_plan("sound_design", "house")
        assert "error" not in result
        assert result["steps"][0]["tool_name"] == "get_arrangement_overview"

    def test_mix_starts_with_query_step(self):
        """mix phase should start with get_arrangement_overview query step."""
        result = get_execution_plan("mix", "house")
        assert "error" not in result
        assert result["steps"][0]["tool_name"] == "get_arrangement_overview"

    def test_sentinel_steps_have_resolution_hint(self):
        """Steps using <track_index> sentinel should have resolution hints in description."""
        phases_with_sentinels = ["drums", "bass", "harmony", "melody"]
        for phase in phases_with_sentinels:
            result = get_execution_plan(phase, "house")
            assert "error" not in result, f"{phase} returned error"
            # Find the first step that uses <track_index> in suggested_args
            sentinel_steps = [
                s for s in result["steps"]
                if s.get("suggested_args", {}).get("track_index") == "<track_index>"
            ]
            assert len(sentinel_steps) > 0, f"{phase} has no <track_index> sentinel steps"
            # The first sentinel step (set_track_name, step 2) should have a resolution hint
            first_sentinel = sentinel_steps[0]
            desc = first_sentinel["description"].lower()
            has_hint = ("resolve" in desc or "get_arrangement_overview" in desc
                        or "get_all_tracks" in desc)
            assert has_hint, (
                f"{phase} first sentinel step description lacks resolution hint: "
                f"'{first_sentinel['description']}'"
            )
