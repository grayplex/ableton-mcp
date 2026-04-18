"""Shared test fixtures for ableton-mcp test suite."""

import ast
import os
from unittest.mock import MagicMock, patch

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _discover_gac_patch_targets() -> list[str]:
    """Return patch target strings for every module that imports get_ableton_connection.

    Scans all .py files under MCP_Server/ with ast.parse (no code execution)
    and emits "<module>.get_ableton_connection" for any file containing:

        from MCP_Server.connection import ... get_ableton_connection ...

    The source definition site (MCP_Server.connection) is always included so
    that code using attribute-access style is also covered.
    """
    targets = {"MCP_Server.connection.get_ableton_connection"}

    mcp_root = os.path.join(ROOT_DIR, "MCP_Server")
    for dirpath, _dirs, filenames in os.walk(mcp_root):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, filename)
            rel = os.path.relpath(filepath, ROOT_DIR)
            # e.g. MCP_Server/tools/clips.py → MCP_Server.tools.clips
            module = rel.replace(os.sep, ".")[:-3]
            if module.endswith(".__init__"):
                module = module[:-9]

            try:
                with open(filepath, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read(), filename=filepath)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.module != "MCP_Server.connection":
                    continue
                if any(alias.name == "get_ableton_connection" for alias in node.names):
                    targets.add(f"{module}.get_ableton_connection")
                    break

    return sorted(targets)


_GAC_PATCH_TARGETS = _discover_gac_patch_targets()


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
