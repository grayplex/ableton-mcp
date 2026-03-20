"""Mixer tools: volume, pan, mute, solo, arm, and send level control."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def set_track_volume(ctx: Context, track_index: int, volume: float, track_type: str = "track") -> str:
    """Set the volume of a track.

    Parameters:
    - track_index: Index of the track
    - volume: Volume level from 0.0 (silence) to 1.0 (max). Response includes dB approximation.
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_volume",
            {"track_index": track_index, "volume": volume, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set track volume",
            detail=str(e),
            suggestion="Volume must be 0.0-1.0. Check track_index with get_all_tracks.",
        )


@mcp.tool()
def set_track_pan(ctx: Context, track_index: int, pan: float, track_type: str = "track") -> str:
    """Set the pan of a track.

    Parameters:
    - track_index: Index of the track
    - pan: Pan position from -1.0 (full left) through 0.0 (center) to 1.0 (full right)
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_pan",
            {"track_index": track_index, "pan": pan, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set track pan",
            detail=str(e),
            suggestion="Pan must be -1.0 to 1.0 (0.0 = center). Check track_index with get_all_tracks.",
        )


@mcp.tool()
def set_track_mute(ctx: Context, track_index: int, mute: bool, track_type: str = "track") -> str:
    """Set the mute state of a track.

    Parameters:
    - track_index: Index of the track
    - mute: True to mute, False to unmute
    - track_type: Type of track - 'track' (default) or 'return'. Master track cannot be muted.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_mute",
            {"track_index": track_index, "mute": mute, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set track mute",
            detail=str(e),
            suggestion="Master track cannot be muted. Check track_index with get_all_tracks.",
        )


@mcp.tool()
def set_track_solo(ctx: Context, track_index: int, solo: bool, track_type: str = "track", exclusive: bool = False) -> str:
    """Set the solo state of a track.

    Parameters:
    - track_index: Index of the track
    - solo: True to solo, False to unsolo
    - track_type: Type of track - 'track' (default) or 'return'. Master track cannot be soloed.
    - exclusive: If True, unsolos all other tracks before soloing this one
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_solo",
            {"track_index": track_index, "solo": solo, "track_type": track_type, "exclusive": exclusive},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set track solo",
            detail=str(e),
            suggestion="Master track cannot be soloed. Check track_index with get_all_tracks.",
        )


@mcp.tool()
def set_track_arm(ctx: Context, track_index: int, arm: bool, track_type: str = "track") -> str:
    """Arm or disarm a track for recording.

    Parameters:
    - track_index: Index of the track
    - arm: True to arm, False to disarm
    - track_type: Type of track - 'track' (default). Return and master tracks cannot be armed.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_track_arm",
            {"track_index": track_index, "arm": arm, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set track arm",
            detail=str(e),
            suggestion="Only MIDI and audio tracks can be armed. Group, return, and master tracks cannot be armed.",
        )


@mcp.tool()
def set_send_level(ctx: Context, track_index: int, return_index: int, level: float, track_type: str = "track") -> str:
    """Set the send level from a track to a return track.

    Parameters:
    - track_index: Index of the source track
    - return_index: Index of the destination return track (0-based, matches return track order)
    - level: Send level from 0.0 (off) to 1.0 (max). Response includes dB approximation.
    - track_type: Type of source track - 'track' (default) or 'return'. Master track has no sends.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_send_level",
            {"track_index": track_index, "return_index": return_index, "level": level, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set send level",
            detail=str(e),
            suggestion="Level must be 0.0-1.0. Check return tracks with get_all_tracks.",
        )


# --- Phase 13: Mixer Extended ---


@mcp.tool()
def set_crossfader(ctx: Context, value: float) -> str:
    """Set the crossfader position. Only available on the master track mixer.

    Parameters:
    - value: Crossfader position (use min/max from response to know range)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_crossfader", {"value": value})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set crossfader",
            detail=str(e),
            suggestion="Crossfader is only on the master track mixer",
        )


@mcp.tool()
def set_crossfade_assign(ctx: Context, track_index: int, assign: int, track_type: str = "track") -> str:
    """Set the crossfade assignment for a track.

    Parameters:
    - track_index: Index of the track
    - assign: 0=A, 1=none, 2=B
    - track_type: 'track' (default) or 'return'. Master track cannot be assigned.
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_crossfade_assign",
            {"track_index": track_index, "assign": assign, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set crossfade assignment",
            detail=str(e),
            suggestion="assign must be 0 (A), 1 (none), or 2 (B). Master track has no crossfade assignment.",
        )


@mcp.tool()
def get_panning_mode(ctx: Context, track_index: int, track_type: str = "track") -> str:
    """Get the panning mode of a track (Stereo or Split Stereo).

    Parameters:
    - track_index: Index of the track
    - track_type: 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_panning_mode",
            {"track_index": track_index, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get panning mode",
            detail=str(e),
            suggestion="Verify track_index is valid",
        )
