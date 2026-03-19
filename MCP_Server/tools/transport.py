"""Transport tools: tempo, playback, time signature, loop, position, undo/redo."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp

# Module-level state for consecutive undo warning
_consecutive_undo_count = 0


@mcp.tool()
def set_tempo(ctx: Context, tempo: float) -> str:
    """Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM (valid range: 20-999)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_tempo", {"tempo": tempo})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set tempo", detail=str(e), suggestion="Tempo must be between 20 and 999 BPM"
        )


@mcp.tool()
def start_playback(ctx: Context) -> str:
    """Start playing the Ableton session from the start marker."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("start_playback")
        return json.dumps(result, indent=2)
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
        result = ableton.send_command("stop_playback")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to stop playback",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def continue_playback(ctx: Context) -> str:
    """Resume playback from the current position (unlike start_playback which starts from the start marker)."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("continue_playback")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to continue playback",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def stop_all_clips(ctx: Context) -> str:
    """Stop all playing clips. Note: this stops clips but the song transport continues playing. Call stop_playback separately to stop the transport."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_all_clips")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to stop all clips",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def set_time_signature(ctx: Context, numerator: int, denominator: int) -> str:
    """Set the time signature. Numerator: 1-32. Denominator must be a power of 2: 1, 2, 4, 8, or 16.

    Parameters:
    - numerator: Time signature numerator (1-32)
    - denominator: Time signature denominator (must be power of 2: 1, 2, 4, 8, or 16)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_time_signature", {"numerator": numerator, "denominator": denominator}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set time signature",
            detail=str(e),
            suggestion="Numerator must be 1-32, denominator must be a power of 2 (1, 2, 4, 8, 16)",
        )


@mcp.tool()
def set_loop_region(
    ctx: Context,
    enabled: bool | None = None,
    start: float | None = None,
    length: float | None = None,
) -> str:
    """Set the song loop region. All parameters are optional -- only provided values are changed.

    Parameters:
    - enabled: Enable or disable the loop (optional)
    - start: Loop start position in beats (optional)
    - length: Loop length in beats (optional)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {}
        if enabled is not None:
            params["enabled"] = enabled
        if start is not None:
            params["start"] = start
        if length is not None:
            params["length"] = length
        result = ableton.send_command("set_loop_region", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set loop region",
            detail=str(e),
            suggestion="Verify start and length are valid beat positions",
        )


@mcp.tool()
def get_playback_position(ctx: Context) -> str:
    """Get the current playback position in beats. Returns position only (not playing status or tempo). For full transport state, use get_transport_state."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_playback_position")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get playback position",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def get_transport_state(ctx: Context) -> str:
    """Get the full transport state including: is_playing, tempo, time_signature, position, loop_enabled, loop_start, loop_length."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_transport_state")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get transport state",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def undo(ctx: Context) -> str:
    """Undo the last action in Ableton Live."""
    global _consecutive_undo_count
    try:
        _consecutive_undo_count += 1
        ableton = get_ableton_connection()
        result = ableton.send_command("undo")
        if _consecutive_undo_count >= 3:
            result["warning"] = (
                f"You have called undo {_consecutive_undo_count} times consecutively. "
                "Consider reviewing the current state before undoing further."
            )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to undo",
            detail=str(e),
            suggestion="There may be nothing to undo",
        )


@mcp.tool()
def redo(ctx: Context) -> str:
    """Redo the last undone action in Ableton Live."""
    global _consecutive_undo_count
    try:
        _consecutive_undo_count = 0
        ableton = get_ableton_connection()
        result = ableton.send_command("redo")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to redo",
            detail=str(e),
            suggestion="There may be nothing to redo",
        )


# --- Scale & Key ---


@mcp.tool()
def get_scale_info(ctx: Context) -> str:
    """Get the current scale/key settings: root_note (0-11, C=0), scale_name, scale_intervals, and scale_mode."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_scale_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get scale info",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def set_scale(
    ctx: Context,
    root_note: int | None = None,
    scale_name: str | None = None,
    scale_mode: int | None = None,
) -> str:
    """Set scale/key properties. All parameters are optional -- only provided values are changed.

    Parameters:
    - root_note: Root note as integer 0-11 (C=0, C#=1, D=2, ... B=11)
    - scale_name: Scale name (e.g. "Major", "Minor", "Dorian")
    - scale_mode: Scale mode index
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {}
        if root_note is not None:
            params["root_note"] = root_note
        if scale_name is not None:
            params["scale_name"] = scale_name
        if scale_mode is not None:
            params["scale_mode"] = scale_mode
        result = ableton.send_command("set_scale", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set scale",
            detail=str(e),
            suggestion="root_note must be 0-11, scale_name must be a valid Ableton scale name",
        )


# --- Cue Points ---


@mcp.tool()
def get_cue_points(ctx: Context) -> str:
    """Get all cue points in the song. Returns a list of {name, time} objects."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_cue_points")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get cue points",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def set_or_delete_cue(ctx: Context) -> str:
    """Toggle a cue point at the current playback position. If a cue exists at the position, it is deleted; otherwise a new one is created."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_or_delete_cue")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to toggle cue point",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def jump_to_cue(
    ctx: Context,
    direction: str = "next",
    index: int | None = None,
) -> str:
    """Jump to a cue point. Either jump to next/prev cue, or jump to a specific cue by index.

    Parameters:
    - direction: "next" or "prev" (default: "next")
    - index: Jump to a specific cue point by index (overrides direction)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"direction": direction}
        if index is not None:
            params["index"] = index
        result = ableton.send_command("jump_to_cue", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to jump to cue",
            detail=str(e),
            suggestion="Use direction='next' or 'prev', or provide a valid cue index",
        )


# --- Capture ---


@mcp.tool()
def capture_scene(ctx: Context) -> str:
    """Capture currently playing clips as a new scene. Creates a new scene containing snapshots of all currently playing clips."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("capture_scene")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to capture scene",
            detail=str(e),
            suggestion="Make sure clips are currently playing",
        )


@mcp.tool()
def capture_midi(ctx: Context) -> str:
    """Capture recently played MIDI input. Records MIDI notes that were played while not recording."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("capture_midi")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to capture MIDI",
            detail=str(e),
            suggestion="Play some MIDI notes first, then capture",
        )


# --- Session Controls ---


@mcp.tool()
def tap_tempo(ctx: Context) -> str:
    """Tap tempo to set BPM by rhythm. Call multiple times in succession to establish tempo."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("tap_tempo")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to tap tempo",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def set_metronome(ctx: Context, enabled: bool) -> str:
    """Enable or disable the metronome click.

    Parameters:
    - enabled: True to enable, False to disable
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_metronome", {"enabled": enabled})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set metronome",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def set_groove_amount(ctx: Context, amount: float) -> str:
    """Set the global groove amount.

    Parameters:
    - amount: Groove amount from 0.0 to 1.0
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_groove_amount", {"amount": amount})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set groove amount",
            detail=str(e),
            suggestion="Amount must be between 0.0 and 1.0",
        )


@mcp.tool()
def set_swing_amount(ctx: Context, amount: float) -> str:
    """Set the global swing amount.

    Parameters:
    - amount: Swing amount from 0.0 to 1.0
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_swing_amount", {"amount": amount})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set swing amount",
            detail=str(e),
            suggestion="Amount must be between 0.0 and 1.0",
        )


@mcp.tool()
def set_clip_trigger_quantization(ctx: Context, quantization: int) -> str:
    """Set the clip trigger quantization value.

    Parameters:
    - quantization: Quantization value 0-14 (0=None, 1=8 bars, ... 5=1 bar, 6=1/2, ... 14=1/32)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_clip_trigger_quantization", {"quantization": quantization}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set clip trigger quantization",
            detail=str(e),
            suggestion="Quantization must be between 0 and 14",
        )


@mcp.tool()
def set_session_record(
    ctx: Context,
    enabled: bool,
    record_mode: bool | None = None,
) -> str:
    """Enable or disable session recording, and optionally set the record mode.

    Parameters:
    - enabled: True to enable session recording, False to disable
    - record_mode: Optional -- True for record mode on, False for off
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"enabled": enabled}
        if record_mode is not None:
            params["record_mode"] = record_mode
        result = ableton.send_command("set_session_record", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set session record",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


# --- Navigation ---


@mcp.tool()
def jump_by(ctx: Context, beats: float) -> str:
    """Jump forward or backward in the song by a number of beats.

    Parameters:
    - beats: Number of beats to jump (positive = forward, negative = backward)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("jump_by", {"beats": beats})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to jump by beats",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )


@mcp.tool()
def play_selection(ctx: Context) -> str:
    """Play the current arrangement selection."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("play_selection")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to play selection",
            detail=str(e),
            suggestion="Select a region in the arrangement view first",
        )


@mcp.tool()
def get_song_length(ctx: Context) -> str:
    """Get the total song length and last event time in beats."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_song_length")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get song length",
            detail=str(e),
            suggestion="Verify connection with get_connection_status",
        )
