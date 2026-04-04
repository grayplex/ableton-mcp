"""Tests for MCP_Server/prompt/history.py and list_production_briefs tool.

Covers SESS-03:
- record_brief / get_briefs round-trip
- clear_briefs empties the log
- get_briefs returns copies (not mutable internal state)
- interpret_prompt and interpret_prompt_to_plan record briefs
- list_production_briefs returns JSON with count, session_started, and briefs array
"""

import json
import sys
import time
import types
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Mock mcp module hierarchy (same pattern as test_refinement_history.py)
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

from MCP_Server.prompt.history import (  # noqa: E402
    clear_briefs,
    get_briefs,
    record_brief,
)
from MCP_Server.tools.prompt import (  # noqa: E402
    interpret_prompt,
    interpret_prompt_to_plan,
    list_production_briefs,
)

_CTX = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_briefs():
    """Clear brief log before and after every test for isolation."""
    clear_briefs()
    yield
    clear_briefs()


# ---------------------------------------------------------------------------
# record_brief / get_briefs
# ---------------------------------------------------------------------------

class TestRecordAndGetBriefs:
    def test_get_briefs_empty_initially(self):
        assert get_briefs() == []

    def test_record_brief_adds_entry(self):
        record_brief("techno", {"primary_genre": "techno"}, "interpret_prompt")
        assert len(get_briefs()) == 1

    def test_entry_has_all_fields(self):
        record_brief("techno", {"primary_genre": "techno"}, "interpret_prompt")
        entry = get_briefs()[0]
        assert "raw_prompt" in entry
        assert "brief" in entry
        assert "source" in entry
        assert "timestamp" in entry

    def test_entries_ordered_chronologically(self):
        record_brief("first", {"primary_genre": "a"}, "interpret_prompt")
        record_brief("second", {"primary_genre": "b"}, "interpret_prompt")
        entries = get_briefs()
        assert entries[1]["timestamp"] >= entries[0]["timestamp"]

    def test_get_briefs_returns_copy(self):
        record_brief("techno", {"primary_genre": "techno"}, "interpret_prompt")
        returned = get_briefs()
        returned.clear()
        # Internal state should be unaffected
        assert len(get_briefs()) == 1


# ---------------------------------------------------------------------------
# clear_briefs
# ---------------------------------------------------------------------------

class TestClearBriefs:
    def test_clear_empties_log(self):
        record_brief("techno", {"primary_genre": "techno"}, "interpret_prompt")
        clear_briefs()
        assert get_briefs() == []


# ---------------------------------------------------------------------------
# interpret_prompt / interpret_prompt_to_plan record briefs
# ---------------------------------------------------------------------------

class TestInterpretPromptRecordsBrief:
    def test_interpret_prompt_records_brief(self):
        interpret_prompt(_CTX, "techno")
        briefs = get_briefs()
        assert len(briefs) == 1
        assert briefs[0]["source"] == "interpret_prompt"

    def test_interpret_prompt_to_plan_records_brief(self):
        interpret_prompt_to_plan(_CTX, "house music")
        briefs = get_briefs()
        assert len(briefs) == 1
        assert briefs[0]["source"] == "interpret_prompt_to_plan"

    def test_both_tools_record_independently(self):
        interpret_prompt(_CTX, "techno")
        interpret_prompt_to_plan(_CTX, "house music")
        assert len(get_briefs()) == 2


# ---------------------------------------------------------------------------
# list_production_briefs
# ---------------------------------------------------------------------------

class TestListProductionBriefs:
    def test_empty_session_returns_zero_count(self):
        result = json.loads(list_production_briefs(_CTX))
        assert result["count"] == 0
        assert result["briefs"] == []

    def test_returns_summary_after_interpret(self):
        interpret_prompt(_CTX, "techno")
        result = json.loads(list_production_briefs(_CTX))
        assert result["count"] == 1
        assert result["briefs"][0]["primary_genre"] == "techno"

    def test_summary_has_expected_fields(self):
        interpret_prompt(_CTX, "techno")
        result = json.loads(list_production_briefs(_CTX))
        summary = result["briefs"][0]
        expected_fields = {
            "index", "raw_prompt", "primary_genre", "bpm_range",
            "key_feel", "energy_level", "confidence", "source", "timestamp",
        }
        for field in expected_fields:
            assert field in summary, f"Missing field: {field}"

    def test_session_started_is_number(self):
        result = json.loads(list_production_briefs(_CTX))
        assert isinstance(result["session_started"], float)
