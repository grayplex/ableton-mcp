"""Smoke tests for transport domain tools (set_tempo, start_playback, stop_playback)."""


async def test_transport_tools_registered(mcp_server):
    """Transport tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "set_tempo" in names
    assert "start_playback" in names
    assert "stop_playback" in names


async def test_set_tempo_calls_send_command(mcp_server, mock_connection):
    """set_tempo invokes send_command with correct tempo value."""
    mock_connection.send_command.return_value = {}
    result = await mcp_server.call_tool("set_tempo", {"tempo": 140.0})
    text = result[0].text
    assert "140" in text
    mock_connection.send_command.assert_called_once_with("set_tempo", {"tempo": 140.0})


async def test_start_playback_returns_message(mcp_server, mock_connection):
    """start_playback returns a confirmation message."""
    mock_connection.send_command.return_value = {}
    result = await mcp_server.call_tool("start_playback", {})
    text = result[0].text
    assert "Started playback" in text
