"""Smoke tests for groove pool tools."""

import json


async def test_groove_tools_registered(mcp_server):
    """All groove tools are registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "list_grooves" in names
    assert "get_groove_params" in names
    assert "set_groove_params" in names


async def test_list_grooves_calls_send_command(mcp_server, mock_connection):
    """list_grooves invokes send_command correctly."""
    mock_connection.send_command.return_value = {
        "grooves": [{"index": 0, "name": "Swing 8th"}],
        "count": 1,
    }
    result = await mcp_server.call_tool("list_grooves", {})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["count"] == 1
    assert parsed["grooves"][0]["name"] == "Swing 8th"
    mock_connection.send_command.assert_called_once_with("list_grooves")


async def test_get_groove_params_calls_send_command(mcp_server, mock_connection):
    """get_groove_params invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "index": 0, "name": "Swing 8th", "base": 1,
        "base_label": "1/8", "timing_amount": 0.5,
        "quantization_amount": 0.0, "random_amount": 0.0,
        "velocity_amount": 0.0,
    }
    result = await mcp_server.call_tool("get_groove_params", {"groove_index": 0})
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["base_label"] == "1/8"
    mock_connection.send_command.assert_called_once_with(
        "get_groove_params", {"groove_index": 0}
    )


async def test_set_groove_params_calls_send_command(mcp_server, mock_connection):
    """set_groove_params invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "index": 0, "name": "Swing 8th", "base": 3,
        "base_label": "1/16", "timing_amount": 0.75,
        "quantization_amount": 0.0, "random_amount": 0.0,
        "velocity_amount": 0.0,
    }
    result = await mcp_server.call_tool(
        "set_groove_params", {"groove_index": 0, "base": 3, "timing_amount": 0.75}
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["base"] == 3
    assert parsed["timing_amount"] == 0.75
    mock_connection.send_command.assert_called_once_with(
        "set_groove_params", {"groove_index": 0, "base": 3, "timing_amount": 0.75}
    )


async def test_list_grooves_error(mcp_server, mock_connection):
    """list_grooves returns format_error on exception."""
    mock_connection.send_command.side_effect = Exception("Pool empty")
    result = await mcp_server.call_tool("list_grooves", {})
    text = result[0][0].text
    assert "Error" in text
