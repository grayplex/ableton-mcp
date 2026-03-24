"""Theory tools: music theory utilities powered by music21."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.theory import midi_to_note as _midi_to_note
from MCP_Server.theory import note_to_midi as _note_to_midi


@mcp.tool()
def midi_to_note(ctx: Context, midi_number: int, key_context: str | None = None) -> str:
    """Convert a MIDI pitch number to a note name. Returns note name, octave, and pitch class.

    Parameters:
    - midi_number: MIDI pitch number (0-127)
    - key_context: Optional key for enharmonic spelling (e.g., "Ab major"). Without key context, black keys use sharps (C#, not Db)
    """
    try:
        if not (0 <= midi_number <= 127):
            return format_error(
                "MIDI number out of range",
                detail=f"Got {midi_number}, must be 0-127",
                suggestion="MIDI pitch numbers range from 0 (C-1) to 127 (G9)",
            )
        result = _midi_to_note(midi_number, key_context=key_context)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to convert MIDI to note",
            detail=str(e),
            suggestion="Check that midi_number is a valid integer",
        )


@mcp.tool()
def note_to_midi(ctx: Context, note_name: str) -> str:
    """Convert a note name to a MIDI pitch number. Accepts standard notation like C4, Eb3, F#5.

    Parameters:
    - note_name: Note name with octave (e.g., "C4", "Eb3", "F#5")
    """
    try:
        result = _note_to_midi(note_name)
        if not (0 <= result["midi"] <= 127):
            return format_error(
                "Resulting MIDI number out of Ableton range",
                detail=f"{note_name} maps to MIDI {result['midi']}, outside 0-127",
                suggestion="Use notes in the range C-1 to G9",
            )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to convert note to MIDI",
            detail=str(e),
            suggestion="Use format like 'C4', 'Eb3', 'F#5'. Include octave number",
        )
