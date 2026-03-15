"""Transport tools: tempo, playback, time signature, loop, position, undo/redo."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp

# Module-level state for consecutive undo warning
_consecutive_undo_count = 0


@mcp.tool()
def set_tempo(ctx: Context, tempo: float) -> str:
    """Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM (valid range: 20-999)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_tempo", {"tempo": tempo})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set tempo", detail=str(e), suggestion="Tempo must be between 20 and 999 BPM"
        )


@mcp.tool()
def start_playback(ctx: Context) -> str:
    """Start playing the Ableton session from the start marker."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("start_playback")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to start playback",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def stop_playback(ctx: Context) -> str:
    """Stop playing the Ableton session."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_playback")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to stop playback",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def continue_playback(ctx: Context) -> str:
    """Resume playback from the current position (unlike start_playback which starts from the start marker)."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("continue_playback")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to continue playback",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def stop_all_clips(ctx: Context) -> str:
    """Stop all playing clips. Note: this stops clips but the song transport continues playing. Call stop_playback separately to stop the transport."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_all_clips")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to stop all clips",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def set_time_signature(ctx: Context, numerator: int, denominator: int) -> str:
    """Set the time signature. Numerator: 1-32. Denominator must be a power of 2: 1, 2, 4, 8, or 16.

    Parameters:
    - numerator: Time signature numerator (1-32)
    - denominator: Time signature denominator (must be power of 2: 1, 2, 4, 8, or 16)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_time_signature", {"numerator": numerator, "denominator": denominator}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set time signature",
            detail=str(e),
            suggestion="Numerator must be 1-32, denominator must be a power of 2 (1, 2, 4, 8, 16)",
        )


@mcp.tool()
def set_loop_region(
    ctx: Context,
    enabled: bool | None = None,
    start: float | None = None,
    length: float | None = None,
) -> str:
    """Set the song loop region. All parameters are optional -- only provided values are changed.

    Parameters:
    - enabled: Enable or disable the loop (optional)
    - start: Loop start position in beats (optional)
    - length: Loop length in beats (optional)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {}
        if enabled is not None:
            params["enabled"] = enabled
        if start is not None:
            params["start"] = start
        if length is not None:
            params["length"] = length
        result = ableton.send_command("set_loop_region", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set loop region",
            detail=str(e),
            suggestion="Verify start and length are valid beat positions",
        )


@mcp.tool()
def get_playback_position(ctx: Context) -> str:
    """Get the current playback position in beats. Returns position only (not playing status or tempo). For full transport state, use get_transport_state."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_playback_position")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get playback position",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def get_transport_state(ctx: Context) -> str:
    """Get the full transport state including: is_playing, tempo, time_signature, position, loop_enabled, loop_start, loop_length."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_transport_state")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get transport state",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def undo(ctx: Context) -> str:
    """Undo the last action in Ableton Live."""
    global _consecutive_undo_count
    try:
        _consecutive_undo_count += 1
        ableton = get_ableton_connection()
        result = ableton.send_command("undo")
        if _consecutive_undo_count >= 3:
            result["warning"] = (
                f"You have called undo {_consecutive_undo_count} times consecutively. "
                "Consider reviewing the current state before undoing further."
            )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to undo",
            detail=str(e),
            suggestion="There may be nothing to undo",
        )


@mcp.tool()
def redo(ctx: Context) -> str:
    """Redo the last undone action in Ableton Live."""
    global _consecutive_undo_count
    try:
        _consecutive_undo_count = 0
        ableton = get_ableton_connection()
        result = ableton.send_command("redo")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to redo",
            detail=str(e),
            suggestion="There may be nothing to redo",
        )
