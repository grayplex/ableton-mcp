"""Smoke tests for transport domain tools (set_tempo, start/stop/continue playback, time signature, loop, undo/redo)."""

import json

import MCP_Server.tools.transport as transport_module


async def test_transport_tools_registered(mcp_server):
    """Original 3 transport tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "set_tempo" in names
    assert "start_playback" in names
    assert "stop_playback" in names


async def test_set_tempo_calls_send_command(mcp_server, mock_connection):
    """set_tempo invokes send_command with correct tempo value."""
    mock_connection.send_command.return_value = {"tempo": 140.0}
    result = await mcp_server.call_tool("set_tempo", {"tempo": 140.0})
    text = result[0][0].text
    assert "140" in text
    mock_connection.send_command.assert_called_once_with("set_tempo", {"tempo": 140.0})


async def test_start_playback_returns_message(mcp_server, mock_connection):
    """start_playback returns a JSON response."""
    mock_connection.send_command.return_value = {"playing": True}
    result = await mcp_server.call_tool("start_playback", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["playing"] is True


async def test_new_transport_tools_registered(mcp_server):
    """All 8 new transport tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "continue_playback" in names
    assert "stop_all_clips" in names
    assert "set_time_signature" in names
    assert "set_loop_region" in names
    assert "get_playback_position" in names
    assert "get_transport_state" in names
    assert "undo" in names
    assert "redo" in names


async def test_continue_playback_calls_send_command(mcp_server, mock_connection):
    """continue_playback invokes send_command correctly."""
    mock_connection.send_command.return_value = {"playing": True}
    result = await mcp_server.call_tool("continue_playback", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["playing"] is True
    mock_connection.send_command.assert_called_once_with("continue_playback")


async def test_stop_all_clips_calls_send_command(mcp_server, mock_connection):
    """stop_all_clips invokes send_command correctly."""
    mock_connection.send_command.return_value = {"stopped": True, "transport_playing": True}
    result = await mcp_server.call_tool("stop_all_clips", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["stopped"] is True
    assert parsed["transport_playing"] is True
    mock_connection.send_command.assert_called_once_with("stop_all_clips")


async def test_set_time_signature_calls_send_command(mcp_server, mock_connection):
    """set_time_signature invokes send_command with correct params."""
    mock_connection.send_command.return_value = {"numerator": 3, "denominator": 4}
    result = await mcp_server.call_tool("set_time_signature", {"numerator": 3, "denominator": 4})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["numerator"] == 3
    assert parsed["denominator"] == 4
    mock_connection.send_command.assert_called_once_with(
        "set_time_signature", {"numerator": 3, "denominator": 4}
    )


async def test_set_loop_region_calls_send_command(mcp_server, mock_connection):
    """set_loop_region invokes send_command with all params."""
    mock_connection.send_command.return_value = {
        "loop_enabled": True,
        "loop_start": 4.0,
        "loop_length": 8.0,
    }
    result = await mcp_server.call_tool(
        "set_loop_region", {"enabled": True, "start": 4.0, "length": 8.0}
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["loop_enabled"] is True
    assert parsed["loop_start"] == 4.0
    assert parsed["loop_length"] == 8.0
    mock_connection.send_command.assert_called_once_with(
        "set_loop_region", {"enabled": True, "start": 4.0, "length": 8.0}
    )


async def test_set_loop_region_conditional_params(mcp_server, mock_connection):
    """set_loop_region only sends non-None params."""
    mock_connection.send_command.return_value = {"loop_enabled": True}
    await mcp_server.call_tool("set_loop_region", {"enabled": True})
    mock_connection.send_command.assert_called_once_with(
        "set_loop_region", {"enabled": True}
    )


async def test_get_playback_position_returns_json(mcp_server, mock_connection):
    """get_playback_position returns position as JSON."""
    mock_connection.send_command.return_value = {"position": 12.5}
    result = await mcp_server.call_tool("get_playback_position", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["position"] == 12.5
    mock_connection.send_command.assert_called_once_with("get_playback_position")


async def test_get_transport_state_returns_json(mcp_server, mock_connection):
    """get_transport_state returns full state dict as JSON."""
    state = {
        "is_playing": True,
        "tempo": 120.0,
        "time_signature": {"numerator": 4, "denominator": 4},
        "position": 8.0,
        "loop_enabled": False,
        "loop_start": 0.0,
        "loop_length": 4.0,
    }
    mock_connection.send_command.return_value = state
    result = await mcp_server.call_tool("get_transport_state", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert "is_playing" in parsed
    assert "tempo" in parsed
    assert "time_signature" in parsed
    assert "position" in parsed
    assert "loop_enabled" in parsed
    assert "loop_start" in parsed
    assert "loop_length" in parsed
    mock_connection.send_command.assert_called_once_with("get_transport_state")


async def test_undo_calls_send_command(mcp_server, mock_connection):
    """undo invokes send_command correctly."""
    transport_module._consecutive_undo_count = 0
    mock_connection.send_command.return_value = {"undone": True}
    result = await mcp_server.call_tool("undo", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["undone"] is True
    mock_connection.send_command.assert_called_once_with("undo")


async def test_redo_calls_send_command(mcp_server, mock_connection):
    """redo invokes send_command correctly."""
    transport_module._consecutive_undo_count = 5
    mock_connection.send_command.return_value = {"redone": True}
    result = await mcp_server.call_tool("redo", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["redone"] is True
    assert transport_module._consecutive_undo_count == 0
    mock_connection.send_command.assert_called_once_with("redo")


async def test_undo_consecutive_warning(mcp_server, mock_connection):
    """undo emits warning after 3+ consecutive calls."""
    transport_module._consecutive_undo_count = 0
    mock_connection.send_command.return_value = {"undone": True}

    # First two calls -- no warning
    result1 = await mcp_server.call_tool("undo", {})
    parsed1 = json.loads(result1[0][0].text)
    assert "warning" not in parsed1

    result2 = await mcp_server.call_tool("undo", {})
    parsed2 = json.loads(result2[0][0].text)
    assert "warning" not in parsed2

    # Third call -- warning present
    result3 = await mcp_server.call_tool("undo", {})
    parsed3 = json.loads(result3[0][0].text)
    assert "warning" in parsed3
    assert "3 times consecutively" in parsed3["warning"]


# --- Phase 12: Song-level gap tools ---


async def test_song_gap_tools_registered(mcp_server):
    """All 16 new transport tools for Song-level gaps are registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "get_scale_info", "set_scale",
        "get_cue_points", "set_or_delete_cue", "jump_to_cue",
        "capture_scene", "capture_midi",
        "tap_tempo", "set_metronome", "set_groove_amount",
        "set_swing_amount", "set_clip_trigger_quantization", "set_session_record",
        "jump_by", "play_selection", "get_song_length",
    }
    missing = expected - names
    assert not missing, f"Missing tools: {missing}"


async def test_get_scale_info_calls_send_command(mcp_server, mock_connection):
    """get_scale_info invokes send_command correctly."""
    mock_connection.send_command.return_value = {
        "root_note": 0, "scale_name": "Major",
        "scale_intervals": [0, 2, 4, 5, 7, 9, 11], "scale_mode": 0,
    }
    result = await mcp_server.call_tool("get_scale_info", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["root_note"] == 0
    assert parsed["scale_name"] == "Major"
    mock_connection.send_command.assert_called_once_with("get_scale_info")


async def test_set_scale_calls_send_command(mcp_server, mock_connection):
    """set_scale invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "root_note": 2, "scale_name": "Major",
        "scale_intervals": [0, 2, 4, 5, 7, 9, 11], "scale_mode": 0,
    }
    result = await mcp_server.call_tool("set_scale", {"root_note": 2})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["root_note"] == 2
    mock_connection.send_command.assert_called_once_with("set_scale", {"root_note": 2})


async def test_get_cue_points_calls_send_command(mcp_server, mock_connection):
    """get_cue_points invokes send_command correctly."""
    mock_connection.send_command.return_value = {"cue_points": []}
    result = await mcp_server.call_tool("get_cue_points", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["cue_points"] == []
    mock_connection.send_command.assert_called_once_with("get_cue_points")


async def test_capture_scene_calls_send_command(mcp_server, mock_connection):
    """capture_scene invokes send_command correctly."""
    mock_connection.send_command.return_value = {"captured": True, "scene_count": 5}
    result = await mcp_server.call_tool("capture_scene", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["captured"] is True
    mock_connection.send_command.assert_called_once_with("capture_scene")


async def test_tap_tempo_calls_send_command(mcp_server, mock_connection):
    """tap_tempo invokes send_command correctly."""
    mock_connection.send_command.return_value = {"tapped": True, "tempo": 120.0}
    result = await mcp_server.call_tool("tap_tempo", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["tapped"] is True
    assert parsed["tempo"] == 120.0
    mock_connection.send_command.assert_called_once_with("tap_tempo")


async def test_set_metronome_calls_send_command(mcp_server, mock_connection):
    """set_metronome invokes send_command with correct params."""
    mock_connection.send_command.return_value = {"metronome": True}
    result = await mcp_server.call_tool("set_metronome", {"enabled": True})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["metronome"] is True
    mock_connection.send_command.assert_called_once_with("set_metronome", {"enabled": True})


async def test_jump_by_calls_send_command(mcp_server, mock_connection):
    """jump_by invokes send_command with correct params."""
    mock_connection.send_command.return_value = {"jumped": True, "beats": 4.0, "position": 12.0}
    result = await mcp_server.call_tool("jump_by", {"beats": 4.0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["jumped"] is True
    assert parsed["beats"] == 4.0
    mock_connection.send_command.assert_called_once_with("jump_by", {"beats": 4.0})


async def test_get_song_length_calls_send_command(mcp_server, mock_connection):
    """get_song_length invokes send_command correctly."""
    mock_connection.send_command.return_value = {"song_length": 128.0, "last_event_time": 120.0}
    result = await mcp_server.call_tool("get_song_length", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["song_length"] == 128.0
    mock_connection.send_command.assert_called_once_with("get_song_length")
