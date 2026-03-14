"""Track tools: track info, creation, and naming."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_track_info(ctx: Context, track_index: int) -> str:
    """Get detailed information about a specific track in Ableton.

    Parameters:
    - track_index: The index of the track to get information about
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_track_info", {"track_index": track_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get track info",
            detail=str(e),
            suggestion="Verify track_index is valid with get_session_info",
        )


@mcp.tool()
def create_midi_track(ctx: Context, index: int = -1) -> str:
    """Create a new MIDI track in the Ableton session.

    Parameters:
    - index: Position to insert the track (-1 for end)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_midi_track", {"index": index})
        return f"Created new MIDI track: {result.get('name', 'unknown')}"
    except Exception as e:
        return format_error(
            "Failed to create MIDI track",
            detail=str(e),
            suggestion="Check track count with get_session_info",
        )


@mcp.tool()
def set_track_name(ctx: Context, track_index: int, name: str) -> str:
    """Rename a track in the Ableton session.

    Parameters:
    - track_index: The index of the track to rename
    - name: The new name for the track
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_name", {"track_index": track_index, "name": name})
        return f"Renamed track to: {result.get('name', name)}"
    except Exception as e:
        return format_error(
            "Failed to set track name",
            detail=str(e),
            suggestion="Verify track_index is valid with get_session_info",
        )
