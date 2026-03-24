"""Theory tools: music theory utilities powered by music21."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.theory import midi_to_note as _midi_to_note
from MCP_Server.theory import note_to_midi as _note_to_midi
from MCP_Server.theory import build_chord as _build_chord
from MCP_Server.theory import get_chord_inversions as _get_chord_inversions
from MCP_Server.theory import get_chord_voicings as _get_chord_voicings
from MCP_Server.theory import identify_chord as _identify_chord
from MCP_Server.theory import get_diatonic_chords as _get_diatonic_chords


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


@mcp.tool()
def build_chord(ctx: Context, root: str, quality: str = "maj", octave: int = 4) -> str:
    """Build a chord from root note and quality. Returns MIDI pitches and note names.

    Parameters:
    - root: Root note name (e.g., "C", "F#", "Bb")
    - quality: Chord quality (e.g., "maj", "min", "maj7", "dom7", "dim", "aug", "sus4", "9")
    - octave: Base octave (default 4, where C4 = MIDI 60)
    """
    try:
        result = _build_chord(root, quality, octave)
        # MIDI range validation at tool boundary (D-18)
        for note in result["notes"]:
            if not (0 <= note["midi"] <= 127):
                return format_error(
                    "Chord contains notes outside MIDI range",
                    detail=f"{note['name']} = MIDI {note['midi']}, outside 0-127",
                    suggestion="Try a different octave to keep all notes within MIDI 0-127",
                )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to build chord",
            detail=str(e),
            suggestion="Check root (e.g., 'C', 'F#') and quality (e.g., 'maj', 'min7', 'dom7')",
        )


@mcp.tool()
def get_chord_inversions(ctx: Context, root: str, quality: str = "maj", octave: int = 4) -> str:
    """Get all inversions of a chord. Returns root position through highest available inversion.

    Parameters:
    - root: Root note name (e.g., "C", "F#", "Bb")
    - quality: Chord quality (e.g., "maj", "min7", "dom7")
    - octave: Base octave (default 4)
    """
    try:
        result = _get_chord_inversions(root, quality, octave)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get chord inversions",
            detail=str(e),
            suggestion="Check root and quality parameters",
        )


@mcp.tool()
def get_chord_voicings(ctx: Context, root: str, quality: str = "maj", octave: int = 4) -> str:
    """Get chord voicings: close, open, drop-2, and drop-3. Drop-3 requires 4+ note chords.

    Parameters:
    - root: Root note name (e.g., "C", "F#", "Bb")
    - quality: Chord quality (e.g., "maj7", "min7", "dom7")
    - octave: Base octave (default 4)
    """
    try:
        result = _get_chord_voicings(root, quality, octave)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get chord voicings",
            detail=str(e),
            suggestion="Check root and quality parameters",
        )


@mcp.tool()
def identify_chord(ctx: Context, midi_pitches: list[int]) -> str:
    """Identify a chord from MIDI pitch numbers. Returns top 3 ranked candidates.

    Parameters:
    - midi_pitches: List of MIDI pitch numbers (e.g., [60, 64, 67] for C major)
    """
    try:
        if not midi_pitches or len(midi_pitches) < 2:
            return format_error(
                "Need at least 2 pitches to identify a chord",
                detail=f"Got {len(midi_pitches) if midi_pitches else 0} pitches",
                suggestion="Provide at least 2 MIDI pitch numbers",
            )
        for p in midi_pitches:
            if not (0 <= p <= 127):
                return format_error(
                    "MIDI pitch out of range",
                    detail=f"Got {p}, must be 0-127",
                    suggestion="All MIDI pitch numbers must be between 0 and 127",
                )
        result = _identify_chord(midi_pitches)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to identify chord",
            detail=str(e),
            suggestion="Provide a list of valid MIDI pitch numbers (e.g., [60, 64, 67])",
        )


@mcp.tool()
def get_diatonic_chords(ctx: Context, key_name: str, scale_type: str = "major", octave: int = 4) -> str:
    """Get all diatonic chords (triads and 7th chords) for a key. Includes Roman numeral labels.

    Parameters:
    - key_name: Key root (e.g., "C", "G", "F#")
    - scale_type: "major" or "minor" (natural minor)
    - octave: Base octave for chord pitches (default 4)
    """
    try:
        result = _get_diatonic_chords(key_name, scale_type, octave)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get diatonic chords",
            detail=str(e),
            suggestion="Use key_name like 'C', 'G', 'F#' and scale_type 'major' or 'minor'",
        )
