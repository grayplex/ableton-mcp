"""Smoke tests for clip domain tools."""

import json


async def test_clip_tools_registered(mcp_server):
    """All 10 clip tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "create_clip",
        "add_notes_to_clip",
        "set_clip_name",
        "fire_clip",
        "stop_clip",
        "get_clip_info",
        "delete_clip",
        "duplicate_clip",
        "set_clip_color",
        "set_clip_loop",
    }
    assert expected.issubset(names), f"Missing clip tools: {expected - names}"


async def test_create_clip_returns_json(mcp_server, mock_connection):
    """create_clip returns JSON response (not plain text)."""
    mock_connection.send_command.return_value = {"name": "clip", "length": 4.0}
    result = await mcp_server.call_tool(
        "create_clip", {"track_index": 0, "clip_index": 0, "length": 4.0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "clip"
    assert data["length"] == 4.0
    mock_connection.send_command.assert_called_once_with(
        "create_clip", {"track_index": 0, "clip_index": 0, "length": 4.0}
    )


async def test_get_clip_info_returns_json(mcp_server, mock_connection):
    """get_clip_info returns JSON with clip details."""
    mock_connection.send_command.return_value = {
        "has_clip": True, "name": "My Clip", "length": 4.0, "color": "red", "color_index": 2
    }
    result = await mcp_server.call_tool(
        "get_clip_info", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["has_clip"] is True
    assert data["name"] == "My Clip"
    mock_connection.send_command.assert_called_once_with(
        "get_clip_info", {"track_index": 0, "clip_index": 0}
    )


async def test_get_clip_info_empty_slot(mcp_server, mock_connection):
    """get_clip_info returns empty slot status."""
    mock_connection.send_command.return_value = {
        "has_clip": False, "slot_index": 0, "track_index": 0, "track_name": "Track"
    }
    result = await mcp_server.call_tool(
        "get_clip_info", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["has_clip"] is False
    assert data["track_name"] == "Track"
    mock_connection.send_command.assert_called_once_with(
        "get_clip_info", {"track_index": 0, "clip_index": 0}
    )


async def test_delete_clip_calls_send_command(mcp_server, mock_connection):
    """delete_clip sends correct wire command and returns JSON."""
    mock_connection.send_command.return_value = {"deleted": True, "clip_name": "Deleted Clip"}
    result = await mcp_server.call_tool(
        "delete_clip", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["deleted"] is True
    assert data["clip_name"] == "Deleted Clip"
    mock_connection.send_command.assert_called_once_with(
        "delete_clip", {"track_index": 0, "clip_index": 0}
    )


async def test_duplicate_clip_calls_send_command(mcp_server, mock_connection):
    """duplicate_clip passes all 4 index params to send_command."""
    mock_connection.send_command.return_value = {
        "name": "Copy", "length": 4.0, "target_track_index": 1, "target_clip_index": 0
    }
    result = await mcp_server.call_tool(
        "duplicate_clip", {
            "track_index": 0, "clip_index": 0,
            "target_track_index": 1, "target_clip_index": 0,
        }
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "Copy"
    mock_connection.send_command.assert_called_once_with(
        "duplicate_clip", {
            "track_index": 0, "clip_index": 0,
            "target_track_index": 1, "target_clip_index": 0,
        }
    )


async def test_set_clip_color_calls_send_command(mcp_server, mock_connection):
    """set_clip_color sends color name and returns JSON."""
    mock_connection.send_command.return_value = {"name": "Clip", "color": "red", "color_index": 2}
    result = await mcp_server.call_tool(
        "set_clip_color", {"track_index": 0, "clip_index": 0, "color": "red"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["color"] == "red"
    mock_connection.send_command.assert_called_once_with(
        "set_clip_color", {"track_index": 0, "clip_index": 0, "color": "red"}
    )


async def test_set_clip_loop_calls_send_command(mcp_server, mock_connection):
    """set_clip_loop sends provided params and returns JSON with all loop values."""
    mock_connection.send_command.return_value = {
        "loop_enabled": True, "loop_start": 0.0, "loop_end": 8.0,
        "start_marker": 0.0, "end_marker": 8.0,
    }
    result = await mcp_server.call_tool(
        "set_clip_loop", {"track_index": 0, "clip_index": 0, "enabled": True, "loop_end": 8.0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["loop_enabled"] is True
    assert data["loop_end"] == 8.0
    # Verify params include enabled and loop_end but NOT loop_start (not provided)
    call_args = mock_connection.send_command.call_args
    assert call_args[0][0] == "set_clip_loop"
    params = call_args[0][1]
    assert "enabled" in params
    assert "loop_end" in params
    assert "loop_start" not in params


async def test_set_clip_loop_omits_none_params(mcp_server, mock_connection):
    """set_clip_loop only sends non-None params to send_command."""
    mock_connection.send_command.return_value = {
        "loop_enabled": True, "loop_start": 2.0, "loop_end": 4.0,
        "start_marker": 0.0, "end_marker": 4.0,
    }
    result = await mcp_server.call_tool(
        "set_clip_loop", {"track_index": 0, "clip_index": 0, "loop_start": 2.0}
    )
    text = result[0][0].text
    assert "loop_start" in text
    # Verify only track_index, clip_index, loop_start sent
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params == {"track_index": 0, "clip_index": 0, "loop_start": 2.0}
    assert "enabled" not in params
    assert "loop_end" not in params
    assert "start_marker" not in params
    assert "end_marker" not in params


async def test_fire_clip_returns_json(mcp_server, mock_connection):
    """fire_clip returns JSON response (not plain text)."""
    mock_connection.send_command.return_value = {
        "fired": True, "is_playing": True, "clip_name": "Clip"
    }
    result = await mcp_server.call_tool(
        "fire_clip", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["fired"] is True
    assert data["clip_name"] == "Clip"
    mock_connection.send_command.assert_called_once_with(
        "fire_clip", {"track_index": 0, "clip_index": 0}
    )


async def test_stop_clip_returns_json(mcp_server, mock_connection):
    """stop_clip returns JSON response (not plain text)."""
    mock_connection.send_command.return_value = {"stopped": True, "clip_name": "Clip"}
    result = await mcp_server.call_tool(
        "stop_clip", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["stopped"] is True
    assert data["clip_name"] == "Clip"
    mock_connection.send_command.assert_called_once_with(
        "stop_clip", {"track_index": 0, "clip_index": 0}
    )


async def test_clip_tool_error_handling(mcp_server, mock_connection):
    """Clip tools return format_error on exception."""
    mock_connection.send_command.side_effect = Exception("No clip in slot")
    result = await mcp_server.call_tool(
        "get_clip_info", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    assert "Error" in text
    assert "No clip in slot" in text


async def test_clip_gap_tools_registered(mcp_server):
    """Phase 12 clip gap tools are registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "set_clip_launch_settings",
        "get_clip_launch_settings",
        "set_clip_muted",
        "crop_clip",
        "duplicate_clip_loop",
        "duplicate_clip_region",
    }
    assert expected.issubset(names), f"Missing clip gap tools: {expected - names}"


async def test_set_clip_launch_settings_calls_send_command(mcp_server, mock_connection):
    """set_clip_launch_settings sends launch_mode param correctly."""
    mock_connection.send_command.return_value = {
        "clip_name": "Clip", "launch_mode": 0,
        "launch_quantization": 0, "legato": False, "velocity_amount": 0.0,
    }
    result = await mcp_server.call_tool(
        "set_clip_launch_settings",
        {"track_index": 0, "clip_index": 0, "launch_mode": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["launch_mode"] == 0
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["launch_mode"] == 0


async def test_set_clip_muted_calls_send_command(mcp_server, mock_connection):
    """set_clip_muted sends muted param correctly."""
    mock_connection.send_command.return_value = {"clip_name": "Clip", "muted": True}
    result = await mcp_server.call_tool(
        "set_clip_muted",
        {"track_index": 0, "clip_index": 0, "muted": True},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["muted"] is True
    mock_connection.send_command.assert_called_once_with(
        "set_clip_muted", {"track_index": 0, "clip_index": 0, "muted": True}
    )


async def test_crop_clip_calls_send_command(mcp_server, mock_connection):
    """crop_clip sends correct command and returns JSON."""
    mock_connection.send_command.return_value = {
        "cropped": True, "clip_name": "Clip", "length": 4.0,
    }
    result = await mcp_server.call_tool(
        "crop_clip", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["cropped"] is True
    mock_connection.send_command.assert_called_once_with(
        "crop_clip", {"track_index": 0, "clip_index": 0}
    )
