"""Audio clip tools: get and set audio-specific clip properties (pitch, gain, warping)."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_audio_clip_properties(ctx: Context, track_index: int, clip_index: int) -> str:
    """Get audio-specific properties of a clip (pitch, gain, warping). Only works on audio clips, not MIDI clips.

    Parameters:
    - track_index: Index of the track (regular tracks only, 0-based)
    - clip_index: Index of the clip slot (0-based)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_audio_clip_properties",
            {"track_index": track_index, "clip_index": clip_index},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get audio clip properties",
            detail=str(e),
            suggestion="Verify clip exists with get_clip_info. This tool only works on audio clips, not MIDI clips.",
        )


@mcp.tool()
def set_audio_clip_properties(
    ctx: Context,
    track_index: int,
    clip_index: int,
    pitch_coarse: int | None = None,
    pitch_fine: int | None = None,
    gain: float | None = None,
    warping: bool | None = None,
) -> str:
    """Set audio-specific properties of a clip. All parameters are optional -- set whichever you need. Only works on audio clips, not MIDI clips.

    Parameters:
    - track_index: Index of the track (regular tracks only, 0-based)
    - clip_index: Index of the clip slot (0-based)
    - pitch_coarse: Pitch transposition in semitones (-48 to 48)
    - pitch_fine: Fine pitch in cents (-500 to 500, where 100 = 1 semitone)
    - gain: Clip gain as normalized value (0.0 to 1.0). Response includes dB display string.
    - warping: True to enable warping, False to disable
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"track_index": track_index, "clip_index": clip_index}
        if pitch_coarse is not None:
            params["pitch_coarse"] = pitch_coarse
        if pitch_fine is not None:
            params["pitch_fine"] = pitch_fine
        if gain is not None:
            params["gain"] = gain
        if warping is not None:
            params["warping"] = warping
        result = ableton.send_command("set_audio_clip_properties", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set audio clip properties",
            detail=str(e),
            suggestion="Verify clip is audio (not MIDI) with get_clip_info. Ranges: pitch_coarse -48 to 48, pitch_fine -500 to 500, gain 0.0 to 1.0.",
        )
