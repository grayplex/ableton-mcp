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
    - notes: List of note dicts with required fields (pitch, start_time, duration, velocity, mute) and optional expression fields (probability 0.0-1.0, velocity_deviation -127.0 to 127.0, release_velocity 0.0-127.0)
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
def get_clip_launch_settings(ctx: Context, track_index: int, clip_index: int) -> str:
    """Get clip launch settings (mode, quantization, legato, velocity amount).

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_clip_launch_settings",
            {"track_index": track_index, "clip_index": clip_index},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get clip launch settings",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )


@mcp.tool()
def set_clip_launch_settings(
    ctx: Context,
    track_index: int,
    clip_index: int,
    launch_mode: int | None = None,
    launch_quantization: int | None = None,
    legato: bool | None = None,
    velocity_amount: float | None = None,
) -> str:
    """Set clip launch settings. All parameters optional -- only provided values are changed.

    launch_mode: 0=Trigger, 1=Gate, 2=Toggle, 3=Repeat
    launch_quantization: 0-14
    legato: bool
    velocity_amount: 0.0-1.0

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - launch_mode: Launch mode (0=Trigger, 1=Gate, 2=Toggle, 3=Repeat)
    - launch_quantization: Launch quantization (0-14)
    - legato: Enable legato mode
    - velocity_amount: Velocity amount (0.0-1.0)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"track_index": track_index, "clip_index": clip_index}
        if launch_mode is not None:
            params["launch_mode"] = launch_mode
        if launch_quantization is not None:
            params["launch_quantization"] = launch_quantization
        if legato is not None:
            params["legato"] = legato
        if velocity_amount is not None:
            params["velocity_amount"] = velocity_amount
        result = ableton.send_command("set_clip_launch_settings", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set clip launch settings",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info. launch_mode 0-3, launch_quantization 0-14, velocity_amount 0.0-1.0.",
        )


@mcp.tool()
def set_clip_muted(ctx: Context, track_index: int, clip_index: int, muted: bool) -> str:
    """Set clip muted/active state (clip activator). Different from track mute.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - muted: True to mute, False to activate
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_clip_muted",
            {"track_index": track_index, "clip_index": clip_index, "muted": muted},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set clip muted state",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )


@mcp.tool()
def crop_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """Crop clip to its loop/markers, removing content outside the loop.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "crop_clip",
            {"track_index": track_index, "clip_index": clip_index},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to crop clip",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )


@mcp.tool()
def duplicate_clip_loop(ctx: Context, track_index: int, clip_index: int) -> str:
    """Double the loop length and duplicate the content.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "duplicate_clip_loop",
            {"track_index": track_index, "clip_index": clip_index},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to duplicate clip loop",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )


@mcp.tool()
def duplicate_clip_region(
    ctx: Context,
    track_index: int,
    clip_index: int,
    region_start: float,
    region_end: float,
    destination_time: float,
) -> str:
    """Duplicate a region within a clip to a destination time.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - region_start: Start of the region to duplicate (in beats)
    - region_end: End of the region to duplicate (in beats)
    - destination_time: Time to paste the duplicated region (in beats)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "duplicate_clip_region",
            {
                "track_index": track_index,
                "clip_index": clip_index,
                "region_start": region_start,
                "region_end": region_end,
                "destination_time": destination_time,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to duplicate clip region",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )


@mcp.tool()
def set_clip_groove(
    ctx: Context,
    track_index: int,
    clip_index: int,
    groove_index: int | None = None,
) -> str:
    """Assign a groove from the groove pool to a clip, or clear the groove assignment.

    Parameters:
    - track_index: Index of the track
    - clip_index: Index of the clip slot
    - groove_index: Index of the groove in the pool (None to clear groove)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"track_index": track_index, "clip_index": clip_index}
        if groove_index is not None:
            params["groove_index"] = groove_index
        else:
            params["groove_index"] = None
        result = ableton.send_command("set_clip_groove", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set clip groove",
            detail=str(e),
            suggestion="Use list_grooves to see available grooves. Groove must be loaded in pool first.",
        )


@mcp.tool()
def create_session_audio_clip(
    ctx: Context,
    track_index: int,
    clip_index: int,
    file_path: str,
) -> str:
    """Create an audio clip in a session view clip slot from an audio file.

    Parameters:
    - track_index: Index of the track (must be an audio track)
    - clip_index: Index of the clip slot
    - file_path: Absolute path to the audio file
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "create_session_audio_clip",
            {"track_index": track_index, "clip_index": clip_index, "file_path": file_path},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create session audio clip",
            detail=str(e),
            suggestion="Track must be an audio track and not frozen. Provide an absolute file path.",
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
