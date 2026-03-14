"""Clip tools: creation, naming, note editing, playback control, info, deletion, duplication, color, and loop."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def create_clip(ctx: Context, track_index: int, clip_index: int, length: float = 4.0) -> str:
    """Create a new MIDI clip in the specified track and clip slot.

    Parameters:
    - track_index: The index of the track to create the clip in
    - clip_index: The index of the clip slot to create the clip in
    - length: The length of the clip in beats (default: 4.0)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "create_clip", {"track_index": track_index, "clip_index": clip_index, "length": length}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create clip",
            detail=str(e),
            suggestion="Verify track_index and clip_index with get_track_info",
        )


@mcp.tool()
def add_notes_to_clip(
    ctx: Context, track_index: int, clip_index: int, notes: list[dict[str, int | float | bool]]
) -> str:
    """Add MIDI notes to an existing clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - notes: List of note dicts with pitch, start_time, duration, velocity, and mute
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "add_notes_to_clip",
            {"track_index": track_index, "clip_index": clip_index, "notes": notes},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to add notes to clip",
            detail=str(e),
            suggestion="Verify clip exists at the specified track and slot with get_track_info",
        )


@mcp.tool()
def set_clip_name(ctx: Context, track_index: int, clip_index: int, name: str) -> str:
    """Rename a clip in the specified track and slot.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - name: The new name for the clip
    """
    try:
        ableton = get_ableton_connection()
        ableton.send_command(
            "set_clip_name", {"track_index": track_index, "clip_index": clip_index, "name": name}
        )
        return f"Renamed clip at track {track_index}, slot {clip_index} to '{name}'"
    except Exception as e:
        return format_error(
            "Failed to set clip name",
            detail=str(e),
            suggestion="Verify clip exists at the specified track and slot with get_track_info",
        )


@mcp.tool()
def fire_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """Start playing a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("fire_clip", {"track_index": track_index, "clip_index": clip_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to fire clip",
            detail=str(e),
            suggestion="Verify clip exists at the specified track and slot with get_track_info",
        )


@mcp.tool()
def stop_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """Stop playing a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_clip", {"track_index": track_index, "clip_index": clip_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to stop clip",
            detail=str(e),
            suggestion="Verify clip exists at the specified track and slot with get_track_info",
        )


@mcp.tool()
def get_clip_info(ctx: Context, track_index: int, clip_index: int) -> str:
    """Get detailed information about a clip in the specified track and slot. Returns clip properties if occupied, or slot status if empty.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot to inspect
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_clip_info", {"track_index": track_index, "clip_index": clip_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get clip info",
            detail=str(e),
            suggestion="Verify track and clip indices with get_track_info",
        )


@mcp.tool()
def delete_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """Delete a clip from the specified track and slot.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip to delete
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("delete_clip", {"track_index": track_index, "clip_index": clip_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to delete clip",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )


@mcp.tool()
def duplicate_clip(ctx: Context, track_index: int, clip_index: int, target_track_index: int, target_clip_index: int) -> str:
    """Duplicate a clip to another slot. Target slot must be empty.

    Parameters:
    - track_index: The index of the source track
    - clip_index: The index of the source clip slot
    - target_track_index: The index of the destination track
    - target_clip_index: The index of the destination clip slot (must be empty)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "duplicate_clip",
            {
                "track_index": track_index,
                "clip_index": clip_index,
                "target_track_index": target_track_index,
                "target_clip_index": target_clip_index,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to duplicate clip",
            detail=str(e),
            suggestion="Check source clip exists with get_clip_info. Target slot must be empty -- delete existing clip first.",
        )


@mcp.tool()
def set_clip_color(ctx: Context, track_index: int, clip_index: int, color: str) -> str:
    """Set the color of a clip. Uses the same 70-color palette as set_track_color.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - color: Color name from the 70-color palette (e.g. 'red', 'blue', 'green')
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_clip_color", {"track_index": track_index, "clip_index": clip_index, "color": color}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set clip color",
            detail=str(e),
            suggestion="Use a valid color name. See set_track_color for the full palette.",
        )


@mcp.tool()
def set_clip_loop(
    ctx: Context,
    track_index: int,
    clip_index: int,
    enabled: bool | None = None,
    loop_start: float | None = None,
    loop_end: float | None = None,
    start_marker: float | None = None,
    end_marker: float | None = None,
) -> str:
    """Set loop and region properties on a clip. All parameters are optional -- only provided values are changed. Positions are in beats (float). Response echoes all current loop/marker values.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - enabled: Enable or disable looping (optional)
    - loop_start: Loop start position in beats (optional)
    - loop_end: Loop end position in beats (optional)
    - start_marker: Start marker position in beats (optional)
    - end_marker: End marker position in beats (optional)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"track_index": track_index, "clip_index": clip_index}
        if enabled is not None:
            params["enabled"] = enabled
        if loop_start is not None:
            params["loop_start"] = loop_start
        if loop_end is not None:
            params["loop_end"] = loop_end
        if start_marker is not None:
            params["start_marker"] = start_marker
        if end_marker is not None:
            params["end_marker"] = end_marker
        result = ableton.send_command("set_clip_loop", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set clip loop",
            detail=str(e),
            suggestion="Check clip exists with get_clip_info. loop_end must be > loop_start, end_marker must be > start_marker.",
        )
