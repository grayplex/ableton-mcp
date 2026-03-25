"""Harmonic analysis library: key detection, chord segmentation, and harmonic rhythm analysis."""

from MCP_Server.theory.pitch import _force_sharp, _format_note_name
from MCP_Server.theory.chords import identify_chord, _make_note_obj, _midi_to_pitch
from MCP_Server.theory.progressions import analyze_progression

# Lazy-loaded music21 modules (per D-19)
_stream_module = None
_note_module = None


def _get_stream_module():
    """Lazy-import music21.stream on first use."""
    global _stream_module
    if _stream_module is None:
        from music21 import stream

        _stream_module = stream
    return _stream_module


def _get_note_module():
    """Lazy-import music21.note on first use."""
    global _note_module
    if _note_module is None:
        from music21 import note

        _note_module = note
    return _note_module


def detect_key(notes):
    """Detect key from a list of note dicts [{pitch, start_time, duration, ...}].

    Returns top 3 key candidates with confidence scores (0-1).

    Args:
        notes: List of note dicts with at least 'pitch' key (MIDI number),
               optional 'duration' (defaults to 1.0)

    Returns:
        list[dict]: Up to 3 candidates, each {"key": str, "mode": str, "confidence": float}

    Raises:
        ValueError: If notes list is empty
    """
    if not notes:
        raise ValueError("No notes provided for key detection")

    stream_mod = _get_stream_module()
    note_mod = _get_note_module()

    s = stream_mod.Stream()
    for nd in notes:
        n = note_mod.Note(midi=nd["pitch"])
        n.quarterLength = nd.get("duration", 1.0)
        s.append(n)

    k = s.analyze('key')

    # Build top 3 candidates from primary + alternateInterpretations
    candidates = []

    # Primary result - apply _force_sharp for consistent sharp spelling
    tonic = _force_sharp(k.tonic)
    candidates.append({
        "key": tonic.name,
        "mode": k.mode,
        "confidence": round(max(0, k.correlationCoefficient), 4),
    })

    # Alternate interpretations
    for alt in k.alternateInterpretations:
        if len(candidates) >= 3:
            break
        alt_tonic = _force_sharp(alt.tonic)
        candidates.append({
            "key": alt_tonic.name,
            "mode": alt.mode,
            "confidence": round(max(0, alt.correlationCoefficient), 4),
        })

    return candidates


def analyze_clip_chords(notes, resolution='beat', beats_per_bar=4):
    """Segment notes into time windows and identify chord at each position.

    Args:
        notes: List of note dicts with 'pitch', 'start_time', 'duration' keys
        resolution: Time grid resolution - 'beat', 'half_beat', or 'bar'
        beats_per_bar: Beats per bar for 'bar' resolution (default 4)

    Returns:
        list[dict]: Segments with chord identification or single-note info

    Raises:
        ValueError: If notes is empty or resolution is invalid
    """
    if not notes:
        raise ValueError("No notes provided for chord analysis")

    valid_resolutions = ('beat', 'half_beat', 'bar')
    if resolution not in valid_resolutions:
        raise ValueError(
            f"Invalid resolution: '{resolution}'. Use one of: {', '.join(valid_resolutions)}"
        )

    QUANTIZE_WINDOW = 0.1  # beats tolerance for off-grid notes

    # Determine grid size in beats
    grid_size = {
        'beat': 1.0,
        'half_beat': 0.5,
        'bar': float(beats_per_bar),
    }[resolution]

    # Find time range
    max_time = max(nd["start_time"] + nd["duration"] for nd in notes)

    segments = []
    t = 0.0
    while t < max_time:
        # Collect pitches of notes that belong to this grid segment
        segment_pitches = []
        for nd in notes:
            note_start = nd["start_time"]
            # Snap to nearest grid point
            nearest_grid = round(note_start / grid_size) * grid_size
            if abs(nearest_grid - t) < 0.001:
                # Note snaps to this grid point
                segment_pitches.append(nd["pitch"])
            elif t - QUANTIZE_WINDOW <= note_start < t + grid_size:
                # Note falls within this segment's time window (with quantize tolerance)
                segment_pitches.append(nd["pitch"])

        if segment_pitches:
            unique_pitches = sorted(set(segment_pitches))
            if len(unique_pitches) >= 2:
                chord_results = identify_chord(unique_pitches)
                if chord_results:
                    top = chord_results[0]
                    segments.append({
                        "beat": t,
                        "chord": top["name"],
                        "quality": top["quality"],
                        "root": top["root"],
                        "notes": top["notes"],
                        "confidence": top["confidence"],
                    })
            else:
                # Single note - not a chord
                note_obj = _make_note_obj(_midi_to_pitch(unique_pitches[0]))
                segments.append({
                    "beat": t,
                    "chord": None,
                    "single_note": note_obj,
                })

        t += grid_size

    return segments


def analyze_harmonic_rhythm(notes, resolution='beat', beats_per_bar=4, key=None):
    """Analyze harmonic rhythm from note data.

    Returns a chord timeline with merged consecutive chords and statistics.

    Args:
        notes: List of note dicts with 'pitch', 'start_time', 'duration' keys
        resolution: Time grid resolution - 'beat', 'half_beat', or 'bar'
        beats_per_bar: Beats per bar (default 4)
        key: Optional key string for Roman numeral analysis (e.g., "C", "G")

    Returns:
        dict: {"timeline": [...], "stats": {"total_chords": int,
               "average_changes_per_bar": float, "most_common_duration": float}}
    """
    # Step 1: Get chord segments
    chord_segments = analyze_clip_chords(notes, resolution, beats_per_bar)

    # Determine grid size (same logic as analyze_clip_chords)
    grid_size = {
        'beat': 1.0,
        'half_beat': 0.5,
        'bar': float(beats_per_bar),
    }[resolution]

    # Step 2: Merge consecutive identical chords into spans
    timeline = []
    for seg in chord_segments:
        chord_name = seg.get("chord")
        if timeline and timeline[-1]["chord"] == chord_name:
            # Extend the previous entry's duration
            timeline[-1]["duration"] += grid_size
        else:
            entry = {
                "chord": chord_name,
                "start_beat": seg["beat"],
                "duration": grid_size,
            }
            # Carry root for progression analysis (root is a simple note name like "C")
            if "root" in seg:
                entry["root"] = seg["root"]
            # Carry single_note through if present
            if "single_note" in seg:
                entry["single_note"] = seg["single_note"]
            timeline.append(entry)

    # Step 3: Optional Roman numeral analysis
    if key and timeline:
        # Extract chord root names from timeline entries that have non-null chords
        # Use root (e.g., "C") for analyze_progression, not full chord name (e.g., "C-major triad")
        chord_entries = [(i, t) for i, t in enumerate(timeline) if t["chord"] is not None]
        if chord_entries:
            chord_names = [t.get("root", t["chord"]) for _, t in chord_entries]
            try:
                roman_analysis = analyze_progression(chord_names, key)
                # Merge Roman numerals back into timeline entries
                for (idx, _), analysis in zip(chord_entries, roman_analysis):
                    timeline[idx]["numeral"] = analysis.get("numeral", "?")
            except (ValueError, Exception):
                pass  # If analysis fails, just skip Roman numerals

    # Step 4: Compute statistics
    # Count chords (non-null chord entries)
    chord_timeline = [t for t in timeline if t["chord"] is not None]
    total_chords = len(chord_timeline)

    # Compute max_time for average changes per bar
    max_time = max(nd["start_time"] + nd["duration"] for nd in notes)
    total_bars = max_time / beats_per_bar if beats_per_bar > 0 else 1

    average_changes_per_bar = round(total_chords / total_bars, 2) if total_bars > 0 else 0.0

    # Most common duration (mode)
    if timeline:
        durations = [t["duration"] for t in timeline]
        most_common_duration = max(set(durations), key=durations.count)
    else:
        most_common_duration = 0.0

    return {
        "timeline": timeline,
        "stats": {
            "total_chords": total_chords,
            "average_changes_per_bar": average_changes_per_bar,
            "most_common_duration": most_common_duration,
        },
    }
