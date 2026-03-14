"""Smoke tests for track domain tools (all track CRUD, color, grouping, info)."""

import json


async def test_track_tools_registered(mcp_server):
    """All track tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "get_track_info",
        "create_midi_track",
        "set_track_name",
        "create_audio_track",
        "create_return_track",
        "create_group_track",
        "delete_track",
        "duplicate_track",
        "set_track_color",
        "set_group_fold",
        "get_all_tracks",
    }
    assert expected.issubset(names), f"Missing tools: {expected - names}"


async def test_create_midi_track_calls_send_command(mcp_server, mock_connection):
    """create_midi_track invokes send_command and returns JSON."""
    mock_connection.send_command.return_value = {"name": "MIDI Track", "index": 0, "type": "midi"}
    result = await mcp_server.call_tool("create_midi_track", {"index": -1})
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "MIDI Track"
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
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "Bass"
    assert data["index"] == 0


async def test_create_audio_track(mcp_server, mock_connection):
    """create_audio_track sends correct wire command."""
    mock_connection.send_command.return_value = {"index": 1, "name": "Audio", "type": "audio"}
    result = await mcp_server.call_tool("create_audio_track", {"index": -1})
    text = result[0][0].text
    data = json.loads(text)
    assert data["type"] == "audio"
    mock_connection.send_command.assert_called_once_with("create_audio_track", {"index": -1})


async def test_create_return_track(mcp_server, mock_connection):
    """create_return_track sends correct wire command."""
    mock_connection.send_command.return_value = {"index": 0, "name": "A-Return", "type": "return"}
    result = await mcp_server.call_tool("create_return_track", {})
    text = result[0][0].text
    data = json.loads(text)
    assert data["type"] == "return"
    mock_connection.send_command.assert_called_once_with("create_return_track", {})


async def test_create_group_track(mcp_server, mock_connection):
    """create_group_track sends correct wire command."""
    mock_connection.send_command.return_value = {"index": 0, "name": "Group", "type": "group"}
    result = await mcp_server.call_tool("create_group_track", {"index": -1})
    text = result[0][0].text
    data = json.loads(text)
    assert data["type"] == "group"
    mock_connection.send_command.assert_called_once_with(
        "create_group_track", {"index": -1, "track_indices": None}
    )


async def test_create_group_track_with_indices(mcp_server, mock_connection):
    """create_group_track parses comma-separated track_indices."""
    mock_connection.send_command.return_value = {"index": 0, "name": "Group", "type": "group"}
    result = await mcp_server.call_tool(
        "create_group_track", {"index": 0, "track_indices": "1,2,3"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["type"] == "group"
    mock_connection.send_command.assert_called_once_with(
        "create_group_track", {"index": 0, "track_indices": [1, 2, 3]}
    )


async def test_delete_track(mcp_server, mock_connection):
    """delete_track sends correct wire command with track_type."""
    mock_connection.send_command.return_value = {
        "deleted": {"name": "Bass", "type": "track", "index": 1}
    }
    result = await mcp_server.call_tool(
        "delete_track", {"track_index": 1, "track_type": "track"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["deleted"]["name"] == "Bass"
    mock_connection.send_command.assert_called_once_with(
        "delete_track", {"track_index": 1, "track_type": "track"}
    )


async def test_duplicate_track(mcp_server, mock_connection):
    """duplicate_track sends correct wire command with optional new_name."""
    mock_connection.send_command.return_value = {
        "index": 2, "name": "Lead Copy", "type": "midi"
    }
    result = await mcp_server.call_tool(
        "duplicate_track", {"track_index": 1, "new_name": "Lead Copy"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "Lead Copy"
    assert data["index"] == 2
    mock_connection.send_command.assert_called_once_with(
        "duplicate_track", {"track_index": 1, "new_name": "Lead Copy"}
    )


async def test_duplicate_track_without_name(mcp_server, mock_connection):
    """duplicate_track omits new_name when empty."""
    mock_connection.send_command.return_value = {
        "index": 2, "name": "Bass Copy", "type": "midi"
    }
    result = await mcp_server.call_tool("duplicate_track", {"track_index": 1})
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "Bass Copy"
    mock_connection.send_command.assert_called_once_with(
        "duplicate_track", {"track_index": 1}
    )


async def test_set_track_color(mcp_server, mock_connection):
    """set_track_color sends correct wire command."""
    mock_connection.send_command.return_value = {
        "index": 0, "name": "Bass", "color": "blue"
    }
    result = await mcp_server.call_tool(
        "set_track_color", {"track_index": 0, "color": "blue"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["color"] == "blue"
    mock_connection.send_command.assert_called_once_with(
        "set_track_color", {"track_index": 0, "color": "blue", "track_type": "track"}
    )


async def test_set_group_fold(mcp_server, mock_connection):
    """set_group_fold sends correct wire command."""
    mock_connection.send_command.return_value = {
        "index": 0, "name": "Drums", "folded": True
    }
    result = await mcp_server.call_tool(
        "set_group_fold", {"track_index": 0, "folded": True}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["folded"] is True
    mock_connection.send_command.assert_called_once_with(
        "set_group_fold", {"track_index": 0, "folded": True}
    )


async def test_get_all_tracks(mcp_server, mock_connection):
    """get_all_tracks returns track summary."""
    mock_connection.send_command.return_value = {
        "tracks": [{"index": 0, "name": "Bass", "type": "midi", "color": "blue"}],
        "return_tracks": [],
        "master_track": {"name": "Master", "type": "master", "color": "gray"},
    }
    result = await mcp_server.call_tool("get_all_tracks", {})
    text = result[0][0].text
    data = json.loads(text)
    assert len(data["tracks"]) == 1
    assert data["master_track"]["type"] == "master"
    mock_connection.send_command.assert_called_once_with("get_all_tracks", {})


async def test_get_track_info_with_type(mcp_server, mock_connection):
    """get_track_info passes track_type parameter."""
    mock_connection.send_command.return_value = {"name": "Master", "type": "master"}
    result = await mcp_server.call_tool(
        "get_track_info", {"track_index": 0, "track_type": "master"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["type"] == "master"
    mock_connection.send_command.assert_called_once_with(
        "get_track_info", {"track_index": 0, "track_type": "master"}
    )


async def test_get_track_info_master_no_mute_solo(mcp_server, mock_connection):
    """get_track_info for master track returns volume/panning but no mute/solo."""
    mock_connection.send_command.return_value = {
        "name": "Master",
        "type": "master",
        "volume": 0.85,
        "panning": 0.0,
        "color": "charcoal",
        "devices": [],
    }
    result = await mcp_server.call_tool(
        "get_track_info", {"track_index": 0, "track_type": "master"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "Master"
    assert data["type"] == "master"
    assert "volume" in data
    assert "panning" in data
    assert "mute" not in data
    assert "solo" not in data
    mock_connection.send_command.assert_called_once_with(
        "get_track_info", {"track_index": 0, "track_type": "master"}
    )


async def test_get_track_info_regular_track_has_mute_solo(mcp_server, mock_connection):
    """get_track_info for regular track includes mute and solo fields."""
    mock_connection.send_command.return_value = {
        "index": 0,
        "name": "Bass",
        "type": "midi",
        "volume": 0.7,
        "panning": 0.0,
        "mute": False,
        "solo": False,
        "color": "blue",
        "devices": [],
        "clip_slots": [],
    }
    result = await mcp_server.call_tool(
        "get_track_info", {"track_index": 0, "track_type": "track"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["mute"] is False
    assert data["solo"] is False
    mock_connection.send_command.assert_called_once_with(
        "get_track_info", {"track_index": 0, "track_type": "track"}
    )


async def test_set_track_name_with_type(mcp_server, mock_connection):
    """set_track_name passes track_type parameter."""
    mock_connection.send_command.return_value = {"name": "FX Send", "type": "return"}
    result = await mcp_server.call_tool(
        "set_track_name", {"track_index": 0, "name": "FX Send", "track_type": "return"}
    )
    text = result[0][0].text
    assert "FX Send" in text
    mock_connection.send_command.assert_called_once_with(
        "set_track_name", {"track_index": 0, "name": "FX Send", "track_type": "return"}
    )


async def test_set_track_name_returns_type(mcp_server, mock_connection):
    """set_track_name response includes track type for non-default types."""
    mock_connection.send_command.return_value = {"name": "My Return", "type": "return", "index": 0}
    result = await mcp_server.call_tool(
        "set_track_name", {"track_index": 0, "name": "My Return", "track_type": "return"}
    )
    text = result[0][0].text
    assert "My Return" in text
    # Verify the wire command receives track_type
    mock_connection.send_command.assert_called_once_with(
        "set_track_name", {"track_index": 0, "name": "My Return", "track_type": "return"}
    )


async def test_set_track_name_master(mcp_server, mock_connection):
    """set_track_name works for master track."""
    mock_connection.send_command.return_value = {"name": "MASTER", "type": "master"}
    result = await mcp_server.call_tool(
        "set_track_name", {"track_index": 0, "name": "MASTER", "track_type": "master"}
    )
    text = result[0][0].text
    assert "MASTER" in text
    mock_connection.send_command.assert_called_once_with(
        "set_track_name", {"track_index": 0, "name": "MASTER", "track_type": "master"}
    )
