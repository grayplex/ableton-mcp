"""Future Bass genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

Future bass with five subgenres: kawaii future, melodic future bass, chill future bass,
dark wave, and hardwave.

Per D-07: The parent genre IS the canonical future bass sound (Flume/San Holo).
No "future bass" subgenre -- the base genre covers that.
"""

GENRE = {
    "name": "Future Bass",
    "id": "future_bass",
    "bpm_range": [150, 160],
    "aliases": ["future bass", "future_bass", "futurewave"],
    "instrumentation": {
        "roles": [
            "supersaw", "bass", "kick", "snare", "hi-hats",
            "vocal_chop", "pad", "pluck", "lead", "fx", "percussion",
        ]
    },
    "harmony": {
        "scales": ["major", "natural_minor", "lydian", "mixolydian"],
        "chord_types": ["maj7", "min7", "maj9", "min9", "sus4", "add9", "7"],
        "common_progressions": [
            ["I", "V", "vi", "IV"],
            ["vi", "IV", "I", "V"],
            ["I", "iii", "vi", "IV"],
            ["IV", "I", "V", "vi"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [150, 160],
        "swing": "none",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "half-time feel snare on beat 3, sidechain kick, crisp hi-hats, snare rolls in builds",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 8, "energy": 2, "roles": ["pad", "pluck", "fx"]},
            {"name": "buildup", "bars": 8, "energy": 5, "roles": ["kick", "hi-hats", "bass", "pad", "vocal_chop", "fx"], "transition_in": "vocal chop entry + riser"},
            {"name": "drop", "bars": 16, "energy": 9, "roles": ["supersaw", "bass", "kick", "snare", "hi-hats", "vocal_chop", "lead", "fx"], "transition_in": "silence gap + supersaw wall"},
            {"name": "breakdown", "bars": 8, "energy": 3, "roles": ["pad", "pluck", "vocal_chop", "fx"], "transition_in": "drum strip + melody"},
            {"name": "buildup2", "bars": 8, "energy": 6, "roles": ["kick", "hi-hats", "bass", "pad", "vocal_chop", "fx"], "transition_in": "snare build + filter sweep"},
            {"name": "drop2", "bars": 16, "energy": 10, "roles": ["supersaw", "bass", "kick", "snare", "hi-hats", "vocal_chop", "lead", "percussion", "fx"], "transition_in": "impact + layered supersaw drop"},
            {"name": "outro", "bars": 8, "energy": 2, "roles": ["pad", "pluck", "fx"], "transition_in": "fadeout + reverb tail"},
        ]
    },
    "mixing": {
        "frequency_focus": "wide supersaws 200Hz-5kHz, sub-bass 30-60Hz, vocal presence 2-6kHz, sparkle 10-16kHz",
        "stereo_field": "ultra-wide supersaws, mono bass, centered vocal chops, wide reverb tails",
        "common_effects": ["sidechain compression", "reverb", "delay", "OTT multiband compression", "chorus", "pitch shifting"],
        "compression_style": "heavy sidechain on supersaws from kick, OTT for loudness, gentle bus compression",
    },
    "production_tips": {
        "techniques": [
            "layer multiple detuned supersaws for massive chord stacks",
            "use heavy sidechain compression for pumping drop effect",
            "pitch and chop vocal samples for melodic hooks",
            "automate filter cutoff and reverb for build sections",
            "use half-time drum patterns under high BPM for laid-back feel",
        ],
        "pitfalls": [
            "supersaws too wide causing mono compatibility issues",
            "drops lacking impact from insufficient contrast with breakdowns",
            "vocal chops too repetitive without variation",
            "low-end muddy from bass and kick overlap at high BPM",
        ],
    },
}

SUBGENRES = {
    "kawaii_future": {
        "name": "Kawaii Future",
        "bpm_range": [150, 160],
        "aliases": ["kawaii future", "kawaii future bass", "kawaii"],
        "harmony": {
            "scales": ["major", "lydian", "mixolydian"],
            "chord_types": ["maj7", "maj9", "add9", "sus4", "maj"],
            "common_progressions": [
                ["I", "V", "vi", "IV"],
                ["IV", "V", "iii", "vi"],
                ["I", "iii", "IV", "V"],
            ],
        },
        "instrumentation": {
            "roles": [
                "supersaw", "chiptune_lead", "bass", "kick", "snare",
                "hi-hats", "vocal_chop", "pluck", "bell", "fx",
            ]
        },
    },
    "melodic_future_bass": {
        "name": "Melodic Future Bass",
        "bpm_range": [148, 160],
        "aliases": ["melodic future bass", "melodic future", "festival future bass"],
        "harmony": {
            "scales": ["natural_minor", "major", "dorian", "mixolydian"],
            "chord_types": ["min7", "maj7", "min9", "sus4", "add9", "7"],
            "common_progressions": [
                ["vi", "IV", "I", "V"],
                ["i", "bVI", "bVII", "iv"],
                ["I", "V", "vi", "IV"],
            ],
        },
    },
    "chill_future_bass": {
        "name": "Chill Future Bass",
        "bpm_range": [140, 155],
        "aliases": ["chill future bass", "chill future", "mellow future bass"],
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [140, 155],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "relaxed half-time feel, soft kick, gentle snare, airy hi-hats",
        },
        "mixing": {
            "frequency_focus": "soft sub-bass 40-80Hz, warm mids 500Hz-2kHz, airy highs 8-14kHz",
            "stereo_field": "wide pads and reverb, mono bass, spacious stereo image",
            "common_effects": ["reverb", "delay", "chorus", "sidechain compression", "low-pass filter"],
            "compression_style": "gentle sidechain, minimal limiting, warm analog-style processing",
        },
    },
    "dark_wave": {
        "name": "Dark Wave",
        "bpm_range": [130, 150],
        "aliases": ["dark wave", "darkwave future bass", "dark future bass"],
        "harmony": {
            "scales": ["natural_minor", "phrygian", "harmonic_minor"],
            "chord_types": ["min7", "min", "dim", "min7b5", "dom7", "sus4"],
            "common_progressions": [
                ["i", "bVI", "bVII"],
                ["i", "iv", "bVI"],
                ["i", "bII", "bVII"],
            ],
        },
        "mixing": {
            "frequency_focus": "dark sub-bass 30-60Hz, aggressive mids 1-4kHz, atmospheric highs",
            "stereo_field": "wide dark pads, mono bass, centered aggressive elements",
            "common_effects": ["distortion", "reverb", "delay", "sidechain compression", "bitcrusher"],
            "compression_style": "heavy compression, aggressive sidechain, dark saturated processing",
        },
    },
    "hardwave": {
        "name": "Hardwave",
        "bpm_range": [150, 165],
        "aliases": ["hardwave", "hard wave", "hard future bass"],
        "harmony": {
            "scales": ["natural_minor", "phrygian", "harmonic_minor", "minor_pentatonic"],
            "chord_types": ["min", "min7", "dom7", "dim", "sus4"],
            "common_progressions": [
                ["i", "bVII", "bVI"],
                ["i", "iv"],
                ["i", "bVI", "bVII", "iv"],
            ],
        },
        "mixing": {
            "frequency_focus": "heavy sub-bass 30-50Hz, distorted mids 1-5kHz, crisp highs 10-16kHz",
            "stereo_field": "wide distorted leads, mono bass, aggressive stereo width",
            "common_effects": ["distortion", "sidechain compression", "OTT multiband compression", "reverb", "delay"],
            "compression_style": "extremely heavy sidechain, aggressive limiting, distorted processing chain",
        },
        "production_tips": {
            "techniques": [
                "use heavy distortion on bass and leads for aggression",
                "layer multiple bass sounds for width and power",
                "use rapid sidechain pumping for intense energy",
                "combine melodic elements with aggressive processing",
            ],
            "pitfalls": [
                "distortion too harsh causing ear fatigue",
                "bass too aggressive losing musicality",
                "too much compression killing dynamics",
                "arrangement too relentless without breathing room",
            ],
        },
    },
}
