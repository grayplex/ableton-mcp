"""Groove pool tools: list grooves, get/set parameters, assign to clips."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def list_grooves(ctx: Context) -> str:
    """List all grooves currently in the groove pool."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("list_grooves")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to list grooves",
            detail=str(e),
            suggestion="Grooves must be loaded into the groove pool first (via browser or drag-and-drop)",
        )


@mcp.tool()
def get_groove_params(ctx: Context, groove_index: int) -> str:
    """Get parameters of a groove by index. Use list_grooves to find available grooves.

    Parameters:
    - groove_index: Index of the groove in the groove pool
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_groove_params", {"groove_index": groove_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get groove params",
            detail=str(e),
            suggestion="Use list_grooves to see available groove indices",
        )


@mcp.tool()
def set_groove_params(
    ctx: Context,
    groove_index: int,
    base: int | None = None,
    timing_amount: float | None = None,
    quantization_amount: float | None = None,
    random_amount: float | None = None,
    velocity_amount: float | None = None,
) -> str:
    """Set parameters of a groove. Only specified parameters are changed.

    Parameters:
    - groove_index: Index of the groove in the groove pool
    - base: Grid base (0=1/4, 1=1/8, 2=1/8T, 3=1/16, 4=1/16T, 5=1/32)
    - timing_amount: Timing groove amount
    - quantization_amount: Quantization amount
    - random_amount: Random timing amount
    - velocity_amount: Velocity groove amount
    """
    try:
        ableton = get_ableton_connection()
        params = {"groove_index": groove_index}
        if base is not None:
            params["base"] = base
        if timing_amount is not None:
            params["timing_amount"] = timing_amount
        if quantization_amount is not None:
            params["quantization_amount"] = quantization_amount
        if random_amount is not None:
            params["random_amount"] = random_amount
        if velocity_amount is not None:
            params["velocity_amount"] = velocity_amount
        result = ableton.send_command("set_groove_params", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set groove params",
            detail=str(e),
            suggestion="Use list_grooves to see available groove indices. base must be 0-5.",
        )
