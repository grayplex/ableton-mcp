"""Trance genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

The canonical trance genre with three subgenres: progressive trance,
uplifting, and psytrance.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Trance",
    "id": "trance",
    "bpm_range": [128, 150],
    "aliases": ["trance music"],
    "instrumentation": {
        "roles": [
            "kick", "bass", "hi-hats", "clap", "pad",
            "lead", "supersaw", "arpeggio", "vocal", "fx", "pluck",
        ]
    },
    "harmony": {
        "scales": ["natural_minor", "harmonic_minor", "lydian", "major", "dorian"],
        "chord_types": ["min", "maj", "min7", "sus4", "add9", "maj7"],
        "common_progressions": [
            ["i", "bVII", "bVI", "bVII"],
            ["i", "bVI", "bVII"],
            ["vi", "IV", "I", "V"],
            ["i", "iv", "bVII"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [128, 150],
        "swing": "none",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "four-on-the-floor kick, offbeat bass, rolling hi-hats, driving energy",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 32},
            {"name": "buildup", "bars": 16},
            {"name": "climax", "bars": 32},
            {"name": "breakdown", "bars": 32},
            {"name": "buildup2", "bars": 16},
            {"name": "climax2", "bars": 32},
            {"name": "outro", "bars": 32},
        ]
    },
    "mixing": {
        "frequency_focus": "tight sub-bass 40-80Hz, lead presence 1-4kHz, supersaw shimmer 4-10kHz",
        "stereo_field": "wide supersaws and pads, mono kick and bass, spacious reverb",
        "common_effects": [
            "reverb", "delay", "sidechain compression", "chorus", "unison detune",
        ],
        "compression_style": "heavy sidechain from kick, bus compression for glue, limiting on master",
    },
    "production_tips": {
        "techniques": [
            "use supersaw leads with unison detune for width",
            "build tension with long filter sweeps and risers",
            "use breakdown for emotional contrast",
            "layer kicks with sub for punch",
            "arpeggiate chords for movement and energy",
        ],
        "pitfalls": [
            "supersaws too wide causing mono compatibility issues",
            "breakdowns too long losing dance floor energy",
            "too many layers creating frequency buildup",
            "leads too bright causing ear fatigue",
        ],
    },
}

SUBGENRES = {
    "progressive_trance": {
        "name": "Progressive Trance",
        "bpm_range": [128, 134],
        "aliases": ["progressive trance", "prog trance"],
        "harmony": {
            "scales": ["natural_minor", "dorian", "lydian"],
            "chord_types": ["min7", "min", "sus4", "add9"],
            "common_progressions": [
                ["i", "bVI", "bVII"],
                ["i", "iv", "bVII"],
                ["i", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [128, 134],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "subtle builds, complex layering, deep grooves",
        },
    },
    "uplifting": {
        "name": "Uplifting",
        "bpm_range": [136, 142],
        "aliases": ["uplifting trance", "uplifting", "epic trance"],
        "harmony": {
            "scales": ["major", "lydian", "harmonic_minor"],
            "chord_types": ["maj", "min", "maj7", "sus4", "add9"],
            "common_progressions": [
                ["vi", "IV", "I", "V"],
                ["I", "V", "vi", "IV"],
                ["i", "bVI", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [136, 142],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "euphoric melodies, anthemic breakdowns, emotional driving energy",
        },
    },
    "psytrance": {
        "name": "Psytrance",
        "bpm_range": [140, 150],
        "aliases": ["psytrance", "psychedelic trance", "psy"],
        "harmony": {
            "scales": ["phrygian", "harmonic_minor", "natural_minor"],
            "chord_types": ["min", "min7", "dim", "sus4"],
            "common_progressions": [
                ["i"],
                ["i", "bII"],
                ["i", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [140, 150],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16", "1/3"],
            "drum_pattern": "psychedelic, rapid arpeggios, complex rhythms, triplet patterns",
        },
    },
}
