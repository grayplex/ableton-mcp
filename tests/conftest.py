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
    """Read and return all Remote Script source code.

    Concatenates __init__.py, registry.py, and all handler modules
    so grep-based tests can find patterns across the entire package.
    """
    base_dir = os.path.join(ROOT_DIR, "AbletonMCP_Remote_Script")
    sources = []

    # Main module
    init_path = os.path.join(base_dir, "__init__.py")
    with open(init_path, encoding="utf-8") as f:
        sources.append(f.read())

    # Registry
    registry_path = os.path.join(base_dir, "registry.py")
    if os.path.exists(registry_path):
        with open(registry_path, encoding="utf-8") as f:
            sources.append(f.read())

    # Handler modules
    handlers_dir = os.path.join(base_dir, "handlers")
    if os.path.isdir(handlers_dir):
        for filename in sorted(os.listdir(handlers_dir)):
            if filename.endswith(".py"):
                with open(os.path.join(handlers_dir, filename), encoding="utf-8") as f:
                    sources.append(f.read())

    return "\n".join(sources)


@pytest.fixture
def server_source():
    """Read and return the MCP server source code."""
    path = os.path.join(ROOT_DIR, "MCP_Server", "server.py")
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def connection_source():
    """Read and return the connection module source code."""
    path = os.path.join(ROOT_DIR, "MCP_Server", "connection.py")
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def protocol_source():
    """Read and return the protocol module source code."""
    path = os.path.join(ROOT_DIR, "MCP_Server", "protocol.py")
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def session_tools_source():
    """Read and return the session tools module source code."""
    path = os.path.join(ROOT_DIR, "MCP_Server", "tools", "session.py")
    with open(path, encoding="utf-8") as f:
        return f.read()
