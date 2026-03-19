"""Smoke tests for audio clip domain tools (get/set audio clip properties)."""

import json


async def test_audio_clip_tools_registered(mcp_server):
    """Both audio clip tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_audio_clip_properties" in names
    assert "set_audio_clip_properties" in names


async def test_get_audio_clip_properties(mcp_server, mock_connection):
    """get_audio_clip_properties returns pitch, gain, warping info."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "clip_name": "Sample",
        "pitch_coarse": 0,
        "pitch_fine": 0,
        "gain": 0.630957,
        "gain_display": "0.0 dB",
        "warping": True,
        "warp_mode": "Beats",
    }
    result = await mcp_server.call_tool(
        "get_audio_clip_properties",
        {"track_index": 0, "clip_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["pitch_coarse"] == 0
    assert parsed["warping"] is True
    assert parsed["gain_display"] == "0.0 dB"
    mock_connection.send_command.assert_called_once_with(
        "get_audio_clip_properties",
        {"track_index": 0, "clip_index": 0},
    )


async def test_set_audio_clip_properties_pitch(mcp_server, mock_connection):
    """set_audio_clip_properties with pitch_coarse only sends that param."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "clip_name": "Sample",
        "changes": [{"property": "pitch_coarse", "previous": 0, "current": 5}],
    }
    result = await mcp_server.call_tool(
        "set_audio_clip_properties",
        {"track_index": 0, "clip_index": 0, "pitch_coarse": 5},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert len(parsed["changes"]) == 1
    assert parsed["changes"][0]["property"] == "pitch_coarse"
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["pitch_coarse"] == 5
    assert "pitch_fine" not in params
    assert "gain" not in params
    assert "warping" not in params


async def test_set_audio_clip_properties_gain(mcp_server, mock_connection):
    """set_audio_clip_properties with gain sends gain param."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "clip_name": "Sample",
        "changes": [
            {
                "property": "gain",
                "previous": 0.630957,
                "current": 0.8,
                "previous_display": "0.0 dB",
                "current_display": "2.1 dB",
            }
        ],
    }
    result = await mcp_server.call_tool(
        "set_audio_clip_properties",
        {"track_index": 0, "clip_index": 0, "gain": 0.8},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["changes"][0]["property"] == "gain"
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["gain"] == 0.8


async def test_set_audio_clip_properties_warping(mcp_server, mock_connection):
    """set_audio_clip_properties with warping sends warping param."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "clip_name": "Sample",
        "changes": [{"property": "warping", "previous": True, "current": False}],
    }
    result = await mcp_server.call_tool(
        "set_audio_clip_properties",
        {"track_index": 0, "clip_index": 0, "warping": False},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["changes"][0]["property"] == "warping"


async def test_set_audio_clip_properties_multiple(mcp_server, mock_connection):
    """set_audio_clip_properties with multiple params sends all of them."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "clip_name": "Sample",
        "changes": [
            {"property": "pitch_coarse", "previous": 0, "current": 3},
            {"property": "pitch_fine", "previous": 0, "current": 50},
        ],
    }
    result = await mcp_server.call_tool(
        "set_audio_clip_properties",
        {"track_index": 0, "clip_index": 0, "pitch_coarse": 3, "pitch_fine": 50},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert len(parsed["changes"]) == 2
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["pitch_coarse"] == 3
    assert params["pitch_fine"] == 50


async def test_get_audio_clip_properties_midi_error(mcp_server, mock_connection):
    """get_audio_clip_properties returns error for MIDI clips."""
    mock_connection.send_command.side_effect = Exception(
        "Clip at track 0 slot 0 is a MIDI clip, not audio."
    )
    result = await mcp_server.call_tool(
        "get_audio_clip_properties",
        {"track_index": 0, "clip_index": 0},
    )
    text = result[0][0].text
    assert "Error" in text
    assert "MIDI clip" in text


async def test_set_audio_clip_properties_error(mcp_server, mock_connection):
    """set_audio_clip_properties returns error for out of range values."""
    mock_connection.send_command.side_effect = Exception(
        "pitch_coarse 99 out of range (-48 to 48)"
    )
    result = await mcp_server.call_tool(
        "set_audio_clip_properties",
        {"track_index": 0, "clip_index": 0, "pitch_coarse": 99},
    )
    text = result[0][0].text
    assert "Error" in text
    assert "out of range" in text


async def test_warp_marker_tools_registered(mcp_server):
    """Phase 12 warp marker tools are registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "get_warp_markers",
        "insert_warp_marker",
        "move_warp_marker",
        "remove_warp_marker",
    }
    assert expected.issubset(names), f"Missing warp marker tools: {expected - names}"


async def test_get_warp_markers_calls_send_command(mcp_server, mock_connection):
    """get_warp_markers returns warp marker data."""
    mock_connection.send_command.return_value = {
        "clip_name": "Sample",
        "warp_markers": [],
    }
    result = await mcp_server.call_tool(
        "get_warp_markers", {"track_index": 0, "clip_index": 0}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert "warp_markers" in data
    mock_connection.send_command.assert_called_once_with(
        "get_warp_markers", {"track_index": 0, "clip_index": 0}
    )


async def test_insert_warp_marker_calls_send_command(mcp_server, mock_connection):
    """insert_warp_marker sends beat_time and sample_time."""
    mock_connection.send_command.return_value = {
        "inserted": True, "beat_time": 1.0, "sample_time": 44100.0,
    }
    result = await mcp_server.call_tool(
        "insert_warp_marker",
        {"track_index": 0, "clip_index": 0, "beat_time": 1.0, "sample_time": 44100.0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["inserted"] is True
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["beat_time"] == 1.0
    assert params["sample_time"] == 44100.0
