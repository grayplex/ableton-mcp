"""Smoke tests for clip domain tools."""


async def test_clip_tools_registered(mcp_server):
    """All 5 clip tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {"create_clip", "add_notes_to_clip", "set_clip_name", "fire_clip", "stop_clip"}
    assert expected.issubset(names), f"Missing clip tools: {expected - names}"


async def test_create_clip_calls_send_command(mcp_server, mock_connection):
    """create_clip invokes send_command with correct parameters."""
    mock_connection.send_command.return_value = {}
    result = await mcp_server.call_tool(
        "create_clip", {"track_index": 0, "clip_index": 0, "length": 4.0}
    )
    text = result[0].text
    assert "Created" in text
    mock_connection.send_command.assert_called_once_with(
        "create_clip", {"track_index": 0, "clip_index": 0, "length": 4.0}
    )


async def test_fire_clip_returns_success(mcp_server, mock_connection):
    """fire_clip returns a success message."""
    mock_connection.send_command.return_value = {}
    result = await mcp_server.call_tool(
        "fire_clip", {"track_index": 0, "clip_index": 0}
    )
    text = result[0].text
    assert "Started playing" in text
