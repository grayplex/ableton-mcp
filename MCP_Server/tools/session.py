"""Session tools: connection health and session information."""
import json
from mcp.server.fastmcp import Context
from MCP_Server.server import mcp
from MCP_Server.connection import get_ableton_connection, format_error


@mcp.tool()
def get_connection_status(ctx: Context) -> str:
    """Check connection health and get Ableton session summary.

    Returns connection state, Ableton version, and basic session info.
    Use this to verify the connection before starting work.
    """
    try:
        ableton = get_ableton_connection()
        ping_result = ableton.send_command("ping")
        session = ableton.send_command("get_session_info")
        return json.dumps({
            "connected": True,
            "ableton_version": ping_result.get("ableton_version", "unknown"),
            "tempo": session.get("tempo"),
            "track_count": session.get("track_count"),
            "return_track_count": session.get("return_track_count"),
        }, indent=2)
    except Exception as e:
        return format_error(
            "Cannot reach Ableton",
            detail=str(e),
            suggestion="Ensure Ableton is running and Remote Script is loaded in Preferences > Link/Tempo/MIDI"
        )


@mcp.tool()
def get_session_info(ctx: Context) -> str:
    """Get detailed information about the current Ableton session.

    Returns tempo, track count, track names, and other session metadata.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_session_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get session info",
            detail=str(e),
            suggestion="Verify connection with get_connection_status first"
        )
