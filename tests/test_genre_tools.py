"""Tests for genre blueprint MCP tool wrappers (list + get).

These tests call the tool functions directly (ctx=None) to verify
the wrapper logic: JSON serialization, section filtering, subgenre
resolution, and error formatting.

The mcp package is not available in the test environment, so we mock
the server module and FastMCP decorator before importing the tools.
"""

import json
import sys
import types
from unittest.mock import MagicMock

import pytest

# Mock the mcp module hierarchy so genres.py can be imported without mcp installed
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

from MCP_Server.tools.genres import get_genre_blueprint, list_genre_blueprints  # noqa: E402


class TestListGenreBlueprints:
    """list_genre_blueprints tool returns discovery metadata."""

    def test_returns_valid_json(self):
        """Tool returns a parseable JSON string."""
        result = list_genre_blueprints(None)
        genres = json.loads(result)
        assert isinstance(genres, list)
        assert len(genres) > 0

    def test_entries_have_required_keys(self):
        """Each genre entry has id, name, bpm_range, subgenres."""
        genres = json.loads(list_genre_blueprints(None))
        for entry in genres:
            assert "id" in entry
            assert "name" in entry
            assert "bpm_range" in entry
            assert "subgenres" in entry

    def test_house_in_results(self):
        """House genre is discoverable via list tool."""
        genres = json.loads(list_genre_blueprints(None))
        genre_ids = [g["id"] for g in genres]
        assert "house" in genre_ids


class TestGetGenreBlueprint:
    """get_genre_blueprint tool returns blueprint data with filtering."""

    def test_full_blueprint(self):
        """Full blueprint has all 6 dimension keys."""
        result = json.loads(get_genre_blueprint(None, genre="house"))
        for dim in [
            "instrumentation", "harmony", "rhythm",
            "arrangement", "mixing", "production_tips",
        ]:
            assert dim in result, f"Missing dimension: {dim}"

    def test_section_filter(self):
        """Section filter returns only requested dimensions plus metadata."""
        result = json.loads(
            get_genre_blueprint(None, genre="house", sections=["harmony", "rhythm"])
        )
        assert "harmony" in result
        assert "rhythm" in result
        assert "id" in result
        assert "name" in result
        assert "bpm_range" in result
        # Excluded sections must be absent
        assert "instrumentation" not in result
        assert "arrangement" not in result
        assert "mixing" not in result
        assert "production_tips" not in result

    def test_subgenre(self):
        """Subgenre parameter returns merged data with overridden BPM."""
        result = json.loads(
            get_genre_blueprint(None, genre="house", subgenre="deep_house")
        )
        assert result["bpm_range"] == [118, 124]

    def test_alias_resolution(self):
        """Alias 'deep house' resolves to house/deep_house subgenre (D-06)."""
        result = json.loads(get_genre_blueprint(None, genre="deep house"))
        assert result["bpm_range"] == [118, 124]

    def test_unknown_genre(self):
        """Unknown genre returns format_error string starting with 'Error:'."""
        result = get_genre_blueprint(None, genre="nonexistent_genre")
        assert result.startswith("Error:")

    def test_invalid_section_ignored(self):
        """Invalid section names are silently ignored; valid ones returned."""
        result = json.loads(
            get_genre_blueprint(None, genre="house", sections=["harmony", "bogus_section"])
        )
        assert "harmony" in result
        assert "bogus_section" not in result
        assert "id" in result

    def test_all_invalid_sections(self):
        """All invalid sections returns error with suggestion."""
        result = get_genre_blueprint(
            None, genre="house", sections=["bogus1", "bogus2"]
        )
        assert result.startswith("Error:")
        assert "valid sections" in result.lower() or "Valid sections" in result

    def test_metadata_keys_in_filtered_result(self):
        """Filtered result always includes id, name, bpm_range."""
        result = json.loads(
            get_genre_blueprint(None, genre="house", sections=["mixing"])
        )
        assert "id" in result
        assert "name" in result
        assert "bpm_range" in result
        assert "mixing" in result
