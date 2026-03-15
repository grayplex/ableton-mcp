"""Smoke tests for session domain tools (get_connection_status, get_session_info, get_session_state)."""

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
    text = result[0][0].text
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
    text = result[0][0].text
    data = json.loads(text)
    assert data["connected"] is True
    assert data["ableton_version"] == "12.1"


async def test_session_state_registered(mcp_server):
    """get_session_state is registered as an MCP tool."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_session_state" in names


async def test_get_session_state_lightweight(mcp_server, mock_connection):
    """get_session_state returns JSON with transport and tracks."""
    mock_connection.send_command.return_value = {
        "transport": {"tempo": 120},
        "tracks": [{"name": "Track 1"}],
        "return_tracks": [],
        "master_track": {"name": "Master"},
    }
    result = await mcp_server.call_tool("get_session_state", {})
    text = result[0][0].text
    data = json.loads(text)
    assert "transport" in data
    assert data["transport"]["tempo"] == 120
    assert "tracks" in data
    assert data["tracks"][0]["name"] == "Track 1"
    assert "master_track" in data


async def test_get_session_state_detailed(mcp_server, mock_connection):
    """get_session_state with detailed=True passes it to send_command."""
    mock_connection.send_command.return_value = {
        "transport": {"tempo": 120},
        "tracks": [],
        "return_tracks": [],
        "master_track": {"name": "Master"},
    }
    result = await mcp_server.call_tool(
        "get_session_state", {"detailed": True}
    )
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["detailed"] is True
