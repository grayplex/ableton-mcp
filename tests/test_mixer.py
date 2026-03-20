"""Smoke tests for mixer domain tools."""

import json


async def test_mixer_tools_registered(mcp_server):
    """All mixer tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "set_track_volume",
        "set_track_pan",
        "set_track_mute",
        "set_track_solo",
        "set_track_arm",
        "set_send_level",
    }
    assert expected.issubset(names), f"Missing tools: {expected - names}"


async def test_set_track_volume(mcp_server, mock_connection):
    """set_track_volume sends correct wire command."""
    mock_connection.send_command.return_value = {
        "volume": 0.75, "volume_db": "-2.5 dB", "name": "Bass", "type": "track", "index": 0
    }
    result = await mcp_server.call_tool("set_track_volume", {"track_index": 0, "volume": 0.75})
    text = result[0][0].text
    data = json.loads(text)
    assert data["volume"] == 0.75
    assert "volume_db" in data
    mock_connection.send_command.assert_called_once_with(
        "set_track_volume", {"track_index": 0, "volume": 0.75, "track_type": "track"}
    )


async def test_set_track_volume_master(mcp_server, mock_connection):
    """set_track_volume works with track_type=master (MIX-07)."""
    mock_connection.send_command.return_value = {
        "volume": 0.85, "volume_db": "-1.4 dB", "name": "Master", "type": "master"
    }
    result = await mcp_server.call_tool(
        "set_track_volume", {"track_index": 0, "volume": 0.85, "track_type": "master"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["type"] == "master"
    assert "index" not in data
    mock_connection.send_command.assert_called_once_with(
        "set_track_volume", {"track_index": 0, "volume": 0.85, "track_type": "master"}
    )


async def test_set_track_volume_return(mcp_server, mock_connection):
    """set_track_volume works with track_type=return (MIX-08)."""
    mock_connection.send_command.return_value = {
        "volume": 0.6, "volume_db": "-4.4 dB", "name": "Reverb", "type": "return", "index": 0
    }
    result = await mcp_server.call_tool(
        "set_track_volume", {"track_index": 0, "volume": 0.6, "track_type": "return"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["type"] == "return"
    mock_connection.send_command.assert_called_once_with(
        "set_track_volume", {"track_index": 0, "volume": 0.6, "track_type": "return"}
    )


async def test_set_track_pan(mcp_server, mock_connection):
    """set_track_pan sends correct wire command."""
    mock_connection.send_command.return_value = {
        "pan": -0.5, "pan_label": "50% left", "name": "Bass", "type": "track", "index": 0
    }
    result = await mcp_server.call_tool("set_track_pan", {"track_index": 0, "pan": -0.5})
    text = result[0][0].text
    data = json.loads(text)
    assert data["pan"] == -0.5
    assert data["pan_label"] == "50% left"
    mock_connection.send_command.assert_called_once_with(
        "set_track_pan", {"track_index": 0, "pan": -0.5, "track_type": "track"}
    )


async def test_set_track_pan_return(mcp_server, mock_connection):
    """set_track_pan works with track_type=return (MIX-08)."""
    mock_connection.send_command.return_value = {
        "pan": 0.0, "pan_label": "center", "name": "Delay", "type": "return", "index": 1
    }
    result = await mcp_server.call_tool(
        "set_track_pan", {"track_index": 1, "pan": 0.0, "track_type": "return"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["pan_label"] == "center"
    mock_connection.send_command.assert_called_once_with(
        "set_track_pan", {"track_index": 1, "pan": 0.0, "track_type": "return"}
    )


async def test_set_track_mute(mcp_server, mock_connection):
    """set_track_mute sends correct wire command."""
    mock_connection.send_command.return_value = {
        "mute": True, "name": "Bass", "type": "track", "index": 0
    }
    result = await mcp_server.call_tool(
        "set_track_mute", {"track_index": 0, "mute": True}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["mute"] is True
    mock_connection.send_command.assert_called_once_with(
        "set_track_mute", {"track_index": 0, "mute": True, "track_type": "track"}
    )


async def test_set_track_solo(mcp_server, mock_connection):
    """set_track_solo sends correct wire command."""
    mock_connection.send_command.return_value = {
        "solo": True, "name": "Lead", "type": "track", "index": 1
    }
    result = await mcp_server.call_tool(
        "set_track_solo", {"track_index": 1, "solo": True}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["solo"] is True
    mock_connection.send_command.assert_called_once_with(
        "set_track_solo",
        {"track_index": 1, "solo": True, "track_type": "track", "exclusive": False},
    )


async def test_set_track_solo_exclusive(mcp_server, mock_connection):
    """set_track_solo passes exclusive parameter."""
    mock_connection.send_command.return_value = {
        "solo": True, "name": "Lead", "type": "track", "index": 1
    }
    result = await mcp_server.call_tool(
        "set_track_solo", {"track_index": 1, "solo": True, "exclusive": True}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["solo"] is True
    mock_connection.send_command.assert_called_once_with(
        "set_track_solo",
        {"track_index": 1, "solo": True, "track_type": "track", "exclusive": True},
    )


async def test_set_track_arm(mcp_server, mock_connection):
    """set_track_arm sends correct wire command."""
    mock_connection.send_command.return_value = {
        "arm": True, "name": "Guitar", "type": "track", "index": 2
    }
    result = await mcp_server.call_tool(
        "set_track_arm", {"track_index": 2, "arm": True}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["arm"] is True
    mock_connection.send_command.assert_called_once_with(
        "set_track_arm", {"track_index": 2, "arm": True, "track_type": "track"}
    )


async def test_set_send_level(mcp_server, mock_connection):
    """set_send_level sends correct wire command."""
    mock_connection.send_command.return_value = {
        "send_level": 0.5, "send_db": "-6.0 dB",
        "return_index": 0, "return_name": "Reverb",
        "name": "Bass", "type": "track", "index": 0,
    }
    result = await mcp_server.call_tool(
        "set_send_level", {"track_index": 0, "return_index": 0, "level": 0.5}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["send_level"] == 0.5
    assert data["return_name"] == "Reverb"
    mock_connection.send_command.assert_called_once_with(
        "set_send_level",
        {"track_index": 0, "return_index": 0, "level": 0.5, "track_type": "track"},
    )


async def test_set_track_volume_error_returns_format_error(mcp_server, mock_connection):
    """set_track_volume returns format_error on exception."""
    mock_connection.send_command.side_effect = Exception("Track not found")
    result = await mcp_server.call_tool("set_track_volume", {"track_index": 99, "volume": 0.5})
    text = result[0][0].text
    assert "Error" in text
    assert "track volume" in text.lower() or "Track not found" in text


# --- Phase 13: Mixer Extended ---


async def test_mixer_extended_tools_registered(mcp_server):
    """All 3 mixer extended tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "set_crossfader" in names
    assert "set_crossfade_assign" in names
    assert "get_panning_mode" in names


async def test_set_crossfader_calls_send_command(mcp_server, mock_connection):
    """set_crossfader invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "crossfader": 0.5, "min": 0.0, "max": 1.0,
    }
    result = await mcp_server.call_tool("set_crossfader", {"value": 0.5})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["crossfader"] == 0.5


async def test_set_crossfade_assign_calls_send_command(mcp_server, mock_connection):
    """set_crossfade_assign invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "crossfade_assign": 0, "assign_label": "A",
        "name": "Bass", "type": "track", "index": 0,
    }
    result = await mcp_server.call_tool(
        "set_crossfade_assign", {"track_index": 0, "assign": 0}
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["assign_label"] == "A"


async def test_get_panning_mode_calls_send_command(mcp_server, mock_connection):
    """get_panning_mode invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "panning_mode": 0, "mode_label": "Stereo",
        "name": "Bass", "type": "track", "index": 0,
    }
    result = await mcp_server.call_tool("get_panning_mode", {"track_index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["mode_label"] == "Stereo"


async def test_set_crossfader_error(mcp_server, mock_connection):
    """set_crossfader returns format_error on exception."""
    mock_connection.send_command.side_effect = Exception("Connection lost")
    result = await mcp_server.call_tool("set_crossfader", {"value": 0.5})
    text = result[0][0].text
    assert "Error" in text
