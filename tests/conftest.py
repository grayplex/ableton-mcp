"""Shared test fixtures for the ableton-mcp test suite."""

import os

import pytest

# Project root directory (one level up from tests/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def root_dir():
    """Return the project root directory path."""
    return ROOT_DIR


@pytest.fixture
def remote_script_source():
    """Read and return the Remote Script source code."""
    path = os.path.join(ROOT_DIR, "AbletonMCP_Remote_Script", "__init__.py")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def server_source():
    """Read and return the MCP server source code."""
    path = os.path.join(ROOT_DIR, "MCP_Server", "server.py")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
