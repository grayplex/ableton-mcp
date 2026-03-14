"""Smoke tests for session domain tools (get_connection_status, get_session_info)."""

import json


async def test_session_tools_registered(mcp_server):
    """get_connection_status and get_session_info are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_connection_status" in names
    assert "get_session_info" in names


async def test_get_session_info_returns_data(mcp_server, mock_connection):
    """get_session_info returns JSON with session fields from mocked response."""
    mock_connection.send_command.return_value = {
        "tempo": 120.0,
        "track_count": 4,
        "tracks": ["Bass", "Drums", "Keys", "Lead"],
    }
    result = await mcp_server.call_tool("get_session_info", {})
    text = result[0].text
    data = json.loads(text)
    assert data["tempo"] == 120.0
    assert data["track_count"] == 4


async def test_get_connection_status_returns_status(mcp_server, mock_connection):
    """get_connection_status returns JSON with connected=True from mocked response."""
    mock_connection.send_command.side_effect = [
        {"ableton_version": "12.1"},  # ping response
        {"tempo": 120.0, "track_count": 4, "return_track_count": 2},  # session info
    ]
    result = await mcp_server.call_tool("get_connection_status", {})
    text = result[0].text
    data = json.loads(text)
    assert data["connected"] is True
    assert data["ableton_version"] == "12.1"
