"""Smoke tests for routing domain tools (get/set input/output routing types)."""

import json


async def test_routing_tools_registered(mcp_server):
    """All 4 routing tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_input_routing_types" in names
    assert "set_input_routing" in names
    assert "get_output_routing_types" in names
    assert "set_output_routing" in names


async def test_get_input_routing_types(mcp_server, mock_connection):
    """get_input_routing_types returns current routing and available options."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "track_type": "track",
        "current": "Ext. In",
        "available": ["Ext. In", "No Input", "Track 2-Audio"],
        "index": 0,
    }
    result = await mcp_server.call_tool(
        "get_input_routing_types",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["current"] == "Ext. In"
    assert len(parsed["available"]) == 3
    mock_connection.send_command.assert_called_once_with(
        "get_input_routing_types",
        {"track_index": 0, "track_type": "track"},
    )


async def test_set_input_routing(mcp_server, mock_connection):
    """set_input_routing returns previous and new routing."""
    mock_connection.send_command.return_value = {
        "previous": "Ext. In",
        "current": "No Input",
        "track_name": "1-Audio",
        "track_type": "track",
        "index": 0,
    }
    result = await mcp_server.call_tool(
        "set_input_routing",
        {"track_index": 0, "routing_name": "No Input"},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["previous"] == "Ext. In"
    assert parsed["current"] == "No Input"
    mock_connection.send_command.assert_called_once_with(
        "set_input_routing",
        {"track_index": 0, "routing_name": "No Input", "track_type": "track"},
    )


async def test_get_output_routing_types(mcp_server, mock_connection):
    """get_output_routing_types returns current routing and available options."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "track_type": "track",
        "current": "Master",
        "available": ["Master", "Ext. Out", "Sends Only", "A-Reverb"],
        "index": 0,
    }
    result = await mcp_server.call_tool(
        "get_output_routing_types",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["current"] == "Master"
    assert len(parsed["available"]) == 4


async def test_set_output_routing(mcp_server, mock_connection):
    """set_output_routing returns previous and new routing."""
    mock_connection.send_command.return_value = {
        "previous": "Master",
        "current": "A-Reverb",
        "track_name": "1-Audio",
        "track_type": "track",
        "index": 0,
    }
    result = await mcp_server.call_tool(
        "set_output_routing",
        {"track_index": 0, "routing_name": "A-Reverb"},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["previous"] == "Master"
    assert parsed["current"] == "A-Reverb"


async def test_routing_with_track_type(mcp_server, mock_connection):
    """Routing tools pass track_type parameter correctly."""
    mock_connection.send_command.return_value = {
        "track_name": "A-Reverb",
        "track_type": "return",
        "current": "Ext. In",
        "available": ["Ext. In", "No Input"],
        "index": 0,
    }
    result = await mcp_server.call_tool(
        "get_input_routing_types",
        {"track_index": 0, "track_type": "return"},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["track_type"] == "return"
    mock_connection.send_command.assert_called_once_with(
        "get_input_routing_types",
        {"track_index": 0, "track_type": "return"},
    )


async def test_set_input_routing_error_handling(mcp_server, mock_connection):
    """set_input_routing returns formatted error for invalid routing name."""
    mock_connection.send_command.side_effect = Exception(
        "Routing type 'Bad Input' not found. Available: ['Ext. In', 'No Input']"
    )
    result = await mcp_server.call_tool(
        "set_input_routing",
        {"track_index": 0, "routing_name": "Bad Input"},
    )
    text = result[0][0].text
    assert "Error" in text
    assert "Bad Input" in text


async def test_get_input_routing_types_error(mcp_server, mock_connection):
    """get_input_routing_types returns formatted error for invalid track index."""
    mock_connection.send_command.side_effect = Exception(
        "Track index 99 out of range"
    )
    result = await mcp_server.call_tool(
        "get_input_routing_types",
        {"track_index": 99},
    )
    text = result[0][0].text
    assert "Error" in text


async def test_routing_channels_tools_registered(mcp_server):
    """Routing channel tools are registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_input_routing_channels" in names
    assert "get_output_routing_channels" in names


async def test_get_input_routing_channels_calls_send_command(mcp_server, mock_connection):
    """get_input_routing_channels invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "track_name": "1-Audio",
        "current": "1/2",
        "available": ["1/2", "3/4", "5/6"],
        "track_index": 0,
    }
    result = await mcp_server.call_tool(
        "get_input_routing_channels",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["current"] == "1/2"
    assert len(parsed["available"]) == 3
    mock_connection.send_command.assert_called_once_with(
        "get_input_routing_channels",
        {"track_index": 0, "track_type": "track"},
    )
