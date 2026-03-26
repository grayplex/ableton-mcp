"""Drum & Bass genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

The canonical drum & bass genre with four subgenres: liquid, neurofunk,
jungle, and neuro.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Drum & Bass",
    "id": "drum_and_bass",
    "bpm_range": [160, 180],
    "aliases": ["drum and bass", "dnb", "d&b", "drum_n_bass", "drum & bass"],
    "instrumentation": {
        "roles": [
            "kick", "snare", "bass", "hi-hats", "break",
            "pad", "lead", "vocal", "fx", "percussion", "amen_break",
        ]
    },
    "harmony": {
        "scales": ["natural_minor", "dorian", "minor_pentatonic", "harmonic_minor"],
        "chord_types": ["min7", "min", "dom7", "min9", "dim"],
        "common_progressions": [
            ["i", "iv"],
            ["i", "bVII"],
            ["i", "bVI", "bVII"],
            ["i", "iv", "bVII"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [160, 180],
        "swing": "light",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "fast breakbeats, syncopated snare patterns, rapid hi-hat work, amen break chops",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 16},
            {"name": "buildup", "bars": 16},
            {"name": "drop", "bars": 32},
            {"name": "breakdown", "bars": 16},
            {"name": "buildup2", "bars": 16},
            {"name": "drop2", "bars": 32},
            {"name": "outro", "bars": 16},
        ]
    },
    "mixing": {
        "frequency_focus": "deep sub-bass 30-60Hz, snare crack 200-500Hz, hi-hat presence 8-12kHz",
        "stereo_field": "mono sub-bass, wide breaks and pads, centered lead elements",
        "common_effects": [
            "sidechain compression", "reverb", "delay", "distortion", "stereo imaging",
        ],
        "compression_style": "heavy compression on breaks, sidechain bass to kick, parallel drum compression",
    },
    "production_tips": {
        "techniques": [
            "chop and rearrange breakbeats for unique patterns",
            "use reese bass with detuned oscillators",
            "layer snare with noise for crack",
            "automate bass filter for movement",
            "use halftime sections for dynamics",
        ],
        "pitfalls": [
            "sub-bass and kick frequency masking",
            "breakbeats too busy losing groove",
            "reese bass too wide causing mono issues",
            "breakdown too long losing energy",
        ],
    },
}

SUBGENRES = {
    "liquid": {
        "name": "Liquid",
        "bpm_range": [170, 176],
        "aliases": ["liquid dnb", "liquid drum and bass", "liquid"],
        "harmony": {
            "scales": ["major", "dorian", "lydian"],
            "chord_types": ["maj7", "min7", "add9", "sus4"],
            "common_progressions": [
                ["I", "vi", "IV", "V"],
                ["ii", "V", "I"],
                ["I", "IV", "vi"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [170, 176],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "smooth rolling drums, melodic emotional feel, liquid grooves",
        },
    },
    "neurofunk": {
        "name": "Neurofunk",
        "bpm_range": [172, 178],
        "aliases": ["neurofunk", "neuro funk"],
        "harmony": {
            "scales": ["phrygian", "harmonic_minor", "natural_minor"],
            "chord_types": ["min7", "dim", "dom7", "min"],
            "common_progressions": [
                ["i", "bII"],
                ["i", "bVI", "bVII"],
                ["i"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [172, 178],
            "swing": "none",
            "note_values": ["1/8", "1/16", "1/32"],
            "drum_pattern": "technical complex breaks, heavy processing, precise rhythmic patterns",
        },
    },
    "jungle": {
        "name": "Jungle",
        "bpm_range": [160, 175],
        "aliases": ["jungle music", "jungle"],
        "harmony": {
            "scales": ["natural_minor", "minor_pentatonic"],
            "chord_types": ["min", "min7"],
            "common_progressions": [
                ["i", "iv"],
                ["i", "bVII"],
                ["i"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [160, 175],
            "swing": "medium",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "chopped amen breaks, ragga and dub influences, original breakbeat style",
        },
    },
    "neuro": {
        "name": "Neuro",
        "bpm_range": [170, 180],
        "aliases": ["neuro dnb", "neuro bass"],
        "harmony": {
            "scales": ["phrygian", "locrian", "harmonic_minor"],
            "chord_types": ["min", "dim", "dom7"],
            "common_progressions": [
                ["i"],
                ["i", "bII"],
                ["i", "bVI"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [170, 180],
            "swing": "none",
            "note_values": ["1/8", "1/16", "1/32"],
            "drum_pattern": "aggressive bass design, harder hitting, experimental heavier than neurofunk",
        },
    },
}
