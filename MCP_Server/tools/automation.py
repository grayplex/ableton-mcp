"""Automation tools: read, write, and clear clip automation envelopes."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_clip_envelope(
    ctx: Context,
    track_index: int,
    clip_index: int,
    device_index: int,
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
    sample_interval: float = 0.25,
) -> str:
    """Get automation envelope for a device parameter in a clip. Two modes: (1) without parameter_name/parameter_index, lists all parameters that have automation on the device; (2) with parameter_name or parameter_index, returns sampled breakpoint data for that parameter's envelope.

    Breakpoints are sampled at sample_interval beats (default 0.25 = 1/16th note). Response includes parameter min/max/value for context.

    Parameters:
    - track_index: Index of the track
    - clip_index: Index of the clip slot
    - device_index: Index of the device on the track
    - parameter_name: Parameter name for detail mode (case-insensitive)
    - parameter_index: Parameter index for detail mode
    - chain_index: Chain index for devices inside rack chains
    - chain_device_index: Device index within a rack chain
    - sample_interval: Sampling interval in beats (default 0.25)
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "clip_index": clip_index,
            "device_index": device_index,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        if sample_interval != 0.25:
            params["sample_interval"] = sample_interval
        result = ableton.send_command("get_clip_envelope", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get clip envelope",
            detail=str(e),
            suggestion="Verify clip and device exist with get_clip_info and get_device_parameters",
        )


@mcp.tool()
def insert_envelope_breakpoints(
    ctx: Context,
    track_index: int,
    clip_index: int,
    device_index: int,
    breakpoints: list[dict],
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
    step_length: float = 0.0,
) -> str:
    """Insert automation breakpoints into a clip envelope for a device parameter. Accepts a list of {time, value} pairs. Breakpoints merge with existing automation -- new breakpoints are added at specified times, existing breakpoints at other times are preserved.

    Values are clamped to the parameter's min/max range. step_length controls the duration of each step in beats (0.0 = point/instantaneous change).

    Parameters:
    - track_index: Index of the track
    - clip_index: Index of the clip slot
    - device_index: Index of the device
    - breakpoints: List of {time: float, value: float} pairs
    - parameter_name: Parameter name (case-insensitive)
    - parameter_index: Parameter index
    - chain_index: Chain index for rack chain devices
    - chain_device_index: Device index within a rack chain
    - step_length: Duration of each step in beats (default 0.0 = point)
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "clip_index": clip_index,
            "device_index": device_index,
            "breakpoints": breakpoints,
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        if step_length != 0.0:
            params["step_length"] = step_length
        result = ableton.send_command("insert_envelope_breakpoints", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to insert envelope breakpoints",
            detail=str(e),
            suggestion="Verify parameter exists with get_device_parameters. Check envelope exists with get_clip_envelope.",
        )


@mcp.tool()
def clear_clip_envelopes(
    ctx: Context,
    track_index: int,
    clip_index: int,
    device_index: int | None = None,
    parameter_name: str | None = None,
    parameter_index: int | None = None,
    chain_index: int | None = None,
    chain_device_index: int | None = None,
) -> str:
    """Clear automation envelopes from a clip. Two modes: (1) without device_index/parameter, clears ALL automation from the clip; (2) with device_index and parameter_name or parameter_index, clears only that parameter's envelope.

    Parameters:
    - track_index: Index of the track
    - clip_index: Index of the clip slot
    - device_index: Index of the device (required for single-parameter clear)
    - parameter_name: Parameter name for single clear (case-insensitive)
    - parameter_index: Parameter index for single clear
    - chain_index: Chain index for rack chain devices
    - chain_device_index: Device index within a rack chain
    """
    try:
        ableton = get_ableton_connection()
        params = {
            "track_index": track_index,
            "clip_index": clip_index,
        }
        if device_index is not None:
            params["device_index"] = device_index
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = parameter_index
        if chain_index is not None:
            params["chain_index"] = chain_index
        if chain_device_index is not None:
            params["chain_device_index"] = chain_device_index
        result = ableton.send_command("clear_clip_envelopes", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to clear clip envelopes",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )
