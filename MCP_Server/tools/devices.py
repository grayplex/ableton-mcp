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
