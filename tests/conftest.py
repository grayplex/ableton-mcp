"""Shared test fixtures for ableton-mcp test suite."""

import os
from unittest.mock import MagicMock, patch

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# All modules that import get_ableton_connection via `from ... import`
_GAC_PATCH_TARGETS = [
    "MCP_Server.connection.get_ableton_connection",
    "MCP_Server.tools.session.get_ableton_connection",
    "MCP_Server.tools.tracks.get_ableton_connection",
    "MCP_Server.tools.clips.get_ableton_connection",
    "MCP_Server.tools.transport.get_ableton_connection",
    "MCP_Server.tools.devices.get_ableton_connection",
    "MCP_Server.tools.browser.get_ableton_connection",
    "MCP_Server.tools.mixer.get_ableton_connection",
    "MCP_Server.tools.notes.get_ableton_connection",
]


@pytest.fixture
def root_dir():
    """Return the project root directory path."""
    return ROOT_DIR


@pytest.fixture
def mock_connection():
    """Mock AbletonConnection with configurable canned responses.

    Patches get_ableton_connection in every module that imports it,
    so all tool functions receive the mock connection directly.

    Usage in tests:
        def test_something(mcp_server, mock_connection):
            mock_connection.send_command.return_value = {"key": "value"}
            result = await mcp_server.call_tool("tool_name", {"param": 1})
    """
    mock = MagicMock()
    mock.send_command.return_value = {}
    patches = [patch(target, return_value=mock) for target in _GAC_PATCH_TARGETS]
    for p in patches:
        p.start()
    try:
        yield mock
    finally:
        for p in patches:
            p.stop()


@pytest.fixture
def mcp_server():
    """Return the live FastMCP server instance for in-memory testing."""
    from MCP_Server.server import mcp

    return mcp
