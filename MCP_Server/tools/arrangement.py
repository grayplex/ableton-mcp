"""Arrangement tools: arrangement clip CRUD and session-to-arrangement bridge."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def create_arrangement_midi_clip(
    ctx: Context,
    track_index: int,
    start_time: float,
    length: float,
    track_type: str = "track",
) -> str:
    """Create a MIDI clip in the arrangement view at the specified position.

    Parameters:
    - track_index: Index of the track
    - start_time: Start position in beats
    - length: Clip length in beats
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "create_arrangement_midi_clip",
            {
                "track_index": track_index,
                "start_time": start_time,
                "length": length,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create arrangement MIDI clip",
            detail=str(e),
            suggestion="Verify track_index with get_all_tracks",
        )


@mcp.tool()
def create_arrangement_audio_clip(
    ctx: Context,
    track_index: int,
    file_path: str,
    position: float,
    track_type: str = "track",
) -> str:
    """Create an audio clip in the arrangement view from a file.

    Parameters:
    - track_index: Index of the track
    - file_path: Absolute path to the audio file
    - position: Position in beats
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "create_arrangement_audio_clip",
            {
                "track_index": track_index,
                "file_path": file_path,
                "position": position,
                "track_type": track_type,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create arrangement audio clip",
            detail=str(e),
            suggestion="Verify the file path exists and track_index is valid",
        )


@mcp.tool()
def get_arrangement_clips(
    ctx: Context,
    track_index: int,
    track_type: str = "track",
) -> str:
    """Get all arrangement clips on a track.

    Parameters:
    - track_index: Index of the track
    - track_type: Track collection - "track", "return", or "master"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_arrangement_clips",
            {"track_index": track_index, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get arrangement clips",
            detail=str(e),
            suggestion="Verify track_index with get_all_tracks",
        )


@mcp.tool()
def duplicate_clip_to_arrangement(
    ctx: Context,
    track_index: int,
    clip_index: int,
    arrangement_time: float,
) -> str:
    """Copy a session clip to the arrangement at the specified time.

    Parameters:
    - track_index: Index of the track
    - clip_index: Index of the clip slot in session view
    - arrangement_time: Target position in beats on the arrangement timeline
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "duplicate_clip_to_arrangement",
            {
                "track_index": track_index,
                "clip_index": clip_index,
                "arrangement_time": arrangement_time,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to duplicate clip to arrangement",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )
