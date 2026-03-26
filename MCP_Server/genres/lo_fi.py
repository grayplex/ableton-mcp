"""Lo-fi genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

Lo-fi with three subgenres: lo-fi hip-hop, chillhop, and lo-fi jazz.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Lo-fi",
    "id": "lo_fi",
    "bpm_range": [60, 95],
    "aliases": ["lo-fi", "lofi", "lo_fi", "lo fi", "lo-fi music"],
    "instrumentation": {
        "roles": [
            "vinyl_noise", "piano", "keys", "bass", "guitar",
            "kick", "snare", "hi-hats", "sample", "pad", "fx",
        ]
    },
    "harmony": {
        "scales": ["dorian", "natural_minor", "mixolydian", "major"],
        "chord_types": ["min7", "maj7", "min9", "maj9", "dom7", "add9", "9"],
        "common_progressions": [
            ["ii", "V", "I"],
            ["i", "iv", "bVII"],
            ["vi", "ii", "V", "I"],
            ["I", "vi", "IV", "V"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [60, 95],
        "swing": "heavy",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "lazy kick and snare with heavy swing, gentle hi-hats, subtle percussion",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 4},
            {"name": "loop_a", "bars": 16},
            {"name": "loop_b", "bars": 16},
            {"name": "loop_a2", "bars": 16},
            {"name": "loop_b2", "bars": 16},
            {"name": "outro", "bars": 4},
        ]
    },
    "mixing": {
        "frequency_focus": "warm bass 60-120Hz, mellow mids 300-1kHz, rolled-off highs above 12kHz",
        "stereo_field": "mono bass, wide ambient textures and reverb, centered drums",
        "common_effects": ["vinyl crackle", "tape saturation", "reverb", "chorus", "bitcrusher", "low-pass filter"],
        "compression_style": "gentle compression, analog warmth, no aggressive limiting",
    },
    "production_tips": {
        "techniques": [
            "add vinyl crackle and tape hiss for warmth and texture",
            "use jazz and soul samples with heavy processing",
            "detune samples slightly for nostalgic character",
            "apply sidechain compression subtly for gentle pump",
            "roll off highs with low-pass filter for lo-fi warmth",
        ],
        "pitfalls": [
            "too much vinyl noise becoming distracting",
            "drums too polished for the lo-fi aesthetic",
            "low-end too boomy from uncontrolled bass",
            "over-detuning making it sound broken rather than warm",
        ],
    },
}

SUBGENRES = {
    "lo_fi_hip_hop": {
        "name": "Lo-fi Hip-hop",
        "bpm_range": [70, 90],
        "aliases": ["lo-fi hip hop", "lo-fi hip-hop", "lofi hip hop", "lofi hiphop"],
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [70, 90],
            "swing": "heavy",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "boom-bap influenced lazy kick and snare, shuffled hi-hats, vinyl crackle layer",
        },
    },
    "chillhop": {
        "name": "Chillhop",
        "bpm_range": [75, 95],
        "aliases": ["chillhop", "chill hop"],
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [75, 95],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "relaxed kick and snare, crisp hi-hats, light percussion accents",
        },
        "instrumentation": {
            "roles": [
                "vinyl_noise", "piano", "keys", "bass", "guitar",
                "kick", "snare", "hi-hats", "sample", "pad", "brass", "fx",
            ]
        },
    },
    "lo_fi_jazz": {
        "name": "Lo-fi Jazz",
        "bpm_range": [60, 85],
        "aliases": ["lo-fi jazz", "lofi jazz", "jazz lofi"],
        "harmony": {
            "scales": ["dorian", "mixolydian", "major", "lydian"],
            "chord_types": ["maj7", "min7", "maj9", "min9", "dom7", "9", "13", "add9"],
            "common_progressions": [
                ["ii", "V", "I"],
                ["iii", "vi", "ii", "V"],
                ["I", "vi", "ii", "V"],
                ["i", "iv", "bVII", "bIII"],
            ],
        },
        "instrumentation": {
            "roles": [
                "vinyl_noise", "piano", "upright_bass", "guitar", "saxophone",
                "kick", "snare", "hi-hats", "brush_drums", "pad", "fx",
            ]
        },
    },
}
