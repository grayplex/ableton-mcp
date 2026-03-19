"""Smoke tests for arrangement domain tools."""

import json


async def test_arrangement_tools_registered(mcp_server):
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "create_arrangement_midi_clip" in names
    assert "create_arrangement_audio_clip" in names
    assert "get_arrangement_clips" in names
    assert "duplicate_clip_to_arrangement" in names


async def test_create_arrangement_midi_clip_calls_send_command(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {
        "created": True,
        "track_name": "1-MIDI",
        "start_time": 0.0,
        "length": 4.0,
    }
    result = await mcp_server.call_tool(
        "create_arrangement_midi_clip",
        {"track_index": 0, "start_time": 0.0, "length": 4.0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["created"] is True
    mock_connection.send_command.assert_called_once_with(
        "create_arrangement_midi_clip",
        {"track_index": 0, "start_time": 0.0, "length": 4.0, "track_type": "track"},
    )


async def test_get_arrangement_clips_calls_send_command(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {
        "track_name": "1-MIDI",
        "clips": [],
    }
    result = await mcp_server.call_tool(
        "get_arrangement_clips",
        {"track_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["clips"] == []
    mock_connection.send_command.assert_called_once_with(
        "get_arrangement_clips",
        {"track_index": 0, "track_type": "track"},
    )


async def test_duplicate_clip_to_arrangement_calls_send_command(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {
        "duplicated": True,
        "clip_name": "Clip 1",
        "arrangement_time": 8.0,
    }
    result = await mcp_server.call_tool(
        "duplicate_clip_to_arrangement",
        {"track_index": 0, "clip_index": 0, "arrangement_time": 8.0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["duplicated"] is True
    mock_connection.send_command.assert_called_once_with(
        "duplicate_clip_to_arrangement",
        {"track_index": 0, "clip_index": 0, "arrangement_time": 8.0},
    )
