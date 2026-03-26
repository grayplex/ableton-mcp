"""Dubstep genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

The canonical dubstep genre with four subgenres: brostep, riddim,
melodic dubstep, and deep dubstep.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Dubstep",
    "id": "dubstep",
    "bpm_range": [138, 150],
    "aliases": ["dubstep music"],
    "instrumentation": {
        "roles": [
            "kick", "snare", "bass", "wobble_bass", "hi-hats",
            "pad", "lead", "vocal", "fx", "percussion",
        ]
    },
    "harmony": {
        "scales": ["natural_minor", "phrygian", "minor_pentatonic", "harmonic_minor"],
        "chord_types": ["min", "min7", "dim", "sus4", "dom7"],
        "common_progressions": [
            ["i", "bVI", "bVII"],
            ["i", "iv"],
            ["i"],
            ["i", "bVII", "bVI"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [138, 150],
        "swing": "none",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "half-time feel, kick on 1, snare on 3, heavy sub-bass emphasis",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 16},
            {"name": "buildup", "bars": 16},
            {"name": "drop", "bars": 16},
            {"name": "breakdown", "bars": 16},
            {"name": "buildup2", "bars": 16},
            {"name": "drop2", "bars": 16},
            {"name": "outro", "bars": 8},
        ]
    },
    "mixing": {
        "frequency_focus": "massive sub-bass 30-60Hz, mid-bass wobble 100-400Hz, snare crack 200-500Hz",
        "stereo_field": "mono sub, mid-bass can be slightly wide, wide reverb on pads",
        "common_effects": [
            "distortion", "wobble LFO", "sidechain compression",
            "reverb", "delay", "bitcrusher",
        ],
        "compression_style": "heavy limiting on bass, sidechain everything from kick",
    },
    "production_tips": {
        "techniques": [
            "use LFO on bass filter cutoff for wobble",
            "layer multiple bass sounds for thickness",
            "use risers and impacts for build-drop transitions",
            "automate bass LFO rate for variation",
            "use silence before drops for impact",
        ],
        "pitfalls": [
            "sub-bass too loud eating headroom",
            "wobble bass phase issues in stereo",
            "drops not hitting hard due to weak buildup",
            "over-processing bass losing fundamental",
        ],
    },
}

SUBGENRES = {
    "brostep": {
        "name": "Brostep",
        "bpm_range": [140, 150],
        "aliases": ["brostep", "bro step"],
        "harmony": {
            "scales": ["natural_minor", "phrygian", "minor_pentatonic"],
            "chord_types": ["min", "min7", "dim", "dom7"],
            "common_progressions": [
                ["i", "bVI", "bVII"],
                ["i"],
                ["i", "iv"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [140, 150],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "aggressive half-time, heavy mid-range bass, complex sound design",
        },
    },
    "riddim": {
        "name": "Riddim",
        "bpm_range": [140, 150],
        "aliases": ["riddim dubstep", "riddim"],
        "harmony": {
            "scales": ["natural_minor", "phrygian"],
            "chord_types": ["min", "min7", "dim"],
            "common_progressions": [
                ["i"],
                ["i", "bVII"],
                ["i", "iv"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [140, 150],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "repetitive patterns, minimal drops, bouncy groove",
        },
    },
    "melodic_dubstep": {
        "name": "Melodic Dubstep",
        "bpm_range": [138, 145],
        "aliases": ["melodic dubstep", "melodic"],
        "harmony": {
            "scales": ["natural_minor", "lydian", "harmonic_minor"],
            "chord_types": ["min7", "maj7", "add9", "sus4"],
            "common_progressions": [
                ["i", "bVI", "bVII"],
                ["vi", "IV", "I", "V"],
                ["i", "iv", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [138, 145],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "emotional melodies, vocal-driven, half-time with melodic elements",
        },
    },
    "deep_dubstep": {
        "name": "Deep Dubstep",
        "bpm_range": [138, 142],
        "aliases": ["deep dubstep", "deep dub", "uk dubstep"],
        "harmony": {
            "scales": ["natural_minor", "phrygian", "minor_pentatonic"],
            "chord_types": ["min", "min7", "dom7"],
            "common_progressions": [
                ["i"],
                ["i", "iv"],
                ["i", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [138, 142],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "original UK sound, minimal, sub-bass focused, half-time, dark atmosphere",
        },
    },
}
