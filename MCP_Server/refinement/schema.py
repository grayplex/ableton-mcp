"""Refinement schema: TypedDicts for section state snapshots.

All types are TypedDicts — JSON-serializable without .asdict().
"""

from typing import Optional, TypedDict


class ClipSummary(TypedDict):
    """Summary of one arrangement clip within a section."""

    name: str
    start_bar: int              # 1-indexed bar in arrangement
    end_bar: int                # 1-indexed exclusive end bar
    length_bars: int
    is_audio: bool
    note_count: Optional[int]        # None for audio clips
    pitch_min: Optional[int]         # MIDI pitch 0-127, None if no notes
    pitch_max: Optional[int]
    dominant_octave: Optional[int]   # MIDI octave 0-9: (pitch_min+pitch_max)//2//12
    rhythm_density: Optional[float]  # notes per bar; None for audio or empty


class TrackStateEntry(TypedDict):
    """State for one track within a section."""

    track_name: str
    track_index: int
    role: Optional[str]         # inferred via _infer_role, None if unrecognized
    clips: list                 # list[ClipSummary]
    mix_context: dict           # {volume, pan, devices, recipe_delta}


class SectionState(TypedDict):
    """Full state snapshot of a named arrangement section."""

    section: str
    start_bar: int
    end_bar: int
    tracks: list                # list[TrackStateEntry]; empty when no clips found
    error: Optional[str]        # descriptive error or None
