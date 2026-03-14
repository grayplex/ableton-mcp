"""Clip tools: creation, naming, note editing, playback control."""

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
        ableton.send_command(
            "create_clip", {"track_index": track_index, "clip_index": clip_index, "length": length}
        )
        return (
            f"Created new clip at track {track_index}, slot {clip_index} with length {length} beats"
        )
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
        ableton.send_command(
            "add_notes_to_clip",
            {"track_index": track_index, "clip_index": clip_index, "notes": notes},
        )
        return f"Added {len(notes)} notes to clip at track {track_index}, slot {clip_index}"
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
        ableton.send_command("fire_clip", {"track_index": track_index, "clip_index": clip_index})
        return f"Started playing clip at track {track_index}, slot {clip_index}"
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
        ableton.send_command("stop_clip", {"track_index": track_index, "clip_index": clip_index})
        return f"Stopped clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        return format_error(
            "Failed to stop clip",
            detail=str(e),
            suggestion="Verify clip exists at the specified track and slot with get_track_info",
        )
