"""Smoke tests for note domain tools."""

import json

import pytest


async def test_note_tools_registered(mcp_server):
    """All 5 note tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "add_notes_to_clip",
        "get_notes",
        "remove_notes",
        "quantize_notes",
        "transpose_notes",
    }
    assert expected.issubset(names), f"Missing note tools: {expected - names}"


async def test_add_notes_returns_json(mcp_server, mock_connection):
    """add_notes_to_clip returns JSON response with note_count (not plain text f-string)."""
    mock_connection.send_command.return_value = {"note_count": 3, "clip_name": "test"}
    result = await mcp_server.call_tool(
        "add_notes_to_clip",
        {
            "track_index": 0,
            "clip_index": 0,
            "notes": [{"pitch": 60, "start_time": 0, "duration": 0.5, "velocity": 100, "mute": False}],
        },
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["note_count"] == 3
    assert data["clip_name"] == "test"


async def test_get_notes_returns_json(mcp_server, mock_connection):
    """get_notes returns JSON with notes array."""
    mock_connection.send_command.return_value = {
        "note_count": 2,
        "notes": [{"pitch": 60, "start_time": 0, "duration": 0.5, "velocity": 100, "mute": False}],
    }
    result = await mcp_server.call_tool(
        "get_notes", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["note_count"] == 2
    assert isinstance(data["notes"], list)
    mock_connection.send_command.assert_called_once_with(
        "get_notes", {"track_index": 0, "clip_index": 0}
    )


async def test_remove_notes_returns_json(mcp_server, mock_connection):
    """remove_notes returns JSON with removed_count."""
    mock_connection.send_command.return_value = {"removed_count": 3}
    result = await mcp_server.call_tool(
        "remove_notes", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["removed_count"] == 3
    mock_connection.send_command.assert_called_once_with(
        "remove_notes", {"track_index": 0, "clip_index": 0}
    )


async def test_remove_notes_optional_params(mcp_server, mock_connection):
    """remove_notes passes optional pitch/time range params to send_command."""
    mock_connection.send_command.return_value = {"removed_count": 1}
    result = await mcp_server.call_tool(
        "remove_notes",
        {"track_index": 0, "clip_index": 0, "pitch_min": 60, "pitch_max": 72},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["removed_count"] == 1
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["pitch_min"] == 60
    assert params["pitch_max"] == 72
    assert "start_time_min" not in params
    assert "start_time_max" not in params


async def test_quantize_notes_returns_json(mcp_server, mock_connection):
    """quantize_notes returns JSON with quantized_count and passes grid params."""
    mock_connection.send_command.return_value = {"quantized_count": 4}
    result = await mcp_server.call_tool(
        "quantize_notes",
        {"track_index": 0, "clip_index": 0, "grid_size": 0.5, "strength": 0.8},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["quantized_count"] == 4
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["grid_size"] == 0.5
    assert params["strength"] == 0.8


async def test_transpose_notes_returns_json(mcp_server, mock_connection):
    """transpose_notes returns JSON with transposed_count."""
    mock_connection.send_command.return_value = {"transposed_count": 4}
    result = await mcp_server.call_tool(
        "transpose_notes",
        {"track_index": 0, "clip_index": 0, "semitones": 7},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["transposed_count"] == 4
    mock_connection.send_command.assert_called_once_with(
        "transpose_notes", {"track_index": 0, "clip_index": 0, "semitones": 7}
    )


async def test_transpose_notes_error(mcp_server, mock_connection):
    """transpose_notes returns format_error on exception."""
    mock_connection.send_command.side_effect = Exception("Transposing pitch 120 by 12 would exceed MIDI range 0-127")
    result = await mcp_server.call_tool(
        "transpose_notes",
        {"track_index": 0, "clip_index": 0, "semitones": 12},
    )
    text = result[0][0].text
    assert "Error" in text
    assert "Transposing pitch 120 by 12" in text


async def test_add_notes_error(mcp_server, mock_connection):
    """add_notes_to_clip returns format_error on exception."""
    mock_connection.send_command.side_effect = Exception("Velocity 0 out of range")
    result = await mcp_server.call_tool(
        "add_notes_to_clip",
        {
            "track_index": 0,
            "clip_index": 0,
            "notes": [{"pitch": 60, "start_time": 0, "duration": 0.5, "velocity": 0, "mute": False}],
        },
    )
    text = result[0][0].text
    assert "Error" in text
    assert "Velocity 0 out of range" in text
