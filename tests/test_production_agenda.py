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
        """Serialized JSON should be under 1600 chars (~400 tokens) for all 12 genres."""
        for genre_id in AGENDA_CATALOG:
            result = get_agenda(genre_id)
            serialized = json.dumps(result)
            assert len(serialized) < 1600, f"{genre_id} agenda too large: {len(serialized)} chars"

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
