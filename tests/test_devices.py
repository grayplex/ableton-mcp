"""Smoke tests for device domain tools (load_instrument_or_effect)."""


async def test_device_tools_registered(mcp_server):
    """load_instrument_or_effect is registered as an MCP tool."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "load_instrument_or_effect" in names


async def test_load_instrument_calls_send_command(mcp_server, mock_connection):
    """load_instrument_or_effect invokes send_command and returns success message."""
    mock_connection.send_command.return_value = {
        "loaded": True,
        "item_name": "Analog",
        "track_name": "1-MIDI",
        "devices": ["Analog"],
    }
    result = await mcp_server.call_tool(
        "load_instrument_or_effect",
        {"track_index": 0, "uri": "query:Synths#Analog"},
    )
    text = result[0][0].text
    assert "Analog" in text
    assert "Loaded" in text
