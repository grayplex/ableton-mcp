"""Smoke tests for scene domain tools (create_scene, set_scene_name, fire_scene, delete_scene)."""

import json


async def test_scene_tools_registered(mcp_server):
    """All 4 scene tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "create_scene" in names
    assert "set_scene_name" in names
    assert "fire_scene" in names
    assert "delete_scene" in names


async def test_create_scene_calls_send_command(mcp_server, mock_connection):
    """create_scene invokes send_command with correct params."""
    mock_connection.send_command.return_value = {"index": 0, "name": "Scene 1"}
    result = await mcp_server.call_tool("create_scene", {"index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["index"] == 0
    mock_connection.send_command.assert_called_once_with("create_scene", {"index": 0})


async def test_create_scene_with_name(mcp_server, mock_connection):
    """create_scene passes name param when provided."""
    mock_connection.send_command.return_value = {"index": 0, "name": "Intro"}
    result = await mcp_server.call_tool("create_scene", {"index": 0, "name": "Intro"})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["name"] == "Intro"
    mock_connection.send_command.assert_called_once_with(
        "create_scene", {"index": 0, "name": "Intro"}
    )


async def test_set_scene_name_calls_send_command(mcp_server, mock_connection):
    """set_scene_name invokes send_command with correct params."""
    mock_connection.send_command.return_value = {"index": 0, "name": "Verse"}
    result = await mcp_server.call_tool("set_scene_name", {"scene_index": 0, "name": "Verse"})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["name"] == "Verse"
    mock_connection.send_command.assert_called_once_with(
        "set_scene_name", {"scene_index": 0, "name": "Verse"}
    )


async def test_fire_scene_calls_send_command(mcp_server, mock_connection):
    """fire_scene invokes send_command with correct params."""
    mock_connection.send_command.return_value = {"fired": True, "index": 0, "name": "Scene 1"}
    result = await mcp_server.call_tool("fire_scene", {"scene_index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["fired"] is True
    mock_connection.send_command.assert_called_once_with("fire_scene", {"scene_index": 0})


async def test_delete_scene_calls_send_command(mcp_server, mock_connection):
    """delete_scene invokes send_command with correct params."""
    mock_connection.send_command.return_value = {"deleted": True, "index": 1, "name": "Scene 2"}
    result = await mcp_server.call_tool("delete_scene", {"scene_index": 1})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["deleted"] is True
    mock_connection.send_command.assert_called_once_with("delete_scene", {"scene_index": 1})


# --- Phase 12: duplicate_scene ---


async def test_duplicate_scene_calls_send_command(mcp_server, mock_connection):
    """duplicate_scene invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "duplicated": True, "source_index": 0, "scene_count": 3,
    }
    result = await mcp_server.call_tool("duplicate_scene", {"scene_index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["duplicated"] is True
    assert parsed["source_index"] == 0
    mock_connection.send_command.assert_called_once_with(
        "duplicate_scene", {"scene_index": 0}
    )


# --- Phase 13: Scene Extended ---


async def test_scene_extended_tools_registered(mcp_server):
    """All 6 scene extended tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "set_scene_color" in names
    assert "get_scene_color" in names
    assert "set_scene_tempo" in names
    assert "set_scene_time_signature" in names
    assert "fire_scene_as_selected" in names
    assert "get_scene_is_empty" in names


async def test_set_scene_color_calls_send_command(mcp_server, mock_connection):
    """set_scene_color invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "scene_index": 0, "name": "Intro", "color": "red",
    }
    result = await mcp_server.call_tool("set_scene_color", {"scene_index": 0, "color": "red"})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["color"] == "red"
    mock_connection.send_command.assert_called_once_with(
        "set_scene_color", {"scene_index": 0, "color": "red"}
    )


async def test_get_scene_color_calls_send_command(mcp_server, mock_connection):
    """get_scene_color invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "scene_index": 0, "name": "Intro", "color": "blue", "color_index": 15,
    }
    result = await mcp_server.call_tool("get_scene_color", {"scene_index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["color"] == "blue"


async def test_set_scene_tempo_calls_send_command(mcp_server, mock_connection):
    """set_scene_tempo invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "scene_index": 0, "name": "Intro", "tempo": 140.0,
        "tempo_enabled": True,
        "note": "Scene tempo will override global tempo when this scene is fired",
    }
    result = await mcp_server.call_tool(
        "set_scene_tempo", {"scene_index": 0, "tempo": 140.0}
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["tempo"] == 140.0
    assert "override" in parsed["note"]


async def test_set_scene_time_signature_calls_send_command(mcp_server, mock_connection):
    """set_scene_time_signature invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "scene_index": 0, "name": "Bridge", "numerator": 3, "denominator": 4,
        "time_signature_enabled": True,
        "note": "Scene time signature will override global when this scene is fired",
    }
    result = await mcp_server.call_tool(
        "set_scene_time_signature", {"scene_index": 0, "numerator": 3, "denominator": 4}
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["numerator"] == 3


async def test_fire_scene_as_selected_calls_send_command(mcp_server, mock_connection):
    """fire_scene_as_selected invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "fired": True, "index": 0, "name": "Intro",
        "force_legato": False,
        "note": "Scene fired and selection advanced to next scene",
    }
    result = await mcp_server.call_tool("fire_scene_as_selected", {"scene_index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["fired"] is True


async def test_get_scene_is_empty_calls_send_command(mcp_server, mock_connection):
    """get_scene_is_empty invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "scene_index": 0, "name": "Scene 1", "is_empty": True,
    }
    result = await mcp_server.call_tool("get_scene_is_empty", {"scene_index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["is_empty"] is True


async def test_set_scene_color_error(mcp_server, mock_connection):
    """set_scene_color returns format_error on exception."""
    mock_connection.send_command.side_effect = Exception("Scene not found")
    result = await mcp_server.call_tool("set_scene_color", {"scene_index": 99, "color": "red"})
    text = result[0][0].text
    assert "Error" in text
