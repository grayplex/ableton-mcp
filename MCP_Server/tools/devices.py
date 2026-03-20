"""Device tools: instrument/effect loading, parameter control, rack navigation."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def load_instrument_or_effect(
    ctx: Context,
    track_index: int,
    uri: str | None = None,
    path: str | None = None,
) -> str:
    """Load an instrument or effect onto a track using its browser URI or path.

    Provide either uri or path (not both). The URI comes from get_browser_tree
    or get_browser_items_at_path. The path is a human-readable browser path
    like "instruments/Analog" or "audio_effects/Delay/Simple Delay".

    Device On/Off is parameter index 0 on all devices. Use set_device_parameter
    to enable/disable.

    Parameters:
    - track_index: The index of the track to load on
    - uri: Browser URI (e.g., 'query:Synths#Analog')
    - path: Browser path (e.g., 'instruments/Analog')
    """
    try:
        ableton = get_ableton_connection()
        params = {"track_index": track_index}
        if uri is not None:
            params["item_uri"] = uri
        if path is not None:
            params["path"] = path
        result = ableton.send_command("load_browser_item", params)

        if result.get("loaded", False):
            return json.dumps(result, indent=2)
        else:
            error_msg = result.get("error", "Unknown reason")
            return format_error(
                f"Failed to load instrument",
                detail=error_msg,
                suggestion="Verify the URI using get_browser_items_at_path first",
            )
    except Exception as e:
        return format_error(
            "Failed to load instrument",
            detail=str(e),
            suggestion="Verify the URI using get_browser_items_at_path first",
        )


@mcp.tool()
def get_device_parameters(
    ctx: Context,
    track_index: int,
    device_index: int,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get all parameters of a device on a track.

    Returns device name, type, and a list of parameters with their current
    values, ranges, and quantization info.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_device_parameters", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get device parameters",
            detail=str(e),
            suggestion="Verify device exists with get_track_info",
        )


@mcp.tool()
def set_device_parameter(
    ctx: Context,
    track_index: int,
    device_index: int,
    value: float,
    track_type: str = "track",
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set a device parameter value by name or index.

    Parameter name matching is case-insensitive and uses first-match if
    duplicates exist. For precise control, use parameter_index instead.

    Tip: Device On/Off is always parameter index 0.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the device on the track
    - value: The value to set (will be clamped to parameter's min/max range)
    - track_type: Track collection - "track", "return", or "master"
    - parameter_name: Name of the parameter (case-insensitive, first match)
    - parameter_index: Index of the parameter (use for precise control)
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "value": value,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_device_parameter", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set device parameter",
            detail=str(e),
            suggestion="Check parameter names with get_device_parameters. Use parameter_index for precise control.",
        )


@mcp.tool()
def delete_device(
    ctx: Context,
    track_index: int,
    device_index: int,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Delete a device from a track's device chain.

    Returns the deleted device name and the updated device list.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the device to delete
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("delete_device", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to delete device",
            detail=str(e),
            suggestion="Verify device exists with get_track_info first",
        )


@mcp.tool()
def get_rack_chains(
    ctx: Context,
    track_index: int,
    device_index: int,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get the chain structure of an Instrument Rack, Effect Rack, or Drum Rack.

    For Instrument/Effect Racks: returns a list of chains, each with its name,
    index, and contained devices.

    For Drum Racks: returns a list of pads (only those with content), each with
    note number, name, and chain devices.

    Use chain_index + chain_device_index to navigate nested racks (rack within
    a rack chain).

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the rack device
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for nested racks
    - chain_device_index: Device index within a rack chain (for nested racks)
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_rack_chains", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get rack chains",
            detail=str(e),
            suggestion="Verify device is a rack with get_track_info (type='rack' or 'drum_machine')",
        )


@mcp.tool()
def insert_device(
    ctx: Context,
    track_index: int,
    device_name: str,
    position: int,
    track_type: str = "track",
) -> str:
    """Insert a native Ableton device by name at a specific position in the device chain.

    Parameters:
    - track_index: Index of the track
    - device_name: Name of the device to insert (e.g., "Wavetable", "EQ Eight")
    - position: Position in the device chain (0-based)
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "insert_device",
            {
                "track_index": track_index,
                "device_name": device_name,
                "position": position,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to insert device",
            detail=str(e),
            suggestion="Verify device name is a valid Ableton device",
        )


@mcp.tool()
def move_device(
    ctx: Context,
    source_track_index: int,
    device_index: int,
    target_track_index: int,
    target_position: int,
    source_track_type: str = "track",
    target_track_type: str = "track",
) -> str:
    """Move a device from one track/position to another.

    Parameters:
    - source_track_index: Index of the source track
    - device_index: Index of the device on the source track
    - target_track_index: Index of the target track
    - target_position: Position in the target track's device chain
    - source_track_type: Source track collection - "track", "return", or "master"
    - target_track_type: Target track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "move_device",
            {
                "source_track_index": source_track_index,
                "device_index": device_index,
                "target_track_index": target_track_index,
                "target_position": target_position,
                "source_track_type": source_track_type,
                "target_track_type": target_track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to move device",
            detail=str(e),
            suggestion="Verify device and target track exist with get_track_info",
        )


# --- Phase 13: Simpler, DrumPad, Plugin, A/B Compare ---


@mcp.tool()
def crop_simpler(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Crop a Simpler device's sample to the active region.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "crop_simpler",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to crop Simpler sample",
            detail=str(e),
            suggestion="Ensure the device is a Simpler with a sample loaded",
        )


@mcp.tool()
def reverse_simpler(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Reverse a Simpler device's loaded sample.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "reverse_simpler",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to reverse Simpler sample",
            detail=str(e),
            suggestion="Ensure the device is a Simpler with a sample loaded",
        )


@mcp.tool()
def warp_simpler(
    ctx: Context,
    track_index: int,
    mode: str,
    device_index: int = 0,
    beats: float | None = None,
    track_type: str = "track",
) -> str:
    """Warp a Simpler device's sample.

    Parameters:
    - track_index: Index of the track
    - mode: 'as' (warp to specified beats), 'double' (double tempo), 'half' (half tempo)
    - device_index: Index of the Simpler device on the track
    - beats: Required when mode='as', number of beats to warp to
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "mode": mode,
        }
        if beats is not None:
            params["beats"] = beats
        result = ableton.send_command("warp_simpler", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to warp Simpler sample",
            detail=str(e),
            suggestion="Ensure the device is a Simpler with a sample loaded",
        )


@mcp.tool()
def get_simpler_info(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Get Simpler device info: playback mode, warp capabilities, and sample details including slices.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_simpler_info",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get Simpler info",
            detail=str(e),
            suggestion="Ensure the device is a Simpler device",
        )


@mcp.tool()
def set_simpler_playback_mode(
    ctx: Context,
    track_index: int,
    mode: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Set Simpler playback mode.

    Parameters:
    - track_index: Index of the track
    - mode: 0=Classic, 1=One-Shot, 2=Slicing
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_simpler_playback_mode",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "mode": mode,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set Simpler playback mode",
            detail=str(e),
            suggestion="Ensure the device is a Simpler device",
        )


@mcp.tool()
def insert_simpler_slice(
    ctx: Context,
    track_index: int,
    time: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Insert a slice marker in a Simpler sample at a position in sample frames.

    Parameters:
    - track_index: Index of the track
    - time: Position in sample frames to insert the slice
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "insert_simpler_slice",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "time": time,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to insert Simpler slice",
            detail=str(e),
            suggestion="Ensure the device is a Simpler with a sample loaded",
        )


@mcp.tool()
def move_simpler_slice(
    ctx: Context,
    track_index: int,
    source_time: int,
    destination_time: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Move a slice marker from one position to another (positions in sample frames).

    Parameters:
    - track_index: Index of the track
    - source_time: Current position of the slice in sample frames
    - destination_time: New position for the slice in sample frames
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "move_simpler_slice",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "source_time": source_time,
                "destination_time": destination_time,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to move Simpler slice",
            detail=str(e),
            suggestion="Ensure the device is a Simpler with a sample loaded",
        )


@mcp.tool()
def remove_simpler_slice(
    ctx: Context,
    track_index: int,
    time: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Remove a slice marker at the specified position (in sample frames).

    Parameters:
    - track_index: Index of the track
    - time: Position of the slice to remove in sample frames
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "remove_simpler_slice",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "time": time,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to remove Simpler slice",
            detail=str(e),
            suggestion="Ensure the device is a Simpler with a sample loaded",
        )


@mcp.tool()
def clear_simpler_slices(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Clear all slice markers from a Simpler sample. Only works in Manual slicing mode.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Simpler device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "clear_simpler_slices",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to clear Simpler slices",
            detail=str(e),
            suggestion="Ensure the device is a Simpler with a sample loaded",
        )


@mcp.tool()
def set_drum_pad_mute(
    ctx: Context,
    track_index: int,
    note: int,
    mute: bool,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Mute or unmute a drum pad by MIDI note number.

    Parameters:
    - track_index: Index of the track
    - note: MIDI note number of the drum pad (e.g., 36 for C1)
    - mute: True to mute, False to unmute
    - device_index: Index of the Drum Rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_drum_pad_mute",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "note": note,
                "mute": mute,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set drum pad mute",
            detail=str(e),
            suggestion="Ensure the device is a Drum Rack and the note number is valid",
        )


@mcp.tool()
def set_drum_pad_solo(
    ctx: Context,
    track_index: int,
    note: int,
    solo: bool,
    device_index: int = 0,
    track_type: str = "track",
    exclusive: bool = False,
) -> str:
    """Solo or unsolo a drum pad by MIDI note number. Note: drum pad solo does not auto-unsolo other pads unless exclusive=True.

    Parameters:
    - track_index: Index of the track
    - note: MIDI note number of the drum pad (e.g., 36 for C1)
    - solo: True to solo, False to unsolo
    - device_index: Index of the Drum Rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - exclusive: If True and solo=True, unsolo all other pads first
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_drum_pad_solo",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "note": note,
                "solo": solo,
                "exclusive": exclusive,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set drum pad solo",
            detail=str(e),
            suggestion="Ensure the device is a Drum Rack and the note number is valid",
        )


@mcp.tool()
def delete_drum_pad_chains(
    ctx: Context,
    track_index: int,
    note: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Clear all chains from a drum pad, removing its content.

    Parameters:
    - track_index: Index of the track
    - note: MIDI note number of the drum pad (e.g., 36 for C1)
    - device_index: Index of the Drum Rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "delete_drum_pad_chains",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "note": note,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to delete drum pad chains",
            detail=str(e),
            suggestion="Ensure the device is a Drum Rack and the note number is valid",
        )


@mcp.tool()
def list_plugin_presets(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """List available presets for a VST/AU plugin device.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the plugin device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "list_plugin_presets",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to list plugin presets",
            detail=str(e),
            suggestion="Only VST/AU plugin devices have presets. Native Ableton devices do not.",
        )


@mcp.tool()
def set_plugin_preset(
    ctx: Context,
    track_index: int,
    preset_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Select a preset by index for a VST/AU plugin device. Use list_plugin_presets to see available presets.

    Parameters:
    - track_index: Index of the track
    - preset_index: Index of the preset to select
    - device_index: Index of the plugin device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_plugin_preset",
            {
                "track_index": track_index,
                "device_index": device_index,
                "track_type": track_type,
                "preset_index": preset_index,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set plugin preset",
            detail=str(e),
            suggestion="Use list_plugin_presets to check available presets and valid indices",
        )


@mcp.tool()
def compare_ab(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    action: str | None = None,
) -> str:
    """A/B preset comparison (Live 12.3+). Call without action to get current state. Use action='save' to save current preset to compare slot.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the device on the track
    - track_type: Track collection - "track", "return", or "master"
    - action: 'save' to save preset to compare slot, or omit for info only
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if action is not None:
            params["action"] = action
        result = ableton.send_command("compare_ab", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to compare A/B presets",
            detail=str(e),
            suggestion="Ensure the device supports A/B comparison (Live 12.3+)",
        )


# --- WavetableDevice ---
# (6 tools: get_wavetable_info, set_wavetable_oscillator, set_wavetable_voice_config,
#  add_wavetable_modulation, set_wavetable_modulation_value, get_wavetable_modulation_value)


@mcp.tool()
def get_wavetable_info(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get Wavetable device info: oscillator categories, wavetables, voice config, and modulation targets.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Wavetable device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_wavetable_info", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get Wavetable info",
            detail=str(e),
            suggestion="Ensure the device is a Wavetable synthesizer",
        )


@mcp.tool()
def set_wavetable_oscillator(
    ctx: Context,
    track_index: int,
    oscillator: int,
    device_index: int = 0,
    track_type: str = "track",
    category: int | None = None,
    index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set oscillator wavetable selection on a Wavetable device. Use get_wavetable_info to see available categories and wavetables.

    Parameters:
    - track_index: Index of the track
    - oscillator: 1 or 2 (which oscillator to configure)
    - device_index: Index of the Wavetable device on the track
    - track_type: Track collection - "track", "return", or "master"
    - category: Wavetable category index
    - index: Wavetable index within the category
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "oscillator": oscillator,
        }
        if category is not None:
            params["category"] = category
        if index is not None:
            params["index"] = index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_wavetable_oscillator", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set Wavetable oscillator",
            detail=str(e),
            suggestion="Use get_wavetable_info to see available categories and wavetables",
        )


@mcp.tool()
def set_wavetable_voice_config(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    mono_poly: int | None = None,
    poly_voices: int | None = None,
    unison_mode: int | None = None,
    unison_voice_count: int | None = None,
    filter_routing: int | None = None,
    oscillator_1_effect_mode: int | None = None,
    oscillator_2_effect_mode: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set Wavetable voice configuration: mono/poly, unison, filter routing, and oscillator effect modes.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Wavetable device on the track
    - track_type: Track collection - "track", "return", or "master"
    - mono_poly: Mono/poly mode
    - poly_voices: Number of polyphony voices
    - unison_mode: Unison mode
    - unison_voice_count: Number of unison voices
    - filter_routing: Filter routing mode
    - oscillator_1_effect_mode: Oscillator 1 effect mode
    - oscillator_2_effect_mode: Oscillator 2 effect mode
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if mono_poly is not None:
            params["mono_poly"] = mono_poly
        if poly_voices is not None:
            params["poly_voices"] = poly_voices
        if unison_mode is not None:
            params["unison_mode"] = unison_mode
        if unison_voice_count is not None:
            params["unison_voice_count"] = unison_voice_count
        if filter_routing is not None:
            params["filter_routing"] = filter_routing
        if oscillator_1_effect_mode is not None:
            params["oscillator_1_effect_mode"] = oscillator_1_effect_mode
        if oscillator_2_effect_mode is not None:
            params["oscillator_2_effect_mode"] = oscillator_2_effect_mode
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_wavetable_voice_config", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set Wavetable voice config",
            detail=str(e),
            suggestion="Use get_wavetable_info to see current voice configuration",
        )


@mcp.tool()
def add_wavetable_modulation(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Add a parameter to the Wavetable modulation matrix. Use get_device_parameters to find parameter names/indices.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Wavetable device on the track
    - track_type: Track collection - "track", "return", or "master"
    - parameter_name: Name of the parameter to add (case-insensitive)
    - parameter_index: Index of the parameter to add
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("add_wavetable_modulation", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to add Wavetable modulation",
            detail=str(e),
            suggestion="Use get_device_parameters to find valid parameter names",
        )


@mcp.tool()
def set_wavetable_modulation_value(
    ctx: Context,
    track_index: int,
    modulation_target: str,
    value: float,
    device_index: int = 0,
    track_type: str = "track",
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set modulation amount for a parameter in the Wavetable modulation matrix.

    Parameters:
    - track_index: Index of the track
    - modulation_target: Target name from visible_modulation_target_names
    - value: Modulation amount (float)
    - device_index: Index of the Wavetable device on the track
    - track_type: Track collection - "track", "return", or "master"
    - parameter_name: Name of the parameter (case-insensitive)
    - parameter_index: Index of the parameter
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "modulation_target": modulation_target,
            "value": value,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_wavetable_modulation_value", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set Wavetable modulation value",
            detail=str(e),
            suggestion="Use get_wavetable_info to see visible_modulation_target_names",
        )


@mcp.tool()
def get_wavetable_modulation_value(
    ctx: Context,
    track_index: int,
    modulation_target: str,
    device_index: int = 0,
    track_type: str = "track",
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get modulation value for a parameter in the Wavetable modulation matrix. Also returns modulatability info.

    Parameters:
    - track_index: Index of the track
    - modulation_target: Target name from visible_modulation_target_names
    - device_index: Index of the Wavetable device on the track
    - track_type: Track collection - "track", "return", or "master"
    - parameter_name: Name of the parameter (case-insensitive)
    - parameter_index: Index of the parameter
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "modulation_target": modulation_target,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_wavetable_modulation_value", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get Wavetable modulation value",
            detail=str(e),
            suggestion="Use get_wavetable_info to see visible_modulation_target_names",
        )


# --- CompressorDevice ---
# (2 tools: get_compressor_sidechain, set_compressor_sidechain)


@mcp.tool()
def get_compressor_sidechain(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get sidechain routing info for a Compressor device. Returns available routing types/channels and current selection.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Compressor device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_compressor_sidechain", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get Compressor sidechain",
            detail=str(e),
            suggestion="Ensure the device is a Compressor with sidechain support",
        )


@mcp.tool()
def set_compressor_sidechain(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    routing_type_index: int | None = None,
    routing_channel_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set sidechain source on a Compressor device. Use get_compressor_sidechain to see available routing options.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Compressor device on the track
    - track_type: Track collection - "track", "return", or "master"
    - routing_type_index: Index into available_input_routing_types
    - routing_channel_index: Index into available_input_routing_channels
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if routing_type_index is not None:
            params["routing_type_index"] = routing_type_index
        if routing_channel_index is not None:
            params["routing_channel_index"] = routing_channel_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_compressor_sidechain", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set Compressor sidechain",
            detail=str(e),
            suggestion="Use get_compressor_sidechain to see available routing options",
        )


# --- RackDevice Extended ---
# (5 tools: get_rack_variations, rack_variation_action, rack_macro_action,
#  insert_rack_chain, copy_drum_pad)


@mcp.tool()
def get_rack_variations(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get macro variation info for a rack device: variation count, selected index, and visible macro count.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_rack_variations", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get rack variations",
            detail=str(e),
            suggestion="Ensure the device is an Instrument or Effect Rack",
        )


@mcp.tool()
def rack_variation_action(
    ctx: Context,
    track_index: int,
    action: str,
    device_index: int = 0,
    track_type: str = "track",
    index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Manage rack macro variations: store, recall, recall_last, or delete.

    Parameters:
    - track_index: Index of the track
    - action: 'store', 'recall', 'recall_last', or 'delete'
    - device_index: Index of the rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - index: Variation index (for recall/delete)
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "action": action,
        }
        if index is not None:
            params["index"] = index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("rack_variation_action", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to perform rack variation action",
            detail=str(e),
            suggestion="Use get_rack_variations to see current variations",
        )


@mcp.tool()
def rack_macro_action(
    ctx: Context,
    track_index: int,
    action: str,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Manage rack macros: add, remove, or randomize macro knobs.

    Parameters:
    - track_index: Index of the track
    - action: 'add', 'remove', or 'randomize'
    - device_index: Index of the rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "action": action,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("rack_macro_action", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to perform rack macro action",
            detail=str(e),
            suggestion="Ensure the device is a rack device",
        )


@mcp.tool()
def insert_rack_chain(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Insert a new chain into a rack device. Defaults to appending at end.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - index: Position to insert chain (default: end)
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if index is not None:
            params["index"] = index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("insert_rack_chain", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to insert rack chain",
            detail=str(e),
            suggestion="Ensure the device is a rack that can have chains",
        )


@mcp.tool()
def copy_drum_pad(
    ctx: Context,
    track_index: int,
    source_note: int,
    target_note: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Copy drum pad content from one pad to another by MIDI note number.

    Parameters:
    - track_index: Index of the track
    - source_note: MIDI note number of the source pad
    - target_note: MIDI note number of the target pad
    - device_index: Index of the Drum Rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "source_note": source_note,
            "target_note": target_note,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("copy_drum_pad", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to copy drum pad",
            detail=str(e),
            suggestion="Ensure the device is a Drum Rack",
        )


# --- DrumChain ---
# (2 tools: get_drum_chain_config, set_drum_chain_config)


@mcp.tool()
def get_drum_chain_config(
    ctx: Context,
    track_index: int,
    chain_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Get drum chain configuration: in_note, out_note, choke_group, and name.

    Parameters:
    - track_index: Index of the track
    - chain_index: Index of the chain within the drum rack
    - device_index: Index of the Drum Rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "chain_index": chain_index,
        }
        result = ableton.send_command("get_drum_chain_config", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get drum chain config",
            detail=str(e),
            suggestion="Ensure the device is a Drum Rack and the chain exists",
        )


@mcp.tool()
def set_drum_chain_config(
    ctx: Context,
    track_index: int,
    chain_index: int,
    device_index: int = 0,
    track_type: str = "track",
    in_note: int | None = None,
    out_note: int | None = None,
    choke_group: int | None = None,
) -> str:
    """Set drum chain properties: in_note, out_note, and choke_group.

    Parameters:
    - track_index: Index of the track
    - chain_index: Index of the chain within the drum rack
    - device_index: Index of the Drum Rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - in_note: MIDI note for chain input
    - out_note: MIDI note for chain output
    - choke_group: Choke group number
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "chain_index": chain_index,
        }
        if in_note is not None:
            params["in_note"] = in_note
        if out_note is not None:
            params["out_note"] = out_note
        if choke_group is not None:
            params["choke_group"] = choke_group
        result = ableton.send_command("set_drum_chain_config", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set drum chain config",
            detail=str(e),
            suggestion="Ensure the device is a Drum Rack and the chain exists",
        )


# --- DeviceParameter Extended ---
# (2 tools: get_parameter_automation_state, re_enable_parameter_automation)


@mcp.tool()
def get_parameter_automation_state(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get automation state of a device parameter (0=none, 1=playing, 2=overridden).

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the device on the track
    - track_type: Track collection - "track", "return", or "master"
    - parameter_name: Name of the parameter (case-insensitive)
    - parameter_index: Index of the parameter
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_parameter_automation_state", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get parameter automation state",
            detail=str(e),
            suggestion="Use get_device_parameters to find parameter names/indices",
        )


@mcp.tool()
def re_enable_parameter_automation(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Re-enable overridden automation for a device parameter.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the device on the track
    - track_type: Track collection - "track", "return", or "master"
    - parameter_name: Name of the parameter (case-insensitive)
    - parameter_index: Index of the parameter
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("re_enable_parameter_automation", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to re-enable parameter automation",
            detail=str(e),
            suggestion="Use get_parameter_automation_state to check current state",
        )


# --- DriftDevice ---
# (2 tools: get_drift_mod_matrix, set_drift_mod_matrix)


@mcp.tool()
def get_drift_mod_matrix(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get Drift modulation matrix state for all 8 slots (source/target indices and lists).

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Drift device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_drift_mod_matrix", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get Drift mod matrix",
            detail=str(e),
            suggestion="Ensure the device is a Drift synthesizer",
        )


@mcp.tool()
def set_drift_mod_matrix(
    ctx: Context,
    track_index: int,
    slot: int,
    device_index: int = 0,
    track_type: str = "track",
    source_index: int | None = None,
    target_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set Drift modulation matrix slot source/target. Use get_drift_mod_matrix to see available sources/targets.

    Parameters:
    - track_index: Index of the track
    - slot: Mod matrix slot number (1-8)
    - device_index: Index of the Drift device on the track
    - track_type: Track collection - "track", "return", or "master"
    - source_index: Index into the slot's source list
    - target_index: Index into the slot's target list
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "slot": slot,
        }
        if source_index is not None:
            params["source_index"] = source_index
        if target_index is not None:
            params["target_index"] = target_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_drift_mod_matrix", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set Drift mod matrix",
            detail=str(e),
            suggestion="Use get_drift_mod_matrix to see valid source/target lists",
        )


# --- LooperDevice ---
# (3 tools: get_looper_info, looper_action, looper_export_to_clip_slot)


@mcp.tool()
def get_looper_info(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get Looper device state: loop length, overdub setting, record length, and tempo.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Looper device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_looper_info", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get Looper info",
            detail=str(e),
            suggestion="Ensure the device is a Looper device",
        )


@mcp.tool()
def looper_action(
    ctx: Context,
    track_index: int,
    action: str,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Execute a Looper action: record, overdub, play, stop, clear, undo, double_speed, half_speed, double_length, half_length.

    Parameters:
    - track_index: Index of the track
    - action: Looper action to perform
    - device_index: Index of the Looper device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "action": action,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("looper_action", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to perform Looper action",
            detail=str(e),
            suggestion="Valid actions: record, overdub, play, stop, clear, undo, double_speed, half_speed, double_length, half_length",
        )


@mcp.tool()
def looper_export_to_clip_slot(
    ctx: Context,
    track_index: int,
    scene_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Export Looper content to a clip slot for further editing.

    Parameters:
    - track_index: Index of the track
    - scene_index: Index of the scene/clip slot to export to
    - device_index: Index of the Looper device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "scene_index": scene_index,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("looper_export_to_clip_slot", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to export Looper to clip slot",
            detail=str(e),
            suggestion="Ensure the Looper has recorded content and the scene index is valid",
        )


# --- SpectralResonatorDevice ---
# (2 tools: get_spectral_resonator_info, set_spectral_resonator_config)


@mcp.tool()
def get_spectral_resonator_info(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get Spectral Resonator device config: frequency dial mode, MIDI gate, mod mode, pitch settings, polyphony.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Spectral Resonator device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_spectral_resonator_info", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get Spectral Resonator info",
            detail=str(e),
            suggestion="Ensure the device is a Spectral Resonator",
        )


@mcp.tool()
def set_spectral_resonator_config(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    frequency_dial_mode: int | None = None,
    midi_gate: int | None = None,
    mod_mode: int | None = None,
    mono_poly: int | None = None,
    pitch_mode: int | None = None,
    pitch_bend_range: int | None = None,
    polyphony: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set Spectral Resonator device properties. Only non-None parameters are updated.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the Spectral Resonator device on the track
    - track_type: Track collection - "track", "return", or "master"
    - frequency_dial_mode: Frequency dial mode
    - midi_gate: MIDI gate setting
    - mod_mode: Modulation mode
    - mono_poly: Mono/poly mode
    - pitch_mode: Pitch mode
    - pitch_bend_range: Pitch bend range
    - polyphony: Number of voices
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if frequency_dial_mode is not None:
            params["frequency_dial_mode"] = frequency_dial_mode
        if midi_gate is not None:
            params["midi_gate"] = midi_gate
        if mod_mode is not None:
            params["mod_mode"] = mod_mode
        if mono_poly is not None:
            params["mono_poly"] = mono_poly
        if pitch_mode is not None:
            params["pitch_mode"] = pitch_mode
        if pitch_bend_range is not None:
            params["pitch_bend_range"] = pitch_bend_range
        if polyphony is not None:
            params["polyphony"] = polyphony
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_spectral_resonator_config", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set Spectral Resonator config",
            detail=str(e),
            suggestion="Use get_spectral_resonator_info to see current settings",
        )


# --- Eq8Device ---
# (2 tools: get_eq8_info, set_eq8_mode)


@mcp.tool()
def get_eq8_info(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Get EQ8 processing modes: edit mode, global mode, and oversample state.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the EQ8 device on the track
    - track_type: Track collection - "track", "return", or "master"
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("get_eq8_info", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get EQ8 info",
            detail=str(e),
            suggestion="Ensure the device is an EQ Eight",
        )


@mcp.tool()
def set_eq8_mode(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    track_type: str = "track",
    edit_mode: int | None = None,
    global_mode: int | None = None,
    oversample: bool | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Set EQ8 processing modes. Only non-None parameters are updated.

    Parameters:
    - track_index: Index of the track
    - device_index: Index of the EQ8 device on the track
    - track_type: Track collection - "track", "return", or "master"
    - edit_mode: EQ8 edit mode
    - global_mode: EQ8 global mode
    - oversample: Enable/disable oversampling
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
        }
        if edit_mode is not None:
            params["edit_mode"] = edit_mode
        if global_mode is not None:
            params["global_mode"] = global_mode
        if oversample is not None:
            params["oversample"] = oversample
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("set_eq8_mode", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set EQ8 mode",
            detail=str(e),
            suggestion="Use get_eq8_info to see current modes",
        )


# --- TakeLane ---
# (3 tools: get_take_lanes, get_take_lane_clips, create_take_lane_clip)


@mcp.tool()
def get_take_lanes(
    ctx: Context,
    track_index: int,
    track_type: str = "track",
) -> str:
    """Get take lanes for a track, including lane names and clip counts.

    Parameters:
    - track_index: Index of the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "track_type": track_type,
        }
        result = ableton.send_command("get_take_lanes", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get take lanes",
            detail=str(e),
            suggestion="Ensure the track supports take lanes",
        )


@mcp.tool()
def get_take_lane_clips(
    ctx: Context,
    track_index: int,
    lane_index: int,
    track_type: str = "track",
) -> str:
    """Get arrangement clips in a specific take lane.

    Parameters:
    - track_index: Index of the track
    - lane_index: Index of the take lane
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "track_type": track_type,
            "lane_index": lane_index,
        }
        result = ableton.send_command("get_take_lane_clips", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get take lane clips",
            detail=str(e),
            suggestion="Use get_take_lanes to see available lanes",
        )


@mcp.tool()
def create_take_lane_clip(
    ctx: Context,
    track_index: int,
    lane_index: int,
    start_time: float,
    length: float,
    clip_type: str = "midi",
    track_type: str = "track",
) -> str:
    """Create a new clip in a take lane.

    Parameters:
    - track_index: Index of the track
    - lane_index: Index of the take lane
    - start_time: Start position in beats
    - length: Clip length in beats
    - clip_type: 'midi' or 'audio'
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "track_type": track_type,
            "lane_index": lane_index,
            "start_time": start_time,
            "length": length,
            "clip_type": clip_type,
        }
        result = ableton.send_command("create_take_lane_clip", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create take lane clip",
            detail=str(e),
            suggestion="Use get_take_lanes to see available lanes",
        )


# --- TuningSystem ---
# (2 tools: get_tuning_system, set_tuning_system)


@mcp.tool()
def get_tuning_system(
    ctx: Context,
) -> str:
    """Get tuning system info: name, reference pitch, note tunings, octave cents, and note range.

    No track/device parameters needed -- this is a song-level property.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_tuning_system", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get tuning system",
            detail=str(e),
            suggestion="Tuning system may not be available in this Live version",
        )


@mcp.tool()
def set_tuning_system(
    ctx: Context,
    reference_pitch: float | None = None,
    note_tunings: str | None = None,
) -> str:
    """Set tuning system properties: reference pitch and note tunings.

    Parameters:
    - reference_pitch: Reference pitch in Hz (e.g., 440.0)
    - note_tunings: JSON array of cent offsets for all notes (e.g., "[0, 100, 200, ...]")
    """
    try:
        ableton = get_ableton_connection()
        params = {}
        if reference_pitch is not None:
            params["reference_pitch"] = reference_pitch
        if note_tunings is not None:
            params["note_tunings"] = json.loads(note_tunings)
        result = ableton.send_command("set_tuning_system", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set tuning system",
            detail=str(e),
            suggestion="Use get_tuning_system to see current tuning configuration",
        )


# --- Chain Direct Control ---
# (3 tools: set_chain_mute_solo, set_chain_name_color, get_chain_info)


@mcp.tool()
def set_chain_mute_solo(
    ctx: Context,
    track_index: int,
    chain_index: int,
    device_index: int = 0,
    track_type: str = "track",
    mute: bool | None = None,
    solo: bool | None = None,
) -> str:
    """Mute or solo a chain within a rack device.

    Parameters:
    - track_index: Index of the track
    - chain_index: Index of the chain within the rack
    - device_index: Index of the rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - mute: True to mute, False to unmute
    - solo: True to solo, False to unsolo
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "chain_index": chain_index,
        }
        if mute is not None:
            params["mute"] = mute
        if solo is not None:
            params["solo"] = solo
        result = ableton.send_command("set_chain_mute_solo", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set chain mute/solo",
            detail=str(e),
            suggestion="Use get_rack_chains to see available chains",
        )


@mcp.tool()
def set_chain_name_color(
    ctx: Context,
    track_index: int,
    chain_index: int,
    device_index: int = 0,
    track_type: str = "track",
    name: str | None = None,
    color_index: int | None = None,
) -> str:
    """Set chain name or color within a rack device.

    Parameters:
    - track_index: Index of the track
    - chain_index: Index of the chain within the rack
    - device_index: Index of the rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    - name: New name for the chain
    - color_index: Color index for the chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "chain_index": chain_index,
        }
        if name is not None:
            params["name"] = name
        if color_index is not None:
            params["color_index"] = color_index
        result = ableton.send_command("set_chain_name_color", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set chain name/color",
            detail=str(e),
            suggestion="Use get_rack_chains to see available chains",
        )


@mcp.tool()
def get_chain_info(
    ctx: Context,
    track_index: int,
    chain_index: int,
    device_index: int = 0,
    track_type: str = "track",
) -> str:
    """Get detailed chain info: name, color, mute, solo, mixer device state, and device count.

    Parameters:
    - track_index: Index of the track
    - chain_index: Index of the chain within the rack
    - device_index: Index of the rack device on the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "device_index": device_index,
            "track_type": track_type,
            "chain_index": chain_index,
        }
        result = ableton.send_command("get_chain_info", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get chain info",
            detail=str(e),
            suggestion="Use get_rack_chains to see available chains",
        )
