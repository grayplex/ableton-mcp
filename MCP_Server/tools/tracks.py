"""Track tools: track info, creation, naming, deletion, duplication, color, and grouping."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_track_info(ctx: Context, track_index: int, track_type: str = "track") -> str:
    """Get detailed information about a specific track in Ableton.

    Parameters:
    - track_index: The index of the track to get information about
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_track_info", {"track_index": track_index, "track_type": track_type}
        )
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
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create MIDI track",
            detail=str(e),
            suggestion="Check track count with get_session_info",
        )


@mcp.tool()
def create_audio_track(ctx: Context, index: int = -1) -> str:
    """Create a new audio track in the Ableton session.

    Parameters:
    - index: Position to insert the track (-1 for end)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_audio_track", {"index": index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create audio track",
            detail=str(e),
            suggestion="Check track count with get_session_info",
        )


@mcp.tool()
def create_return_track(ctx: Context) -> str:
    """Create a new return track in the Ableton session. Always appended to end."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_return_track", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create return track",
            detail=str(e),
            suggestion="Check track count with get_session_info",
        )


@mcp.tool()
def create_group_track(ctx: Context, index: int = -1, track_indices: str = "") -> str:
    """Create a group track in the Ableton session.

    Parameters:
    - index: Position to insert the group track (-1 for end)
    - track_indices: Comma-separated track indices to group (e.g. '1,2,3'). Leave empty for an empty group.
    """
    try:
        parsed_indices = None
        if track_indices:
            parsed_indices = [int(i.strip()) for i in track_indices.split(",")]
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "create_group_track", {"index": index, "track_indices": parsed_indices}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create group track",
            detail=str(e),
            suggestion="Check track count with get_session_info",
        )


@mcp.tool()
def delete_track(ctx: Context, track_index: int, track_type: str = "track") -> str:
    """Delete a track from the Ableton session.

    Parameters:
    - track_index: Index of the track to delete
    - track_type: Type of track - 'track' (default) or 'return'. Master cannot be deleted.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "delete_track", {"track_index": track_index, "track_type": track_type}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to delete track",
            detail=str(e),
            suggestion="Verify track_index with get_all_tracks. Master track cannot be deleted.",
        )


@mcp.tool()
def duplicate_track(ctx: Context, track_index: int, new_name: str = "") -> str:
    """Duplicate a track in the Ableton session.

    Parameters:
    - track_index: Index of the track to duplicate
    - new_name: Optional name for the duplicated track. Leave empty for Ableton's default naming.
    """
    try:
        params = {"track_index": track_index}
        if new_name:
            params["new_name"] = new_name
        ableton = get_ableton_connection()
        result = ableton.send_command("duplicate_track", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to duplicate track",
            detail=str(e),
            suggestion="Verify track_index with get_all_tracks",
        )


@mcp.tool()
def set_track_name(ctx: Context, track_index: int, name: str, track_type: str = "track") -> str:
    """Rename a track in the Ableton session.

    Parameters:
    - track_index: The index of the track to rename
    - name: The new name for the track
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_name",
            {"track_index": track_index, "name": name, "track_type": track_type},
        )
        return f"Renamed track to: {result.get('name', name)}"
    except Exception as e:
        return format_error(
            "Failed to set track name",
            detail=str(e),
            suggestion="Verify track_index is valid with get_session_info",
        )


@mcp.tool()
def set_track_color(ctx: Context, track_index: int, color: str, track_type: str = "track") -> str:
    """Set the color of a track by friendly name.

    Parameters:
    - track_index: Index of the track
    - color: Color name (e.g. 'red', 'blue', 'dark_green'). Invalid names return the list of valid colors.
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_color",
            {"track_index": track_index, "color": color, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set track color",
            detail=str(e),
            suggestion="Use a valid color name. Call with an invalid name to see the full list.",
        )


@mcp.tool()
def set_group_fold(ctx: Context, track_index: int, folded: bool) -> str:
    """Fold or unfold a group track.

    Parameters:
    - track_index: Index of the group track
    - folded: True to fold (collapse), False to unfold (expand)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_group_fold", {"track_index": track_index, "folded": folded}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set group fold state",
            detail=str(e),
            suggestion="Track must be a group track (is_foldable=True). Check with get_track_info.",
        )


@mcp.tool()
def get_all_tracks(ctx: Context) -> str:
    """Get a summary list of all tracks in the session (regular, return, and master)."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_all_tracks", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get all tracks",
            detail=str(e),
            suggestion="Check connection with get_session_info",
        )
