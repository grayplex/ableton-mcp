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
