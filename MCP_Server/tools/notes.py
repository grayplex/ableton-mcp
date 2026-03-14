"""Note tools: get, remove, quantize, and transpose MIDI notes in clips."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_notes(ctx: Context, track_index: int, clip_index: int) -> str:
    """Get all MIDI notes from a clip. Returns notes sorted by start_time then pitch, each with pitch, start_time, duration, velocity, and mute properties.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_notes", {"track_index": track_index, "clip_index": clip_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get notes",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info",
        )


@mcp.tool()
def remove_notes(
    ctx: Context,
    track_index: int,
    clip_index: int,
    pitch_min: int | None = None,
    pitch_max: int | None = None,
    start_time_min: float | None = None,
    start_time_max: float | None = None,
) -> str:
    """Remove MIDI notes from a clip within a time and pitch range. All range parameters are optional -- omit to remove all notes.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - pitch_min: Minimum pitch to remove (optional, 0-127)
    - pitch_max: Maximum pitch to remove (optional, 0-127)
    - start_time_min: Minimum start time in beats to remove (optional)
    - start_time_max: Maximum start time in beats to remove (optional)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"track_index": track_index, "clip_index": clip_index}
        if pitch_min is not None:
            params["pitch_min"] = pitch_min
        if pitch_max is not None:
            params["pitch_max"] = pitch_max
        if start_time_min is not None:
            params["start_time_min"] = start_time_min
        if start_time_max is not None:
            params["start_time_max"] = start_time_max
        result = ableton.send_command("remove_notes", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to remove notes",
            detail=str(e),
            suggestion="Verify clip has notes with get_notes",
        )


@mcp.tool()
def quantize_notes(
    ctx: Context, track_index: int, clip_index: int, grid_size: float = 0.25, strength: float = 1.0
) -> str:
    """Quantize all MIDI notes in a clip to a grid. Grid size is in beats: 0.25 = 1/16th, 0.5 = 1/8th, 1.0 = 1/4. Strength 0.0-1.0 controls how much notes snap to grid (1.0 = full snap).

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - grid_size: Grid size in beats (default: 0.25 = 1/16th note)
    - strength: How much to snap to grid, 0.0-1.0 (default: 1.0 = full snap)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "quantize_notes",
            {"track_index": track_index, "clip_index": clip_index, "grid_size": grid_size, "strength": strength},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to quantize notes",
            detail=str(e),
            suggestion="Verify clip has notes with get_notes",
        )


@mcp.tool()
def transpose_notes(ctx: Context, track_index: int, clip_index: int, semitones: int) -> str:
    """Transpose all MIDI notes in a clip by a number of semitones. Positive = up, negative = down. Errors if any note would go outside MIDI range (0-127).

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - semitones: Number of semitones to transpose (positive = up, negative = down)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "transpose_notes",
            {"track_index": track_index, "clip_index": clip_index, "semitones": semitones},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to transpose notes",
            detail=str(e),
            suggestion="Check note ranges with get_notes before transposing. Notes must stay within 0-127.",
        )
