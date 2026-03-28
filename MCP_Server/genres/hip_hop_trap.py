"""Hip-hop/Trap genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

Hip-hop/Trap with two subgenres: boom bap and trap.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Hip-hop/Trap",
    "id": "hip_hop_trap",
    "bpm_range": [70, 160],
    "aliases": ["hip hop", "hiphop", "hip_hop", "trap", "rap"],
    "instrumentation": {
        "roles": [
            "kick", "808_bass", "hi-hats", "snare", "clap",
            "vocal", "sample", "pad", "lead", "fx", "percussion",
        ]
    },
    "harmony": {
        "scales": ["natural_minor", "minor_pentatonic", "blues", "dorian", "mixolydian"],
        "chord_types": ["min7", "maj7", "dom7", "min9", "dim7", "add9"],
        "common_progressions": [
            ["i", "iv", "bVI", "bVII"],
            ["i", "bVI", "bVII"],
            ["i", "iv"],
            ["IV", "I", "V", "vi"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [70, 160],
        "swing": "light",
        "note_values": ["1/4", "1/8", "1/16", "1/32"],
        "drum_pattern": "808 kick patterns, rapid hi-hat rolls, snare on 2 and 4 or syncopated",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 8, "energy": 2, "roles": ["sample", "pad", "fx"]},
            {"name": "verse", "bars": 16, "energy": 5, "roles": ["kick", "808_bass", "hi-hats", "snare", "vocal", "sample"], "transition_in": "beat drop-in"},
            {"name": "hook", "bars": 8, "energy": 8, "roles": ["kick", "808_bass", "hi-hats", "snare", "clap", "vocal", "lead", "fx"], "transition_in": "drum fill + vocal hook entry"},
            {"name": "verse2", "bars": 16, "energy": 6, "roles": ["kick", "808_bass", "hi-hats", "snare", "vocal", "sample", "pad"], "transition_in": "beat variation"},
            {"name": "hook2", "bars": 8, "energy": 8, "roles": ["kick", "808_bass", "hi-hats", "snare", "clap", "vocal", "lead", "fx"], "transition_in": "drum fill + hook return"},
            {"name": "bridge", "bars": 8, "energy": 4, "roles": ["pad", "vocal", "fx"], "transition_in": "beat strip + atmosphere"},
            {"name": "hook3", "bars": 8, "energy": 9, "roles": ["kick", "808_bass", "hi-hats", "snare", "clap", "vocal", "lead", "percussion", "fx"], "transition_in": "build + final hook"},
            {"name": "outro", "bars": 8, "energy": 3, "roles": ["sample", "pad", "fx"], "transition_in": "beat fadeout"},
        ]
    },
    "mixing": {
        "frequency_focus": "sub-bass 30-60Hz heavy 808, kick presence 60-100Hz, vocal clarity 2-5kHz",
        "stereo_field": "mono 808 bass and kick, wide ad-libs and effects, centered lead vocal",
        "common_effects": ["distortion", "reverb", "delay", "sidechain compression", "saturation"],
        "compression_style": "heavy compression on vocals, sidechain bass to kick, limiting on master",
    },
    "production_tips": {
        "techniques": [
            "layer 808s with distortion for character",
            "use hi-hat rolls with velocity variation",
            "sidechain pads to vocals",
            "use pitch slides on 808 bass",
            "chop samples for melodic hooks",
        ],
        "pitfalls": [
            "808 bass too loud masking everything",
            "hi-hat patterns too monotonous",
            "muddy low-end from 808 and kick overlap",
            "over-compressed vocals",
        ],
    },
}

SUBGENRES = {
    "boom_bap": {
        "name": "Boom Bap",
        "bpm_range": [85, 95],
        "aliases": ["boom bap", "boom_bap", "boombap"],
        "instrumentation": {
            "roles": [
                "kick", "snare", "hi-hats", "bass", "sample",
                "vocal", "scratch", "percussion",
            ]
        },
        "harmony": {
            "scales": ["natural_minor", "minor_pentatonic", "blues", "dorian"],
            "chord_types": ["min7", "maj7", "dom7", "min9"],
            "common_progressions": [
                ["i", "iv"],
                ["i", "bVI", "bVII"],
                ["ii", "V", "I"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [85, 95],
            "swing": "heavy",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "punchy kick and snare, classic boom-bap swing, simple hi-hat patterns, vinyl crackle",
        },
        "production_tips": {
            "techniques": [
                "sample jazz, soul, and funk records for melodic content",
                "add vinyl crackle and tape hiss for warmth",
                "use MPC-style swing on drums",
                "chop samples creatively for unique melodies",
            ],
            "pitfalls": [
                "samples too recognizable without creative chopping",
                "drums too clean losing the gritty character",
                "mix too polished for the aesthetic",
            ],
        },
    },
    "trap": {
        "name": "Trap",
        "bpm_range": [130, 160],
        "aliases": ["trap music"],
        "instrumentation": {
            "roles": [
                "kick", "808_bass", "hi-hats", "snare", "clap",
                "vocal", "lead", "pad", "fx", "percussion",
            ]
        },
        "harmony": {
            "scales": ["natural_minor", "phrygian", "minor_pentatonic", "blues"],
            "chord_types": ["min7", "min", "dim", "dom7"],
            "common_progressions": [
                ["i"],
                ["i", "bVI", "bVII"],
                ["i", "iv"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [130, 160],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16", "1/32"],
            "drum_pattern": "808 kick with sub-bass, rapid hi-hat rolls and triplets, hard snare on 2 and 4",
        },
        "mixing": {
            "frequency_focus": "heavy 808 sub-bass 30-50Hz, crisp hi-hats 8-14kHz, snare crack 200-500Hz",
            "stereo_field": "mono 808 bass, wide hi-hat rolls, centered snare and vocal",
            "common_effects": ["distortion", "reverb", "delay", "sidechain compression", "pitch shifting"],
            "compression_style": "heavy limiting on 808, sidechain everything to kick, aggressive master limiting",
        },
        "production_tips": {
            "techniques": [
                "use 808 slides and pitch bends for movement",
                "layer hi-hat patterns with varying velocities and rolls",
                "use dark melodies in minor keys",
                "add ad-libs and vocal chops for energy",
            ],
            "pitfalls": [
                "808 bass overwhelming the mix",
                "hi-hat rolls too repetitive",
                "melodies too busy competing with vocals",
                "clipping from excessive 808 levels",
            ],
        },
    },
}
