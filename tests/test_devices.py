"""Smoke tests for device domain tools."""

import json

import pytest


async def test_device_tools_registered(mcp_server):
    """All 5 device tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "load_instrument_or_effect",
        "get_device_parameters",
        "set_device_parameter",
        "delete_device",
        "get_rack_chains",
    }
    assert expected.issubset(names), f"Missing device tools: {expected - names}"


async def test_load_instrument_calls_send_command(mcp_server, mock_connection):
    """load_instrument_or_effect invokes send_command and returns JSON with parameters."""
    mock_connection.send_command.return_value = {
        "loaded": True,
        "item_name": "Analog",
        "track_name": "1-MIDI",
        "devices": ["Analog"],
        "device_count": 1,
        "parameters": [
            {
                "index": 0,
                "name": "Device On",
                "value": 1.0,
                "min": 0.0,
                "max": 1.0,
                "is_quantized": True,
            }
        ],
    }
    result = await mcp_server.call_tool(
        "load_instrument_or_effect",
        {"track_index": 0, "uri": "query:Synths#Analog"},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["item_name"] == "Analog"
    assert "parameters" in data
    assert data["parameters"][0]["name"] == "Device On"


async def test_load_instrument_with_path(mcp_server, mock_connection):
    """load_instrument_or_effect with path param sends path to send_command."""
    mock_connection.send_command.return_value = {
        "loaded": True,
        "item_name": "Analog",
        "track_name": "1-MIDI",
        "devices": ["Analog"],
        "device_count": 1,
        "parameters": [],
    }
    result = await mcp_server.call_tool(
        "load_instrument_or_effect",
        {"track_index": 0, "path": "instruments/Analog"},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["loaded"] is True
    # Verify send_command was called with path key
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert "path" in params
    assert params["path"] == "instruments/Analog"


async def test_get_device_parameters(mcp_server, mock_connection):
    """get_device_parameters returns JSON with device_name and parameters."""
    mock_connection.send_command.return_value = {
        "device_name": "Analog",
        "device_type": "instrument",
        "class_name": "OriginalSimpler",
        "parameter_count": 1,
        "parameters": [
            {
                "index": 0,
                "name": "Device On",
                "value": 1.0,
                "min": 0.0,
                "max": 1.0,
                "is_quantized": True,
            }
        ],
    }
    result = await mcp_server.call_tool(
        "get_device_parameters",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Analog"
    assert isinstance(data["parameters"], list)
    assert data["parameters"][0]["name"] == "Device On"


async def test_get_device_parameters_chain(mcp_server, mock_connection):
    """get_device_parameters with chain params passes them to send_command."""
    mock_connection.send_command.return_value = {
        "device_name": "Simpler",
        "device_type": "instrument",
        "parameters": [],
    }
    result = await mcp_server.call_tool(
        "get_device_parameters",
        {
            "track_index": 0,
            "device_index": 0,
            "chain_index": 0,
            "chain_device_index": 0,
        },
    )
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["chain_index"] == 0
    assert params["chain_device_index"] == 0


async def test_set_device_parameter_by_name(mcp_server, mock_connection):
    """set_device_parameter by name returns JSON response."""
    mock_connection.send_command.return_value = {
        "device_name": "Analog",
        "parameter_name": "Filter Freq",
        "parameter_index": 5,
        "value": 0.5,
        "min": 0.0,
        "max": 1.0,
        "is_quantized": False,
    }
    result = await mcp_server.call_tool(
        "set_device_parameter",
        {
            "track_index": 0,
            "device_index": 0,
            "value": 0.5,
            "parameter_name": "Filter Freq",
        },
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["parameter_name"] == "Filter Freq"
    assert data["value"] == 0.5


async def test_set_device_parameter_by_index(mcp_server, mock_connection):
    """set_device_parameter by index passes parameter_index to send_command."""
    mock_connection.send_command.return_value = {
        "device_name": "Analog",
        "parameter_name": "Osc Volume",
        "parameter_index": 3,
        "value": 0.8,
    }
    result = await mcp_server.call_tool(
        "set_device_parameter",
        {
            "track_index": 0,
            "device_index": 0,
            "value": 0.8,
            "parameter_index": 3,
        },
    )
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["parameter_index"] == 3
    assert params["value"] == 0.8


async def test_set_device_parameter_clamped(mcp_server, mock_connection):
    """set_device_parameter returns warning when value is clamped."""
    mock_connection.send_command.return_value = {
        "device_name": "Analog",
        "parameter_name": "Volume",
        "parameter_index": 1,
        "value": 1.0,
        "min": 0.0,
        "max": 1.0,
        "is_quantized": False,
        "warning": "Value 1.5 clamped to max 1.0",
    }
    result = await mcp_server.call_tool(
        "set_device_parameter",
        {
            "track_index": 0,
            "device_index": 0,
            "value": 1.5,
            "parameter_name": "Volume",
        },
    )
    text = result[0][0].text
    data = json.loads(text)
    assert "warning" in data
    assert "clamped" in data["warning"]


async def test_delete_device(mcp_server, mock_connection):
    """delete_device returns JSON with deleted_device_name."""
    mock_connection.send_command.return_value = {
        "deleted_device_name": "Analog",
        "track_name": "1-MIDI",
        "track_type": "track",
        "updated_devices": [],
    }
    result = await mcp_server.call_tool(
        "delete_device",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["deleted_device_name"] == "Analog"
    assert isinstance(data["updated_devices"], list)


async def test_get_rack_chains(mcp_server, mock_connection):
    """get_rack_chains returns chains for Instrument/Effect Racks."""
    mock_connection.send_command.return_value = {
        "device_name": "Instrument Rack",
        "device_type": "rack",
        "chains": [
            {
                "index": 0,
                "name": "Chain 1",
                "devices": [
                    {
                        "index": 0,
                        "name": "Analog",
                        "type": "instrument",
                        "can_have_chains": False,
                    }
                ],
            }
        ],
    }
    result = await mcp_server.call_tool(
        "get_rack_chains",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_type"] == "rack"
    assert "chains" in data
    assert data["chains"][0]["name"] == "Chain 1"


async def test_get_rack_chains_drum(mcp_server, mock_connection):
    """get_rack_chains returns pads for Drum Racks."""
    mock_connection.send_command.return_value = {
        "device_name": "Drum Rack",
        "device_type": "drum_machine",
        "pads": [
            {
                "note": 36,
                "name": "C1",
                "chains": [
                    {
                        "name": "Chain",
                        "devices": [
                            {
                                "index": 0,
                                "name": "Simpler",
                                "type": "instrument",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    result = await mcp_server.call_tool(
        "get_rack_chains",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_type"] == "drum_machine"
    assert "pads" in data
    assert data["pads"][0]["note"] == 36


async def test_load_instrument_error(mcp_server, mock_connection):
    """load_instrument_or_effect returns format_error on exception."""
    mock_connection.send_command.side_effect = Exception("Connection lost")
    result = await mcp_server.call_tool(
        "load_instrument_or_effect",
        {"track_index": 0, "uri": "query:Synths#Analog"},
    )
    text = result[0][0].text
    assert "Error" in text
    assert "Connection lost" in text
