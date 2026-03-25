"""Theory engine library: music theory utilities powered by music21."""

from .pitch import midi_to_note, note_to_midi
from .chords import build_chord, get_chord_inversions, get_chord_voicings, identify_chord, get_diatonic_chords
from .scales import list_scales, get_scale_pitches, check_notes_in_scale, get_related_scales, detect_scales_from_notes
from .progressions import get_common_progressions, generate_progression, analyze_progression, suggest_next_chord
from .analysis import detect_key, analyze_clip_chords, analyze_harmonic_rhythm

__all__ = [
    "midi_to_note",
    "note_to_midi",
    "build_chord",
    "get_chord_inversions",
    "get_chord_voicings",
    "identify_chord",
    "get_diatonic_chords",
    "list_scales",
    "get_scale_pitches",
    "check_notes_in_scale",
    "get_related_scales",
    "detect_scales_from_notes",
    "get_common_progressions",
    "generate_progression",
    "analyze_progression",
    "suggest_next_chord",
    "detect_key",
    "analyze_clip_chords",
    "analyze_harmonic_rhythm",
]
