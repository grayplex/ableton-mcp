"""Techno genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

The canonical techno genre with five subgenres: minimal, industrial, melodic,
detroit, and peaktime/driving.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Techno",
    "id": "techno",
    "bpm_range": [125, 150],
    "aliases": ["techno music"],
    "instrumentation": {
        "roles": [
            "kick", "bass", "hi-hats", "clap", "snare",
            "percussion", "synth_stab", "pad", "lead", "fx", "noise",
        ]
    },
    "harmony": {
        "scales": ["natural_minor", "dorian", "phrygian", "locrian"],
        "chord_types": ["min7", "min", "dim", "sus4", "dom7"],
        "common_progressions": [
            ["i"], ["i", "iv"], ["i", "bVII"], ["i", "bVI", "bVII"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [125, 150],
        "swing": "none",
        "note_values": ["1/4", "1/8", "1/16", "1/32"],
        "drum_pattern": "four-on-the-floor kick, closed hi-hats on 16ths, clap on beats 2 and 4, layered percussion",
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
        "frequency_focus": "sub-bass 30-60Hz, kick punch 80-150Hz, hi-hat sizzle 8-14kHz",
        "stereo_field": "mono kick and bass, wide reverb on percussion, centered lead elements",
        "common_effects": ["reverb", "delay", "distortion", "filter sweeps", "sidechain compression"],
        "compression_style": "heavy sidechain on bass from kick, parallel compression on drums",
    },
    "production_tips": {
        "techniques": [
            "use long filter sweeps for builds and tension",
            "layer percussive elements for complexity and groove",
            "automate effects parameters for evolving textures",
            "use noise risers and impacts for transitions",
            "keep melodies minimal — focus on rhythm and texture",
        ],
        "pitfalls": [
            "too many melodic elements competing for attention",
            "kick and bass frequency clash in sub region",
            "builds that are too short to create tension",
            "over-processing drums losing punch",
        ],
    },
}

SUBGENRES = {
    "minimal": {
        "name": "Minimal Techno",
        "bpm_range": [128, 135],
        "aliases": ["minimal techno", "minimal"],
        "instrumentation": {
            "roles": ["kick", "bass", "hi-hats", "clap", "percussion", "fx", "noise"]
        },
        "harmony": {
            "scales": ["natural_minor", "dorian"],
            "chord_types": ["min7", "min", "sus4"],
            "common_progressions": [
                ["i"], ["i", "iv"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [128, 135],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "sparse four-on-the-floor kick, subtle hi-hats, minimal percussion layers",
        },
        "mixing": {
            "frequency_focus": "clean sub-bass 30-60Hz, sparse mid-range, subtle high-end",
            "stereo_field": "mono kick and bass, wide spatial effects, minimal stereo width",
            "common_effects": ["delay", "reverb", "filter sweeps", "sidechain compression"],
            "compression_style": "gentle sidechain, dynamic range preserved",
        },
    },
    "industrial": {
        "name": "Industrial Techno",
        "bpm_range": [135, 150],
        "aliases": ["industrial techno", "industrial"],
        "instrumentation": {
            "roles": [
                "kick", "bass", "hi-hats", "clap", "snare",
                "percussion", "noise", "fx", "distorted_synth",
            ]
        },
        "harmony": {
            "scales": ["phrygian", "locrian", "natural_minor"],
            "chord_types": ["min", "dim", "min7", "dom7"],
            "common_progressions": [
                ["i"], ["i", "bII"], ["i", "bVI", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [135, 150],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16", "1/32"],
            "drum_pattern": "pounding four-on-the-floor kick, distorted claps, aggressive hi-hat patterns, metallic percussion",
        },
        "production_tips": {
            "techniques": [
                "use heavy distortion and saturation on drums and bass",
                "layer noise textures for industrial atmosphere",
                "use bitcrushing and downsampling for grit",
                "automate distortion amount for intensity builds",
            ],
            "pitfalls": [
                "too much distortion causing ear fatigue",
                "losing groove under layers of noise",
                "harsh frequencies in 2-4kHz range",
            ],
        },
    },
    "melodic": {
        "name": "Melodic Techno",
        "bpm_range": [125, 135],
        "aliases": ["melodic techno"],
        "harmony": {
            "scales": ["natural_minor", "dorian", "lydian", "mixolydian"],
            "chord_types": ["min7", "maj7", "sus4", "add9", "min9"],
            "common_progressions": [
                ["i", "bVI", "bVII"], ["i", "iv", "bVII"],
                ["vi", "IV", "I", "V"], ["i", "bIII", "bVII", "iv"],
            ],
        },
        "arrangement": {
            "sections": [
                {"name": "intro", "bars": 32},
                {"name": "buildup", "bars": 16},
                {"name": "drop", "bars": 32},
                {"name": "breakdown", "bars": 32},
                {"name": "buildup2", "bars": 16},
                {"name": "drop2", "bars": 32},
                {"name": "outro", "bars": 16},
            ]
        },
        "production_tips": {
            "techniques": [
                "use arpeggiated synth patterns for melodic hooks",
                "layer pads for emotional depth",
                "use long reverb tails on melodic elements",
                "build tension with gradual filter opening",
            ],
            "pitfalls": [
                "melodies too complex losing the hypnotic quality",
                "too many layers muddying the mix",
                "losing the driving techno feel under melodies",
            ],
        },
    },
    "detroit": {
        "name": "Detroit Techno",
        "bpm_range": [128, 135],
        "aliases": ["detroit techno", "detroit"],
        "instrumentation": {
            "roles": [
                "kick", "bass", "hi-hats", "clap", "snare",
                "pad", "stab", "lead", "strings", "fx",
            ]
        },
        "harmony": {
            "scales": ["dorian", "natural_minor", "mixolydian"],
            "chord_types": ["min7", "dom7", "min9", "maj7", "sus4"],
            "common_progressions": [
                ["i", "iv"], ["ii", "V", "I"],
                ["i", "bVII"], ["i", "iv", "bVII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [128, 135],
            "swing": "light",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "four-on-the-floor kick, classic 808/909 drums, syncopated hi-hats, analog warmth",
        },
        "production_tips": {
            "techniques": [
                "use classic analog synth sounds (303, Juno, DX7 style)",
                "layer string pads for emotional depth",
                "use jazzy chord voicings with extensions",
                "keep arrangements evolving with subtle variation",
            ],
            "pitfalls": [
                "over-quantizing losing the human feel",
                "too clean/digital losing the analog character",
                "ignoring the soulful/emotional quality",
            ],
        },
    },
    "peaktime_driving": {
        "name": "Peaktime / Driving Techno",
        "bpm_range": [135, 145],
        "aliases": ["peaktime techno", "driving techno", "peaktime"],
        "instrumentation": {
            "roles": [
                "kick", "bass", "hi-hats", "clap", "snare",
                "percussion", "synth_stab", "fx", "noise",
            ]
        },
        "harmony": {
            "scales": ["natural_minor", "phrygian"],
            "chord_types": ["min", "min7", "sus4"],
            "common_progressions": [
                ["i"], ["i", "bVII"], ["i", "bII"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [135, 145],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16", "1/32"],
            "drum_pattern": "relentless four-on-the-floor kick, driving hi-hats, intense percussion layers, powerful clap on 2 and 4",
        },
        "arrangement": {
            "sections": [
                {"name": "intro", "bars": 16},
                {"name": "buildup", "bars": 32},
                {"name": "drop", "bars": 32},
                {"name": "breakdown", "bars": 16},
                {"name": "buildup2", "bars": 32},
                {"name": "drop2", "bars": 32},
                {"name": "outro", "bars": 16},
            ]
        },
        "production_tips": {
            "techniques": [
                "use long builds with layered percussion for maximum tension",
                "keep bass simple and powerful — single notes or octaves",
                "use risers and impacts for dramatic transitions",
                "automate energy level through percussion density",
            ],
            "pitfalls": [
                "too monotonous without enough variation",
                "builds that peak too early",
                "bass and kick fighting for sub space",
            ],
        },
    },
}
