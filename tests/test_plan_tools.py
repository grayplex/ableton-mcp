"""Tests for production plan builder MCP tools.

Tests call the tool functions directly (ctx=None) to verify JSON output,
bar position math, conditional vibe field, time_signature defaulting, and
token budget constraints.

The mcp package is not available in the test environment, so we mock the
server module and FastMCP decorator before importing the tools.
"""

import json
import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Mock the mcp module hierarchy so plans.py can be imported without mcp installed
# ---------------------------------------------------------------------------
_mock_mcp = types.ModuleType("mcp")
_mock_fastmcp = types.ModuleType("mcp.server.fastmcp")
_mock_server = types.ModuleType("mcp.server")
_mock_fastmcp.Context = type("Context", (), {})
_mock_mcp.server = _mock_server
_mock_server.fastmcp = _mock_fastmcp
sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", _mock_server)
sys.modules.setdefault("mcp.server.fastmcp", _mock_fastmcp)

# Mock MCP_Server.server.mcp so @mcp.tool() is a passthrough decorator
if "MCP_Server.server" not in sys.modules:
    _mock_app_server = types.ModuleType("MCP_Server.server")
    _mcp_instance = MagicMock()
    _mcp_instance.tool.return_value = lambda fn: fn  # @mcp.tool() is identity
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server

from MCP_Server.tools.plans import generate_production_plan, generate_section_plan  # noqa: E402
from MCP_Server.genres import list_genres  # noqa: E402


# ---------------------------------------------------------------------------
# generate_production_plan tests
# ---------------------------------------------------------------------------

class TestFullPlanBasic:
    """Full plan generation returns correct structure."""

    def test_full_plan_house_basic(self):
        """generate_production_plan returns valid JSON with top-level metadata."""
        result = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
        plan = json.loads(result)
        assert plan["genre"] == "house"
        assert plan["key"] == "Am"
        assert plan["bpm"] == 125
        assert plan["time_signature"] == "4/4"
        assert "sections" in plan
        assert isinstance(plan["sections"], list)
        assert len(plan["sections"]) == 7

    def test_full_plan_sections_have_required_fields(self):
        """Each section in the plan has name, bar_start, bars, and roles."""
        result = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
        plan = json.loads(result)
        for section in plan["sections"]:
            assert "name" in section, f"Missing 'name' in {section}"
            assert "bar_start" in section, f"Missing 'bar_start' in {section}"
            assert "bars" in section, f"Missing 'bars' in {section}"
            assert "roles" in section, f"Missing 'roles' in {section}"
            assert isinstance(section["bar_start"], int)
            assert isinstance(section["bars"], int)
            assert isinstance(section["roles"], list)

    def test_full_plan_bar_positions_house(self):
        """House sections have cumulative bar_start values starting from 1."""
        # intro=16, buildup=8, drop=32, breakdown=16, buildup2=8, drop2=32, outro=16
        # bar_starts: 1, 17, 25, 57, 73, 81, 113
        expected_starts = [1, 17, 25, 57, 73, 81, 113]
        result = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
        plan = json.loads(result)
        actual_starts = [s["bar_start"] for s in plan["sections"]]
        assert actual_starts == expected_starts, (
            f"Expected bar_starts {expected_starts}, got {actual_starts}"
        )

    def test_full_plan_transition_in_absent_for_first_section(self):
        """First section (intro) has no 'transition_in'; second section (buildup) does."""
        result = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
        plan = json.loads(result)
        sections = plan["sections"]
        assert "transition_in" not in sections[0], (
            "Intro section should not have transition_in"
        )
        assert "transition_in" in sections[1], (
            "Buildup section should have transition_in"
        )

    def test_full_plan_vibe_included_when_provided(self):
        """Vibe string is echoed verbatim when provided."""
        result = generate_production_plan(
            ctx=None, genre="house", key="Am", bpm=125, vibe="dark and groovy"
        )
        plan = json.loads(result)
        assert "vibe" in plan
        assert plan["vibe"] == "dark and groovy"

    def test_full_plan_vibe_absent_when_omitted(self):
        """Vibe key is absent when not provided."""
        result = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
        plan = json.loads(result)
        assert "vibe" not in plan

    def test_full_plan_time_signature_custom(self):
        """Custom time_signature is reflected in output."""
        result = generate_production_plan(
            ctx=None, genre="house", key="Am", bpm=125, time_signature="3/4"
        )
        plan = json.loads(result)
        assert plan["time_signature"] == "3/4"

    def test_full_plan_all_12_genres(self):
        """generate_production_plan succeeds for all 12 registered base genres."""
        genres = list_genres()
        genre_ids = [g["id"] for g in genres]
        assert len(genre_ids) == 12, f"Expected 12 genres, got {len(genre_ids)}"
        for genre_id in genre_ids:
            result = generate_production_plan(
                ctx=None, genre=genre_id, key="Am", bpm=120
            )
            plan = json.loads(result)
            assert "sections" in plan, f"No sections in {genre_id} plan"
            assert isinstance(plan["sections"], list)
            assert len(plan["sections"]) > 0, f"Empty sections in {genre_id} plan"

    def test_token_budget_all_genres(self):
        """Plan JSON output is under 1600 chars for all 12 base genres (proxy for 400 tokens)."""
        genres = list_genres()
        for genre_entry in genres:
            genre_id = genre_entry["id"]
            result = generate_production_plan(
                ctx=None, genre=genre_id, key="Am", bpm=120
            )
            plan = json.loads(result)
            serialized = json.dumps(plan)
            assert len(serialized) < 1600, (
                f"Genre '{genre_id}' plan is {len(serialized)} chars "
                f"(limit: 1600). Plan: {serialized[:200]}..."
            )

    def test_full_plan_unknown_genre_returns_error(self):
        """Unknown genre returns a string starting with 'Error:'."""
        result = generate_production_plan(
            ctx=None, genre="nonexistent", key="C", bpm=120
        )
        assert isinstance(result, str)
        assert result.startswith("Error:")


# ---------------------------------------------------------------------------
# generate_section_plan tests
# ---------------------------------------------------------------------------

class TestSectionPlan:
    """Single-section plan generation."""

    def test_section_plan_house_drop(self):
        """generate_section_plan for 'drop' returns correct structure."""
        result = generate_section_plan(
            ctx=None, genre="house", key="Am", bpm=125, section_name="drop"
        )
        plan = json.loads(result)
        assert "section" in plan
        section = plan["section"]
        assert section["name"] == "drop"
        assert section["bar_start"] == 25
        assert section["bars"] == 32
        assert isinstance(section["roles"], list)
        assert len(section["roles"]) > 0

    def test_section_plan_bar_start_correct(self):
        """generate_section_plan for 'breakdown' in house returns bar_start=57."""
        result = generate_section_plan(
            ctx=None, genre="house", key="Am", bpm=125, section_name="breakdown"
        )
        plan = json.loads(result)
        assert plan["section"]["bar_start"] == 57

    def test_section_plan_unknown_section_returns_error(self):
        """Unknown section name returns a string starting with 'Error:'."""
        result = generate_section_plan(
            ctx=None, genre="house", key="Am", bpm=125, section_name="nonexistent"
        )
        assert isinstance(result, str)
        assert result.startswith("Error:")

    def test_section_plan_has_header(self):
        """Section plan output includes genre, key, bpm, and time_signature."""
        result = generate_section_plan(
            ctx=None, genre="house", key="Am", bpm=125, section_name="intro"
        )
        plan = json.loads(result)
        assert plan["genre"] == "house"
        assert plan["key"] == "Am"
        assert plan["bpm"] == 125
        assert plan["time_signature"] == "4/4"

    def test_section_plan_accepts_time_signature(self):
        """Custom time_signature is reflected in section plan output."""
        result = generate_section_plan(
            ctx=None, genre="house", key="Am", bpm=125, section_name="drop",
            time_signature="6/8"
        )
        plan = json.loads(result)
        assert plan["time_signature"] == "6/8"

    def test_section_plan_unknown_genre_returns_error(self):
        """Unknown genre in section plan returns error string."""
        result = generate_section_plan(
            ctx=None, genre="nonexistent", key="Am", bpm=120, section_name="drop"
        )
        assert result.startswith("Error:")


# ---------------------------------------------------------------------------
# Blueprint mutation safety test
# ---------------------------------------------------------------------------

class TestBlueprintMutationSafety:
    """Blueprint data in the registry is never mutated by tool calls."""

    def test_blueprint_data_not_mutated(self):
        """Calling generate_production_plan twice returns identical results (deep copy works)."""
        result1 = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
        result2 = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
        plan1 = json.loads(result1)
        plan2 = json.loads(result2)
        # Both calls must produce identical section structures
        assert plan1["sections"] == plan2["sections"]
        # Bar starts must be identical (would diverge if cumulative state leaked)
        starts1 = [s["bar_start"] for s in plan1["sections"]]
        starts2 = [s["bar_start"] for s in plan2["sections"]]
        assert starts1 == starts2
        # Verify that original expected bar starts are preserved on second call
        assert starts1 == [1, 17, 25, 57, 73, 81, 113]
