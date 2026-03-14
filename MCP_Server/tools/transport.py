"""Transport tools: tempo, playback start/stop."""

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def set_tempo(ctx: Context, tempo: float) -> str:
    """Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM (valid range: 20-999)
    """
    try:
        ableton = get_ableton_connection()
        ableton.send_command("set_tempo", {"tempo": tempo})
        return f"Set tempo to {tempo} BPM"
    except Exception as e:
        return format_error(
            "Failed to set tempo", detail=str(e), suggestion="Tempo must be between 20 and 999 BPM"
        )


@mcp.tool()
def start_playback(ctx: Context) -> str:
    """Start playing the Ableton session."""
    try:
        ableton = get_ableton_connection()
        ableton.send_command("start_playback")
        return "Started playback"
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
        ableton.send_command("stop_playback")
        return "Stopped playback"
    except Exception as e:
        return format_error(
            "Failed to stop playback",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )
