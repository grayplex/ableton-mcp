"""Neo-soul/R&B genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

The canonical neo-soul/R&B genre with three subgenres: neo soul,
contemporary R&B, and alternative R&B.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Neo-soul/R&B",
    "id": "neo_soul_rnb",
    "bpm_range": [65, 110],
    "aliases": ["neo soul", "r&b", "rnb", "neo-soul", "rhythm and blues", "neo_soul"],
    "instrumentation": {
        "roles": [
            "keys", "bass", "drums", "guitar", "vocal",
            "strings", "horn", "pad", "percussion", "fx",
        ]
    },
    "harmony": {
        "scales": ["dorian", "mixolydian", "major", "natural_minor", "minor_pentatonic", "blues"],
        "chord_types": ["min7", "maj7", "dom7", "min9", "maj9", "add9", "11", "13", "dim7"],
        "common_progressions": [
            ["ii", "V", "I"],
            ["i", "iv", "bVII"],
            ["I", "IV", "vi", "V"],
            ["ii", "V", "I", "IV"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [65, 110],
        "swing": "medium",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "laid-back groove, syncopated bass, ghost note snares, organic feel",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 8},
            {"name": "verse", "bars": 16},
            {"name": "prechorus", "bars": 8},
            {"name": "chorus", "bars": 16},
            {"name": "verse2", "bars": 16},
            {"name": "prechorus2", "bars": 8},
            {"name": "chorus2", "bars": 16},
            {"name": "bridge", "bars": 8},
            {"name": "chorus3", "bars": 16},
            {"name": "outro", "bars": 8},
        ]
    },
    "mixing": {
        "frequency_focus": "warm bass 60-150Hz, vocal warmth 200-800Hz, presence 2-5kHz, air 10-16kHz",
        "stereo_field": "centered vocals and bass, wide keys and pads, subtle stereo guitar",
        "common_effects": [
            "reverb", "delay", "saturation", "chorus", "tape emulation",
        ],
        "compression_style": "gentle vocal compression, warm bus compression, tape saturation for warmth",
    },
    "production_tips": {
        "techniques": [
            "use extended jazz chords for sophistication",
            "add ghost notes on drums for feel",
            "use analog synth warmth or tape saturation",
            "layer harmonized vocals",
            "use chromatic passing chords for color",
        ],
        "pitfalls": [
            "over-quantizing losing the human feel",
            "too many extended chords creating harmonic clutter",
            "vocals buried under thick arrangements",
            "bass too loud for the mellow vibe",
        ],
    },
}

SUBGENRES = {
    "neo_soul": {
        "name": "Neo Soul",
        "bpm_range": [70, 95],
        "aliases": ["neo soul", "neo-soul"],
        "harmony": {
            "scales": ["dorian", "mixolydian", "major"],
            "chord_types": ["min7", "maj7", "dom7", "min9", "maj9", "11"],
            "common_progressions": [
                ["ii", "V", "I"],
                ["i", "iv", "bVII"],
                ["I", "IV", "vi", "V"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [70, 95],
            "swing": "medium",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "jazz-influenced, live instruments, warm organic feel, laid-back groove",
        },
    },
    "contemporary_rnb": {
        "name": "Contemporary R&B",
        "bpm_range": [80, 110],
        "aliases": ["contemporary r&b", "modern rnb", "modern r&b"],
        "harmony": {
            "scales": ["natural_minor", "dorian", "major"],
            "chord_types": ["min7", "maj7", "dom7", "add9", "sus4"],
            "common_progressions": [
                ["I", "IV", "vi", "V"],
                ["vi", "IV", "I", "V"],
                ["ii", "V", "I"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [80, 110],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "modern production, synth-heavy, pop-influenced rhythms, polished drums",
        },
    },
    "alternative_rnb": {
        "name": "Alternative R&B",
        "bpm_range": [65, 100],
        "aliases": ["alternative r&b", "alt rnb", "alt r&b", "dark rnb"],
        "harmony": {
            "scales": ["natural_minor", "phrygian", "harmonic_minor", "dorian"],
            "chord_types": ["min7", "dim7", "dom7", "min9", "sus4"],
            "common_progressions": [
                ["i", "iv", "bVII"],
                ["i", "bVI", "bVII"],
                ["i", "iv"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [65, 100],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "darker production, electronic elements, experimental, atmospheric",
        },
    },
}
