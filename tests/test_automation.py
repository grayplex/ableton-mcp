"""Smoke tests for automation domain tools (get_clip_envelope, insert_envelope_breakpoints, clear_clip_envelopes)."""

import json


async def test_automation_tools_registered(mcp_server):
    """All 3 automation tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_clip_envelope" in names
    assert "insert_envelope_breakpoints" in names
    assert "clear_clip_envelopes" in names


async def test_get_clip_envelope_list_mode(mcp_server, mock_connection):
    """get_clip_envelope without parameter returns list of automated parameters."""
    mock_connection.send_command.return_value = {
        "has_envelopes": True,
        "device_name": "Analog",
        "parameters_with_automation": [
            {"name": "Filter Freq", "index": 3, "min": 0.0, "max": 1.0}
        ],
    }
    result = await mcp_server.call_tool(
        "get_clip_envelope",
        {"track_index": 0, "clip_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["device_name"] == "Analog"
    assert len(parsed["parameters_with_automation"]) == 1
    mock_connection.send_command.assert_called_once_with(
        "get_clip_envelope",
        {"track_index": 0, "clip_index": 0, "device_index": 0},
    )


async def test_get_clip_envelope_detail_mode(mcp_server, mock_connection):
    """get_clip_envelope with parameter_name returns sampled breakpoint data."""
    mock_connection.send_command.return_value = {
        "parameter_name": "Filter Freq",
        "device_name": "Analog",
        "has_automation": True,
        "sample_interval": 0.25,
        "breakpoints": [
            {"time": 0.0, "value": 0.5},
            {"time": 1.0, "value": 0.8},
        ],
        "min": 0.0,
        "max": 1.0,
        "value": 0.5,
    }
    result = await mcp_server.call_tool(
        "get_clip_envelope",
        {
            "track_index": 0,
            "clip_index": 0,
            "device_index": 0,
            "parameter_name": "Filter Freq",
        },
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["has_automation"] is True
    assert len(parsed["breakpoints"]) == 2
    assert parsed["min"] == 0.0
    mock_connection.send_command.assert_called_once_with(
        "get_clip_envelope",
        {
            "track_index": 0,
            "clip_index": 0,
            "device_index": 0,
            "parameter_name": "Filter Freq",
        },
    )


async def test_insert_envelope_breakpoints(mcp_server, mock_connection):
    """insert_envelope_breakpoints sends breakpoints list to Ableton."""
    mock_connection.send_command.return_value = {
        "parameter_name": "Filter Freq",
        "device_name": "Analog",
        "breakpoints_inserted": 3,
        "total_breakpoints": 17,
    }
    breakpoints = [
        {"time": 0.0, "value": 0.0},
        {"time": 2.0, "value": 0.5},
        {"time": 4.0, "value": 1.0},
    ]
    result = await mcp_server.call_tool(
        "insert_envelope_breakpoints",
        {
            "track_index": 0,
            "clip_index": 0,
            "device_index": 0,
            "parameter_name": "Filter Freq",
            "breakpoints": breakpoints,
        },
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["breakpoints_inserted"] == 3
    call_args = mock_connection.send_command.call_args
    assert call_args[0][0] == "insert_envelope_breakpoints"
    assert len(call_args[0][1]["breakpoints"]) == 3


async def test_clear_clip_envelopes_all(mcp_server, mock_connection):
    """clear_clip_envelopes without device_index clears all envelopes."""
    mock_connection.send_command.return_value = {
        "cleared": "all",
        "envelopes_cleared": "all",
    }
    result = await mcp_server.call_tool(
        "clear_clip_envelopes",
        {"track_index": 0, "clip_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["cleared"] == "all"
    mock_connection.send_command.assert_called_once_with(
        "clear_clip_envelopes",
        {"track_index": 0, "clip_index": 0},
    )


async def test_clear_clip_envelopes_single(mcp_server, mock_connection):
    """clear_clip_envelopes with device_index and parameter clears single envelope."""
    mock_connection.send_command.return_value = {
        "cleared": "Filter Freq",
        "device_name": "Analog",
        "envelopes_cleared": 1,
    }
    result = await mcp_server.call_tool(
        "clear_clip_envelopes",
        {
            "track_index": 0,
            "clip_index": 0,
            "device_index": 0,
            "parameter_name": "Filter Freq",
        },
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["envelopes_cleared"] == 1
    assert parsed["cleared"] == "Filter Freq"
    call_args = mock_connection.send_command.call_args
    assert call_args[0][1]["device_index"] == 0
    assert call_args[0][1]["parameter_name"] == "Filter Freq"


async def test_get_clip_envelope_error_handling(mcp_server, mock_connection):
    """get_clip_envelope returns formatted error on exception."""
    mock_connection.send_command.side_effect = Exception(
        "Track index 99 out of range"
    )
    result = await mcp_server.call_tool(
        "get_clip_envelope",
        {"track_index": 99, "clip_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    assert "Error" in text
    assert "Track index 99 out of range" in text
