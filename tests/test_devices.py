"""Smoke tests for device domain tools."""

import json

import pytest


async def test_device_tools_registered(mcp_server):
    """All device tools (original + 34 new LOM gap tools) are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "load_instrument_or_effect",
        "get_device_parameters",
        "set_device_parameter",
        "delete_device",
        "get_rack_chains",
        # Quick Task: LOM gaps - 34 new tools
        "get_wavetable_info",
        "set_wavetable_oscillator",
        "set_wavetable_voice_config",
        "add_wavetable_modulation",
        "set_wavetable_modulation_value",
        "get_wavetable_modulation_value",
        "get_compressor_sidechain",
        "set_compressor_sidechain",
        "get_rack_variations",
        "rack_variation_action",
        "rack_macro_action",
        "insert_rack_chain",
        "copy_drum_pad",
        "get_drum_chain_config",
        "set_drum_chain_config",
        "get_parameter_automation_state",
        "re_enable_parameter_automation",
        "get_drift_mod_matrix",
        "set_drift_mod_matrix",
        "get_looper_info",
        "looper_action",
        "looper_export_to_clip_slot",
        "get_spectral_resonator_info",
        "set_spectral_resonator_config",
        "get_eq8_info",
        "set_eq8_mode",
        "get_take_lanes",
        "get_take_lane_clips",
        "create_take_lane_clip",
        "get_tuning_system",
        "set_tuning_system",
        "set_chain_mute_solo",
        "set_chain_name_color",
        "get_chain_info",
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


async def test_insert_device_tool_registered(mcp_server):
    """insert_device and move_device tools are registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "insert_device" in names
    assert "move_device" in names


async def test_insert_device_calls_send_command(mcp_server, mock_connection):
    """insert_device invokes send_command with correct params."""
    mock_connection.send_command.return_value = {
        "inserted": True,
        "device_name": "Wavetable",
        "position": 0,
        "track_name": "1-MIDI",
    }
    result = await mcp_server.call_tool(
        "insert_device",
        {"track_index": 0, "device_name": "Wavetable", "position": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["inserted"] is True
    mock_connection.send_command.assert_called_once_with(
        "insert_device",
        {"track_index": 0, "device_name": "Wavetable", "position": 0, "track_type": "track"},
    )


async def test_move_device_calls_send_command(mcp_server, mock_connection):
    """move_device invokes send_command with source/target params."""
    mock_connection.send_command.return_value = {
        "moved": True,
        "device_name": "Compressor",
        "target_track": "2-Audio",
        "position": 1,
    }
    result = await mcp_server.call_tool(
        "move_device",
        {
            "source_track_index": 0,
            "device_index": 0,
            "target_track_index": 1,
            "target_position": 1,
        },
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["moved"] is True
    mock_connection.send_command.assert_called_once_with(
        "move_device",
        {
            "source_track_index": 0,
            "device_index": 0,
            "target_track_index": 1,
            "target_position": 1,
            "source_track_type": "track",
            "target_track_type": "track",
        },
    )


# --- Phase 13: Simpler, DrumPad, Plugin, A/B ---


async def test_device_extended_tools_registered(mcp_server):
    """All 15 new device extended tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "crop_simpler",
        "reverse_simpler",
        "warp_simpler",
        "get_simpler_info",
        "set_simpler_playback_mode",
        "insert_simpler_slice",
        "move_simpler_slice",
        "remove_simpler_slice",
        "clear_simpler_slices",
        "set_drum_pad_mute",
        "set_drum_pad_solo",
        "delete_drum_pad_chains",
        "list_plugin_presets",
        "set_plugin_preset",
        "compare_ab",
    }
    assert expected.issubset(names), f"Missing device extended tools: {expected - names}"


async def test_crop_simpler_calls_send_command(mcp_server, mock_connection):
    """crop_simpler invokes send_command and returns cropped status."""
    mock_connection.send_command.return_value = {
        "cropped": True,
        "device_name": "Simpler",
    }
    result = await mcp_server.call_tool(
        "crop_simpler",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["cropped"] is True


async def test_reverse_simpler_calls_send_command(mcp_server, mock_connection):
    """reverse_simpler invokes send_command and returns reversed status."""
    mock_connection.send_command.return_value = {
        "reversed": True,
        "device_name": "Simpler",
    }
    result = await mcp_server.call_tool(
        "reverse_simpler",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["reversed"] is True


async def test_warp_simpler_calls_send_command(mcp_server, mock_connection):
    """warp_simpler invokes send_command with mode param."""
    mock_connection.send_command.return_value = {
        "warped": True,
        "device_name": "Simpler",
        "mode": "double",
    }
    result = await mcp_server.call_tool(
        "warp_simpler",
        {"track_index": 0, "mode": "double"},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["mode"] == "double"


async def test_get_simpler_info_calls_send_command(mcp_server, mock_connection):
    """get_simpler_info returns playback mode and sample details."""
    mock_connection.send_command.return_value = {
        "device_name": "Simpler",
        "playback_mode": 0,
        "playback_mode_label": "Classic",
        "sample": {
            "file_path": "/test.wav",
            "length": 44100,
            "sample_rate": 44100,
            "slices": [],
            "slicing_sensitivity": 0.5,
            "slicing_style": 0,
        },
        "can_warp_as": True,
        "can_warp_double": True,
        "can_warp_half": True,
    }
    result = await mcp_server.call_tool(
        "get_simpler_info",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["playback_mode_label"] == "Classic"


async def test_set_simpler_playback_mode_calls_send_command(mcp_server, mock_connection):
    """set_simpler_playback_mode sets mode and returns label."""
    mock_connection.send_command.return_value = {
        "device_name": "Simpler",
        "playback_mode": 2,
        "playback_mode_label": "Slicing",
    }
    result = await mcp_server.call_tool(
        "set_simpler_playback_mode",
        {"track_index": 0, "mode": 2},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["playback_mode"] == 2


async def test_insert_simpler_slice_calls_send_command(mcp_server, mock_connection):
    """insert_simpler_slice inserts a slice and returns updated slices."""
    mock_connection.send_command.return_value = {
        "inserted": True,
        "device_name": "Simpler",
        "time": 22050,
        "slices": [22050],
    }
    result = await mcp_server.call_tool(
        "insert_simpler_slice",
        {"track_index": 0, "time": 22050},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["inserted"] is True


async def test_remove_simpler_slice_calls_send_command(mcp_server, mock_connection):
    """remove_simpler_slice removes a slice and returns updated slices."""
    mock_connection.send_command.return_value = {
        "removed": True,
        "device_name": "Simpler",
        "time": 22050,
        "slices": [],
    }
    result = await mcp_server.call_tool(
        "remove_simpler_slice",
        {"track_index": 0, "time": 22050},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["removed"] is True


async def test_clear_simpler_slices_calls_send_command(mcp_server, mock_connection):
    """clear_simpler_slices clears all slices."""
    mock_connection.send_command.return_value = {
        "cleared": True,
        "device_name": "Simpler",
        "slices": [],
    }
    result = await mcp_server.call_tool(
        "clear_simpler_slices",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["cleared"] is True


async def test_set_drum_pad_mute_calls_send_command(mcp_server, mock_connection):
    """set_drum_pad_mute mutes a pad by MIDI note."""
    mock_connection.send_command.return_value = {
        "note": 36,
        "name": "C1 Kick",
        "mute": True,
    }
    result = await mcp_server.call_tool(
        "set_drum_pad_mute",
        {"track_index": 0, "note": 36, "mute": True},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["mute"] is True


async def test_set_drum_pad_solo_calls_send_command(mcp_server, mock_connection):
    """set_drum_pad_solo solos a pad by MIDI note."""
    mock_connection.send_command.return_value = {
        "note": 38,
        "name": "D1 Snare",
        "solo": True,
        "note_text": "DrumPad solo does not auto-unsolo other pads. Use exclusive=True to solo exclusively.",
    }
    result = await mcp_server.call_tool(
        "set_drum_pad_solo",
        {"track_index": 0, "note": 38, "solo": True},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["solo"] is True


async def test_set_drum_pad_solo_exclusive(mcp_server, mock_connection):
    """set_drum_pad_solo with exclusive=True passes exclusive in params."""
    mock_connection.send_command.return_value = {
        "note": 38,
        "name": "D1 Snare",
        "solo": True,
        "note_text": "DrumPad solo does not auto-unsolo other pads. Use exclusive=True to solo exclusively.",
    }
    await mcp_server.call_tool(
        "set_drum_pad_solo",
        {"track_index": 0, "note": 38, "solo": True, "exclusive": True},
    )
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["exclusive"] is True


async def test_delete_drum_pad_chains_calls_send_command(mcp_server, mock_connection):
    """delete_drum_pad_chains clears pad content."""
    mock_connection.send_command.return_value = {
        "deleted": True,
        "note": 36,
        "name": "C1 Kick",
    }
    result = await mcp_server.call_tool(
        "delete_drum_pad_chains",
        {"track_index": 0, "note": 36},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["deleted"] is True


async def test_list_plugin_presets_calls_send_command(mcp_server, mock_connection):
    """list_plugin_presets returns preset list for a plugin device."""
    mock_connection.send_command.return_value = {
        "device_name": "Serum",
        "presets": ["Init", "Bass 1", "Lead 1"],
        "selected_preset_index": 0,
        "preset_count": 3,
    }
    result = await mcp_server.call_tool(
        "list_plugin_presets",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert len(parsed["presets"]) == 3


async def test_set_plugin_preset_calls_send_command(mcp_server, mock_connection):
    """set_plugin_preset selects a preset by index."""
    mock_connection.send_command.return_value = {
        "device_name": "Serum",
        "selected_preset_index": 1,
        "preset_name": "Bass 1",
    }
    result = await mcp_server.call_tool(
        "set_plugin_preset",
        {"track_index": 0, "preset_index": 1},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["preset_name"] == "Bass 1"


async def test_compare_ab_calls_send_command(mcp_server, mock_connection):
    """compare_ab returns A/B comparison state."""
    mock_connection.send_command.return_value = {
        "device_name": "EQ Eight",
        "can_compare_ab": True,
        "is_using_compare_preset_b": False,
        "action": "info",
    }
    result = await mcp_server.call_tool(
        "compare_ab",
        {"track_index": 0},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["can_compare_ab"] is True


async def test_compare_ab_save(mcp_server, mock_connection):
    """compare_ab with action='save' saves preset to compare slot."""
    mock_connection.send_command.return_value = {
        "device_name": "EQ Eight",
        "can_compare_ab": True,
        "is_using_compare_preset_b": False,
        "action": "save",
    }
    result = await mcp_server.call_tool(
        "compare_ab",
        {"track_index": 0, "action": "save"},
    )
    text = result[0][0].text
    parsed = json.loads(text)
    assert parsed["action"] == "save"


# --- Quick Task: LOM Gap Smoke Tests ---


async def test_get_wavetable_info(mcp_server, mock_connection):
    """get_wavetable_info returns Wavetable device info."""
    mock_connection.send_command.return_value = {
        "device_name": "Wavetable",
        "oscillator_wavetable_categories": ["Basic Shapes"],
    }
    result = await mcp_server.call_tool(
        "get_wavetable_info",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Wavetable"


async def test_get_compressor_sidechain(mcp_server, mock_connection):
    """get_compressor_sidechain returns sidechain routing info."""
    mock_connection.send_command.return_value = {
        "device_name": "Compressor",
        "input_routing_type": "Post FX",
    }
    result = await mcp_server.call_tool(
        "get_compressor_sidechain",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Compressor"


async def test_get_rack_variations(mcp_server, mock_connection):
    """get_rack_variations returns macro variation info."""
    mock_connection.send_command.return_value = {
        "device_name": "Instrument Rack",
        "variation_count": 3,
    }
    result = await mcp_server.call_tool(
        "get_rack_variations",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["variation_count"] == 3


async def test_get_drift_mod_matrix(mcp_server, mock_connection):
    """get_drift_mod_matrix returns Drift modulation matrix state."""
    mock_connection.send_command.return_value = {
        "device_name": "Drift",
        "slots": [],
    }
    result = await mcp_server.call_tool(
        "get_drift_mod_matrix",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Drift"


async def test_get_looper_info(mcp_server, mock_connection):
    """get_looper_info returns Looper device state."""
    mock_connection.send_command.return_value = {
        "device_name": "Looper",
        "loop_length": 4.0,
    }
    result = await mcp_server.call_tool(
        "get_looper_info",
        {"track_index": 0, "device_index": 0},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Looper"


async def test_get_tuning_system(mcp_server, mock_connection):
    """get_tuning_system returns tuning system info."""
    mock_connection.send_command.return_value = {
        "name": "12-TET",
        "reference_pitch": 440.0,
    }
    result = await mcp_server.call_tool(
        "get_tuning_system",
        {},
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "12-TET"
