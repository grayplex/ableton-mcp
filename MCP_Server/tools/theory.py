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
from MCP_Server.theory import list_scales as _list_scales
from MCP_Server.theory import get_scale_pitches as _get_scale_pitches
from MCP_Server.theory import check_notes_in_scale as _check_notes_in_scale
from MCP_Server.theory import get_related_scales as _get_related_scales
from MCP_Server.theory import detect_scales_from_notes as _detect_scales_from_notes
from MCP_Server.theory import get_common_progressions as _get_common_progressions
from MCP_Server.theory import generate_progression as _generate_progression
from MCP_Server.theory import analyze_progression as _analyze_progression
from MCP_Server.theory import suggest_next_chord as _suggest_next_chord


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
    - scale_type: "major", "minor" (natural minor), "harmonic_minor", or "melodic_minor"
    - octave: Base octave for chord pitches (default 4)
    """
    try:
        result = _get_diatonic_chords(key_name, scale_type, octave)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get diatonic chords",
            detail=str(e),
            suggestion="Use key_name like 'C', 'G', 'F#' and scale_type 'major', 'minor', 'harmonic_minor', or 'melodic_minor'",
        )


@mcp.tool()
def list_scales(ctx: Context) -> str:
    """List all available scales and modes with their interval patterns and categories.

    Returns a catalog of ~38 scales organized by category (diatonic, modal, minor_variant,
    pentatonic, blues, symmetric, bebop, world).
    """
    try:
        result = _list_scales()
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to list scales",
            detail=str(e),
            suggestion="This tool takes no parameters",
        )


@mcp.tool()
def get_scale_pitches(ctx: Context, root: str, scale_name: str, octave_start: int = 4, octave_end: int = 5) -> str:
    """Get scale degrees as MIDI pitches for a given root, scale, and octave range.

    Parameters:
    - root: Root note name (e.g., "C", "F#", "Bb")
    - scale_name: Scale name from the catalog (e.g., "major", "minor_pentatonic", "dorian")
    - octave_start: Starting octave (default 4)
    - octave_end: Ending octave (default 5)
    """
    try:
        result = _get_scale_pitches(root, scale_name, octave_start, octave_end)
        # MIDI range validation at tool boundary (D-15)
        for note in result["pitches"]:
            if not (0 <= note["midi"] <= 127):
                return format_error(
                    "Scale contains pitches outside MIDI range",
                    detail=f"{note['name']} = MIDI {note['midi']}, outside 0-127",
                    suggestion="Try a smaller octave range to keep all pitches within MIDI 0-127",
                )
        return json.dumps(result, indent=2)
    except ValueError as e:
        return format_error(
            "Invalid scale parameters",
            detail=str(e),
            suggestion="Use list_scales to see available scale names",
        )
    except Exception as e:
        return format_error(
            "Failed to get scale pitches",
            detail=str(e),
            suggestion="Check root (e.g., 'C', 'F#') and scale_name (use list_scales for options)",
        )


@mcp.tool()
def check_notes_in_scale(ctx: Context, midi_pitches: list[int], root: str, scale_name: str) -> str:
    """Check whether notes belong to a given scale. Reports in-scale and out-of-scale notes.

    Parameters:
    - midi_pitches: List of MIDI pitch numbers to check (e.g., [60, 64, 67])
    - root: Scale root note (e.g., "C", "F#")
    - scale_name: Scale name from the catalog (e.g., "major", "dorian")
    """
    try:
        # MIDI range validation at tool boundary (D-15)
        for p in midi_pitches:
            if not (0 <= p <= 127):
                return format_error(
                    "MIDI pitch out of range",
                    detail=f"Got {p}, must be 0-127",
                    suggestion="All MIDI pitch numbers must be between 0 and 127",
                )
        result = _check_notes_in_scale(midi_pitches, root, scale_name)
        return json.dumps(result, indent=2)
    except ValueError as e:
        return format_error(
            "Invalid parameters",
            detail=str(e),
            suggestion="Use list_scales to see available scale names",
        )
    except Exception as e:
        return format_error(
            "Failed to check notes in scale",
            detail=str(e),
            suggestion="Provide midi_pitches as a list of integers, root (e.g., 'C'), and scale_name",
        )


@mcp.tool()
def get_related_scales(ctx: Context, root: str, scale_name: str) -> str:
    """Get related scales: parallel (same root), relative (same key signature), and modes.

    Parameters:
    - root: Root note name (e.g., "C", "F#")
    - scale_name: Scale name from the catalog (e.g., "major", "natural_minor")
    """
    try:
        result = _get_related_scales(root, scale_name)
        return json.dumps(result, indent=2)
    except ValueError as e:
        return format_error(
            "Invalid parameters",
            detail=str(e),
            suggestion="Use list_scales to see available scale names",
        )
    except Exception as e:
        return format_error(
            "Failed to get related scales",
            detail=str(e),
            suggestion="Check root (e.g., 'C', 'F#') and scale_name (use list_scales for options)",
        )


@mcp.tool()
def detect_scales_from_notes(ctx: Context, midi_pitches: list[int]) -> str:
    """Detect which scales contain a given set of notes. Returns top 5 ranked by coverage.

    Parameters:
    - midi_pitches: List of MIDI pitch numbers (e.g., [60, 62, 64, 65, 67, 69, 71])
    """
    try:
        if not midi_pitches:
            return format_error(
                "Need at least 1 pitch to detect scales",
                detail="Got empty list",
                suggestion="Provide at least one MIDI pitch number",
            )
        # MIDI range validation at tool boundary (D-15)
        for p in midi_pitches:
            if not (0 <= p <= 127):
                return format_error(
                    "MIDI pitch out of range",
                    detail=f"Got {p}, must be 0-127",
                    suggestion="All MIDI pitch numbers must be between 0 and 127",
                )
        result = _detect_scales_from_notes(midi_pitches)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to detect scales from notes",
            detail=str(e),
            suggestion="Provide a list of valid MIDI pitch numbers (e.g., [60, 62, 64])",
        )


@mcp.tool()
def get_common_progressions(ctx: Context, key: str, genre: str | None = None, octave: int = 4) -> str:
    """Get common chord progressions by genre, resolved to MIDI pitches in a given key.

    Returns a catalog of ~25 progressions across pop, rock, jazz, blues, R&B/soul, classical,
    and EDM genres. Each progression includes Roman numerals and resolved MIDI chord data.

    Parameters:
    - key: Key to resolve progressions in (e.g., "C", "G", "F#")
    - genre: Optional genre filter (e.g., "jazz", "pop", "blues", "rock", "rnb", "classical", "edm")
    - octave: Base octave for chord pitches (default 4)
    """
    try:
        result = _get_common_progressions(key, genre, octave)
        # MIDI range validation at tool boundary (D-20)
        for prog in result:
            for chord in prog["chords"]:
                for note in chord["notes"]:
                    if not (0 <= note["midi"] <= 127):
                        return format_error(
                            "Progression contains notes outside MIDI range",
                            detail=f"{note['name']} = MIDI {note['midi']}, outside 0-127",
                            suggestion="Try a different octave to keep all notes within MIDI 0-127",
                        )
        return json.dumps(result, indent=2)
    except ValueError as e:
        return format_error(
            "Invalid parameters for get_common_progressions",
            detail=str(e),
            suggestion="Check key (e.g., 'C', 'G') and genre (e.g., 'jazz', 'pop', 'blues')",
        )
    except Exception as e:
        return format_error(
            "Failed to get common progressions",
            detail=str(e),
            suggestion="Check key (e.g., 'C', 'G') and optional genre filter",
        )


@mcp.tool()
def generate_progression(ctx: Context, key: str, numerals: list[str], scale_type: str = "major", octave: int = 4) -> str:
    """Generate a voice-led chord progression from Roman numeral input in any key and scale.

    Applies basic nearest-voice voice leading to minimize pitch movement between consecutive chords.

    Parameters:
    - key: Key root (e.g., "C", "G", "Bb")
    - numerals: List of Roman numerals (e.g., ["I", "IV", "V", "I"] or ["ii7", "V7", "I7"])
    - scale_type: Scale context (default "major"). Supports "major", "minor", "dorian", "mixolydian", etc.
    - octave: Base octave for chord pitches (default 4)
    """
    try:
        if not numerals:
            return format_error(
                "Empty numerals list",
                detail="numerals must be a non-empty list of Roman numeral strings",
                suggestion="Provide at least one Roman numeral (e.g., ['I', 'IV', 'V', 'I'])",
            )
        result = _generate_progression(key, numerals, scale_type, octave)
        # MIDI range validation at tool boundary (D-20)
        for chord in result["chords"]:
            for note in chord["notes"]:
                if not (0 <= note["midi"] <= 127):
                    return format_error(
                        "Progression contains notes outside MIDI range",
                        detail=f"{note['name']} = MIDI {note['midi']}, outside 0-127",
                        suggestion="Try a different octave to keep all notes within MIDI 0-127",
                    )
        return json.dumps(result, indent=2)
    except ValueError as e:
        return format_error(
            "Invalid parameters for generate_progression",
            detail=str(e),
            suggestion="Check key, numerals (e.g., ['I', 'IV', 'V']), and scale_type",
        )
    except Exception as e:
        return format_error(
            "Failed to generate progression",
            detail=str(e),
            suggestion="Check key (e.g., 'C', 'G') and numerals (e.g., ['I', 'IV', 'V', 'I'])",
        )


@mcp.tool()
def analyze_progression(ctx: Context, chord_names: list[str], key: str) -> str:
    """Analyze a sequence of chord names as Roman numerals in a given key.

    Detects diatonic chords, borrowed chords (bVII, bIII), and chromatic alterations.

    Parameters:
    - chord_names: List of chord name strings (e.g., ["Cmaj7", "Dm", "G7", "C"])
    - key: Analysis key (e.g., "C", "G", "F#")
    """
    try:
        if not chord_names:
            return format_error(
                "Empty chord names list",
                detail="chord_names must be a non-empty list of chord name strings",
                suggestion="Provide at least one chord name (e.g., ['C', 'F', 'G'])",
            )
        result = _analyze_progression(chord_names, key)
        return json.dumps(result, indent=2)
    except ValueError as e:
        return format_error(
            "Invalid parameters for analyze_progression",
            detail=str(e),
            suggestion="Check chord_names (e.g., ['C', 'Dm', 'G7']) and key (e.g., 'C')",
        )
    except Exception as e:
        return format_error(
            "Failed to analyze progression",
            detail=str(e),
            suggestion="Check chord_names (e.g., ['C', 'F', 'G', 'C']) and key (e.g., 'C')",
        )


@mcp.tool()
def suggest_next_chord(ctx: Context, key: str, preceding: list[str], genre: str | None = None) -> str:
    """Suggest next chords given a progression context, using hybrid theory rules and catalog patterns.

    Returns 3-5 ranked suggestions, each with a brief reason explaining the harmonic logic.

    Parameters:
    - key: Key context (e.g., "C", "G", "Bb")
    - preceding: 1-4 preceding chords as Roman numerals (e.g., ["I", "V", "vi"])
    - genre: Optional genre filter to weight catalog patterns (e.g., "jazz", "pop")
    """
    try:
        if not preceding:
            return format_error(
                "Empty preceding list",
                detail="preceding must be a non-empty list of Roman numeral strings",
                suggestion="Provide at least one preceding chord (e.g., ['I', 'V'])",
            )
        result = _suggest_next_chord(key, preceding, genre)
        return json.dumps(result, indent=2)
    except ValueError as e:
        return format_error(
            "Invalid parameters for suggest_next_chord",
            detail=str(e),
            suggestion="Check key (e.g., 'C') and preceding numerals (e.g., ['I', 'V'])",
        )
    except Exception as e:
        return format_error(
            "Failed to suggest next chord",
            detail=str(e),
            suggestion="Check key (e.g., 'C') and preceding (e.g., ['I', 'V', 'vi'])",
        )
