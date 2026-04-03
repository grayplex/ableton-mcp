"""Tests for MCP_Server/orchestration/agenda.py and MCP_Server/tools/orchestration.py.

Covers all 5 AGND-01/AGND-02 success criteria:
1. Techno phase order: setup→drums→bass→sound_design→arrangement→mix→master
2. Ambient has no drums phase
3. Brief energy_level >= 7 moves drums to position 1
4. Brief primary_genre overrides genre arg
5. Unknown genre returns error dict, no exception
6. total_estimated_steps == sum of phase estimated_steps
7. JSON output ≤ 400 tokens for all 12 genres (approximate: ≤1600 chars)
8. House drums phase roles include kick, snare, hi-hats
"""

import json
import sys
import types
from unittest.mock import MagicMock

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
from MCP_Server.orchestration.agenda import AGENDA_CATALOG, get_agenda, refine_agenda  # noqa: E402
from MCP_Server.orchestration.schema import ProductionAgenda, ProductionPhase  # noqa: E402


class TestProductionAgendaCatalog:
    def test_techno_phase_order(self):
        result = get_agenda("techno")
        assert "error" not in result
        phase_ids = [p["phase_id"] for p in result["phases"]]
        assert phase_ids[0] == "setup"
        assert phase_ids[1] == "drums"
        assert phase_ids[2] == "bass"
        assert phase_ids[3] == "sound_design"
        assert phase_ids[-2] == "mix"
        assert phase_ids[-1] == "master"

    def test_ambient_no_drums(self):
        result = get_agenda("ambient")
        assert "error" not in result
        phase_types = [p["phase_type"] for p in result["phases"]]
        assert "drums" not in phase_types

    def test_brief_energy_high_moves_drums_first(self):
        brief = {"primary_genre": None, "energy_level": 8}
        # Use house which normally has setup→drums→bass (drums already at 1, should stay)
        result = get_agenda("house", brief=brief)
        phase_ids = [p["phase_id"] for p in result["phases"]]
        assert phase_ids[0] == "setup"
        assert phase_ids[1] == "drums"
        # neo_soul_rnb normally has drums at position 3 — test it moves up
        result2 = get_agenda("neo_soul_rnb", brief=brief)
        phase_ids2 = [p["phase_id"] for p in result2["phases"]]
        assert phase_ids2[0] == "setup"
        assert phase_ids2[1] == "drums"

    def test_brief_primary_genre_overrides_arg(self):
        brief = {"primary_genre": "techno", "energy_level": 5}
        result = get_agenda("house", brief=brief)  # brief says techno
        assert result["genre"] == "techno"
        phase_ids = [p["phase_id"] for p in result["phases"]]
        assert "harmony" not in phase_ids  # techno has no harmony phase

    def test_unknown_genre_returns_error(self):
        result = get_agenda("not_a_real_genre_xyz")
        assert "error" in result
        assert "not_a_real_genre_xyz" in result["error"]

    def test_total_steps_is_sum(self):
        result = get_agenda("house")
        assert "error" not in result
        expected = sum(p["estimated_steps"] for p in result["phases"])
        assert result["total_estimated_steps"] == expected

    def test_json_output_reasonable_size(self):
        """Serialized JSON should be under 2000 chars (~500 tokens) for all 12 genres.

        Budget was raised from 1600 to 2000 after PARA-01: the true dependency map
        adds ~20 chars per phase (parallelizable field) plus arrangement's depends_on
        list now contains up to 5 phase ids instead of 1. 9-phase genres add ~250
        chars vs. the pre-PARA-01 budget. All genres remain well under 500 tokens.
        """
        for genre_id in AGENDA_CATALOG:
            result = get_agenda(genre_id)
            serialized = json.dumps(result)
            assert len(serialized) < 2000, f"{genre_id} agenda too large: {len(serialized)} chars"

    def test_house_drums_phase_roles(self):
        result = get_agenda("house")
        drums_phase = next(p for p in result["phases"] if p["phase_type"] == "drums")
        roles = drums_phase["roles"]
        assert "kick" in roles
        assert "snare" in roles or "clap" in roles
        assert "hi-hats" in roles


class TestRefineAgenda:
    """Tests for refine_agenda(agenda, instruction) pure function."""

    def _house_agenda(self):
        return get_agenda("house")

    def test_skip_mastering_removes_master_phase(self):
        agenda = self._house_agenda()
        original_steps = agenda["total_estimated_steps"]
        result = refine_agenda(agenda, "skip mastering")
        phase_types = [p["phase_type"] for p in result["phases"]]
        assert "master" not in phase_types
        assert result["total_estimated_steps"] == original_steps - 3

    def test_skip_drums_removes_drums_phase(self):
        agenda = self._house_agenda()
        original_steps = agenda["total_estimated_steps"]
        result = refine_agenda(agenda, "skip drums")
        phase_types = [p["phase_type"] for p in result["phases"]]
        assert "drums" not in phase_types
        assert result["total_estimated_steps"] == original_steps - 12

    def test_add_second_melody_inserts_melody_2_after_melody(self):
        agenda = self._house_agenda()
        result = refine_agenda(agenda, "add a second melody phase")
        phase_ids = [p["phase_id"] for p in result["phases"]]
        melody_idx = phase_ids.index("melody")
        assert phase_ids[melody_idx + 1] == "melody_2"
        melody_2 = result["phases"][melody_idx + 1]
        assert melody_2["depends_on"] == ["melody"]

    def test_unrecognised_instruction_returns_agenda_unchanged(self):
        agenda = self._house_agenda()
        result = refine_agenda(agenda, "do something weird XYZ-unknown")
        assert result == agenda

    def test_instruction_is_case_insensitive(self):
        agenda = self._house_agenda()
        result = refine_agenda(agenda, "Skip Mastering")
        phase_types = [p["phase_type"] for p in result["phases"]]
        assert "master" not in phase_types

    def test_total_steps_recomputed_after_skip(self):
        agenda = self._house_agenda()
        result = refine_agenda(agenda, "skip mix")
        expected = sum(p["estimated_steps"] for p in result["phases"])
        assert result["total_estimated_steps"] == expected

    def test_total_steps_recomputed_after_duplicate(self):
        agenda = self._house_agenda()
        result = refine_agenda(agenda, "add another melody")
        expected = sum(p["estimated_steps"] for p in result["phases"])
        assert result["total_estimated_steps"] == expected


class TestParallelDependencies:
    """Tests for true musical dependency map and parallelizable field (PARA-01)."""

    def _get_phase(self, genre: str, phase_type: str) -> dict:
        agenda = get_agenda(genre)
        return next(p for p in agenda["phases"] if p["phase_type"] == phase_type)

    def test_bass_depends_only_on_setup(self):
        phase = self._get_phase("house", "bass")
        assert phase["depends_on"] == ["setup"]

    def test_drums_depends_only_on_setup(self):
        phase = self._get_phase("house", "drums")
        assert phase["depends_on"] == ["setup"]

    def test_harmony_depends_only_on_setup(self):
        phase = self._get_phase("house", "harmony")
        assert phase["depends_on"] == ["setup"]

    def test_mix_depends_on_arrangement(self):
        phase = self._get_phase("house", "mix")
        assert "arrangement" in phase["depends_on"]

    def test_master_depends_on_mix(self):
        phase = self._get_phase("house", "master")
        assert phase["depends_on"] == ["mix"]

    def test_parallelizable_field_present_on_all_phases(self):
        agenda = get_agenda("house")
        for phase in agenda["phases"]:
            assert "parallelizable" in phase, f"phase {phase['phase_id']} missing parallelizable"
            assert isinstance(phase["parallelizable"], bool)

    def test_drums_bass_harmony_are_parallelizable(self):
        agenda = get_agenda("house")
        for phase in agenda["phases"]:
            if phase["phase_type"] in ("drums", "bass", "harmony"):
                assert phase["parallelizable"] is True, (
                    f"{phase['phase_type']} should be parallelizable"
                )

    def test_mix_master_are_not_parallelizable(self):
        agenda = get_agenda("house")
        for phase in agenda["phases"]:
            if phase["phase_type"] in ("mix", "master"):
                assert phase["parallelizable"] is False, (
                    f"{phase['phase_type']} should not be parallelizable"
                )

    def test_ambient_parallel_deps(self):
        # ambient has no drums — harmony still only depends on setup
        phase = self._get_phase("ambient", "harmony")
        assert phase["depends_on"] == ["setup"]

    def test_arrangement_deps_filtered_to_genre(self):
        # techno has no harmony or melody — arrangement should not list them
        phase = self._get_phase("techno", "arrangement")
        techno_phase_types = [
            p["phase_type"] for p in get_agenda("techno")["phases"]
        ]
        for dep in phase["depends_on"]:
            assert dep in techno_phase_types, (
                f"arrangement dep '{dep}' not in techno agenda phases"
            )
        assert "harmony" not in phase["depends_on"]
        assert "melody" not in phase["depends_on"]
