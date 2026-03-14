"""Smoke tests for track domain tools (get_track_info, create_midi_track, set_track_name)."""

import json


async def test_track_tools_registered(mcp_server):
    """Track tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_track_info" in names
    assert "create_midi_track" in names
    assert "set_track_name" in names


async def test_create_midi_track_calls_send_command(mcp_server, mock_connection):
    """create_midi_track invokes send_command with correct command type."""
    mock_connection.send_command.return_value = {"name": "MIDI Track"}
    result = await mcp_server.call_tool("create_midi_track", {"index": -1})
    text = result[0].text
    assert "MIDI" in text
    mock_connection.send_command.assert_called_once_with(
        "create_midi_track", {"index": -1}
    )


async def test_get_track_info_returns_data(mcp_server, mock_connection):
    """get_track_info returns JSON track data from mocked response."""
    mock_connection.send_command.return_value = {
        "index": 0,
        "name": "Bass",
        "type": "midi",
    }
    result = await mcp_server.call_tool("get_track_info", {"track_index": 0})
    text = result[0].text
    data = json.loads(text)
    assert data["name"] == "Bass"
    assert data["index"] == 0
