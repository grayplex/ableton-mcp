"""House genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

The canonical house genre with four subgenres: deep house, tech house,
progressive house, and acid house.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "House",
    "id": "house",
    "bpm_range": [120, 130],
    "aliases": ["house music", "house_music"],
    "instrumentation": {
        "roles": [
            "kick", "bass", "hi-hats", "clap", "snare",
            "pad", "stab", "lead", "vocal_chop", "percussion", "fx",
        ]
    },
    "harmony": {
        "scales": ["natural_minor", "dorian", "mixolydian", "major"],
        "chord_types": ["min7", "maj7", "dom7", "min9", "sus4", "add9"],
        "common_progressions": [
            ["i", "iv"],
            ["i", "bVII", "iv"],
            ["ii", "V", "I"],
            ["i", "bVI", "bVII"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [120, 130],
        "swing": "none",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "four-on-the-floor kick, offbeat closed hi-hats, clap on beats 2 and 4",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 16, "energy": 2, "roles": ["kick", "hi-hats", "pad"]},
            {"name": "buildup", "bars": 8, "energy": 5, "roles": ["kick", "hi-hats", "clap", "bass", "pad", "fx"], "transition_in": "filter sweep + riser"},
            {"name": "drop", "bars": 32, "energy": 9, "roles": ["kick", "bass", "hi-hats", "clap", "lead", "pad", "stab"], "transition_in": "impact hit + full drop"},
            {"name": "breakdown", "bars": 16, "energy": 4, "roles": ["pad", "lead", "fx"], "transition_in": "gradual strip-back"},
            {"name": "buildup2", "bars": 8, "energy": 6, "roles": ["kick", "hi-hats", "clap", "bass", "pad", "fx"], "transition_in": "snare roll + filter sweep"},
            {"name": "drop2", "bars": 32, "energy": 9, "roles": ["kick", "bass", "hi-hats", "clap", "lead", "pad", "stab", "vocal_chop"], "transition_in": "impact hit + drop"},
            {"name": "outro", "bars": 16, "energy": 3, "roles": ["kick", "hi-hats", "pad"], "transition_in": "gradual element removal"},
        ]
    },
    "mixing": {
        "frequency_focus": "sub-bass 40-80Hz, kick presence 100-200Hz, hi-hat air 8-12kHz",
        "stereo_field": "mono bass and kick, wide pads and reverb, centered vocals",
        "common_effects": ["sidechain compression", "reverb", "delay", "filter sweeps", "chorus"],
        "compression_style": "heavy sidechain on bass and pads from kick, light bus compression",
    },
    "production_tips": {
        "techniques": [
            "sidechain bass to kick for pumping effect",
            "layer kick with sub for weight",
            "use filter automation for builds and breakdowns",
            "pitch-shift vocal chops for melodic hooks",
            "automate reverb send for breakdown transitions",
        ],
        "pitfalls": [
            "muddy low-end from overlapping kick and bass frequencies",
            "over-compressed master losing dynamics",
            "hi-hat patterns too busy for the groove",
            "breakdowns too long losing energy",
        ],
    },
}

SUBGENRES = {
    "deep_house": {
        "name": "Deep House",
        "bpm_range": [118, 124],
        "aliases": ["deep house", "deep"],
        "harmony": {
            "scales": ["natural_minor", "dorian", "mixolydian"],
            "chord_types": ["min7", "maj7", "min9", "maj9", "dom7"],
            "common_progressions": [
                ["ii", "V", "I"],
                ["i", "iv", "bVII"],
                ["vi", "ii", "V", "I"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [118, 124],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "four-on-the-floor kick, shuffled hi-hats, rimshot on beat 3",
        },
        "mixing": {
            "frequency_focus": "warm sub-bass 50-90Hz, soft hi-hats, lush mid-range pads",
            "stereo_field": "wide reverb, mono bass, spacious stereo field",
            "common_effects": ["reverb", "delay", "chorus", "sidechain compression", "saturation"],
            "compression_style": "gentle sidechain, warm analog-style saturation on bass",
        },
    },
    "tech_house": {
        "name": "Tech House",
        "bpm_range": [124, 130],
        "aliases": ["tech house", "tech"],
        "instrumentation": {
            "roles": ["kick", "bass", "hi-hats", "clap", "percussion", "synth_stab", "vocal_chop", "fx"]
        },
        "harmony": {
            "scales": ["natural_minor", "dorian"],
            "chord_types": ["min7", "dom7"],
            "common_progressions": [
                ["i", "iv"],
                ["i", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [124, 130],
            "swing": "none",
            "note_values": ["1/8", "1/16", "1/32"],
            "drum_pattern": "driving kick, busy percussive hi-hats and shakers, groove-focused",
        },
    },
    "progressive_house": {
        "name": "Progressive House",
        "bpm_range": [124, 132],
        "aliases": ["progressive house", "progressive", "prog house"],
        "harmony": {
            "scales": ["natural_minor", "dorian", "lydian", "mixolydian"],
            "chord_types": ["min7", "maj7", "sus4", "add9", "min9"],
            "common_progressions": [
                ["i", "bVI", "bVII"],
                ["i", "iv", "bVII", "bIII"],
                ["vi", "IV", "I", "V"],
            ],
        },
        "arrangement": {
            "sections": [
                {"name": "intro", "bars": 32, "energy": 2, "roles": ["pad", "percussion", "fx"]},
                {"name": "buildup", "bars": 16, "energy": 5, "roles": ["kick", "bass", "pad", "lead", "fx"], "transition_in": "gradual layering + filter open"},
                {"name": "drop", "bars": 32, "energy": 8, "roles": ["kick", "bass", "hi-hats", "clap", "lead", "pad"], "transition_in": "smooth transition + full arrangement"},
                {"name": "breakdown", "bars": 32, "energy": 3, "roles": ["pad", "lead", "fx"], "transition_in": "filter close + element strip"},
                {"name": "buildup2", "bars": 16, "energy": 6, "roles": ["kick", "bass", "pad", "lead", "percussion", "fx"], "transition_in": "slow layering + rising tension"},
                {"name": "drop2", "bars": 32, "energy": 9, "roles": ["kick", "bass", "hi-hats", "clap", "lead", "pad", "stab"], "transition_in": "climactic drop"},
                {"name": "outro", "bars": 32, "energy": 2, "roles": ["pad", "percussion", "fx"], "transition_in": "long fadeout + element removal"},
            ]
        },
    },
    "acid_house": {
        "name": "Acid House",
        "bpm_range": [120, 130],
        "aliases": ["acid house", "acid"],
        "instrumentation": {
            "roles": ["kick", "303_bass", "hi-hats", "clap", "percussion", "fx"]
        },
        "harmony": {
            "scales": ["natural_minor", "blues", "minor_pentatonic"],
            "chord_types": ["min7", "dom7"],
            "common_progressions": [
                ["i"],
                ["i", "iv"],
                ["i", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [120, 130],
            "swing": "none",
            "note_values": ["1/8", "1/16"],
            "drum_pattern": "four-on-the-floor kick, raw 808/909 drums, driving 16th hi-hats",
        },
        "production_tips": {
            "techniques": [
                "use resonance and cutoff automation on 303-style bass",
                "accent patterns on bass sequencer for groove",
                "distort/saturate bass for aggression",
                "keep arrangement repetitive — hypnotic variation over time",
            ],
            "pitfalls": [
                "resonance too high causing ear fatigue",
                "arrangement too static without filter movement",
                "overproducing — acid thrives on rawness",
            ],
        },
    },
}
