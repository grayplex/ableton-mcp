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
