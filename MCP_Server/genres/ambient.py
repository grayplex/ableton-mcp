"""Ambient genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

Ambient with three subgenres: dark ambient, drone, and cinematic ambient.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Ambient",
    "id": "ambient",
    "bpm_range": [60, 120],
    "aliases": ["ambient music", "atmospheric"],
    "instrumentation": {
        "roles": [
            "pad", "drone", "texture", "field_recording", "bell",
            "piano", "strings", "fx", "granular", "vocal",
        ]
    },
    "harmony": {
        "scales": ["major", "lydian", "mixolydian", "dorian", "natural_minor", "major_pentatonic"],
        "chord_types": ["maj7", "min7", "add9", "sus4", "sus2", "maj9"],
        "common_progressions": [
            ["I", "IV"],
            ["I"],
            ["vi", "IV"],
            ["I", "V", "vi", "IV"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [60, 120],
        "swing": "none",
        "note_values": ["1/2", "1/4", "1/8"],
        "drum_pattern": "minimal or absent rhythm, sustained textures, slow evolution",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 16},
            {"name": "movement1", "bars": 32},
            {"name": "transition", "bars": 16},
            {"name": "movement2", "bars": 32},
            {"name": "transition2", "bars": 8},
            {"name": "movement3", "bars": 32},
            {"name": "outro", "bars": 16},
        ]
    },
    "mixing": {
        "frequency_focus": "deep sub-bass 20-60Hz, warm mids 200-800Hz, airy highs 8-16kHz",
        "stereo_field": "very wide stereo field, spatial depth through reverb layers, mono sub elements only",
        "common_effects": ["reverb", "delay", "granular processing", "filter sweeps", "spectral processing"],
        "compression_style": "minimal compression, preserve natural dynamics, gentle limiting only",
    },
    "production_tips": {
        "techniques": [
            "use long reverb tails for depth and space",
            "layer multiple textures at different frequencies",
            "use granular synthesis for evolving pads",
            "automate filter cutoffs slowly over bars",
            "use field recordings for organic texture",
        ],
        "pitfalls": [
            "too many competing textures creating mud",
            "reverb tails too long causing wash",
            "lack of movement making it static",
            "low-end buildup from sustained bass notes",
        ],
    },
}

SUBGENRES = {
    "dark_ambient": {
        "name": "Dark Ambient",
        "bpm_range": [60, 80],
        "aliases": ["dark ambient", "dark"],
        "instrumentation": {
            "roles": [
                "drone", "pad", "texture", "noise", "field_recording",
                "fx", "vocal", "granular",
            ]
        },
        "harmony": {
            "scales": ["natural_minor", "phrygian", "harmonic_minor"],
            "chord_types": ["min", "min7", "dim", "dim7"],
            "common_progressions": [
                ["i"],
                ["i", "bII"],
                ["i", "bVI"],
            ],
        },
        "mixing": {
            "frequency_focus": "dark sub-bass 20-50Hz, ominous mids 200-600Hz, sparse highs",
            "stereo_field": "wide dark textures, mono drones, unsettling spatial movement",
            "common_effects": ["reverb", "granular processing", "distortion", "pitch shifting", "convolution"],
            "compression_style": "minimal compression, preserve dynamics for tension and release",
        },
        "production_tips": {
            "techniques": [
                "use drones with slow modulation for unease",
                "layer field recordings of industrial and natural sounds",
                "use pitch shifting and granular processing for otherworldly textures",
                "create tension through dissonance and silence",
            ],
            "pitfalls": [
                "too much noise losing musical quality",
                "monotony without enough subtle variation",
                "sub-bass buildup causing listening fatigue",
            ],
        },
    },
    "drone": {
        "name": "Drone Ambient",
        "bpm_range": [0, 60],
        "aliases": ["drone music", "drone ambient"],
        "instrumentation": {
            "roles": [
                "drone", "pad", "texture", "strings", "fx", "granular",
            ]
        },
        "harmony": {
            "scales": ["lydian", "major", "dorian"],
            "chord_types": ["maj7", "sus4", "sus2"],
            "common_progressions": [
                ["I"],
                ["I", "IV"],
            ],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [0, 60],
            "swing": "none",
            "note_values": ["1/1", "1/2"],
            "drum_pattern": "no percussion, sustained tones only, glacial movement",
        },
        "mixing": {
            "frequency_focus": "deep fundamentals 30-80Hz, rich harmonics 100-2kHz, ethereal highs 4-12kHz",
            "stereo_field": "immersive wide field, slow spatial movement, layered depth",
            "common_effects": ["reverb", "delay", "granular processing", "spectral processing", "freeze"],
            "compression_style": "no compression, fully dynamic, natural sustain and decay",
        },
        "production_tips": {
            "techniques": [
                "use sustained tones with very slow modulation",
                "layer harmonically related drones for richness",
                "use spectral freeze and granular stretch for static textures",
                "explore just intonation for beating frequencies",
            ],
            "pitfalls": [
                "too static without any evolution",
                "phase cancellation from layered drones",
                "listening fatigue from unrelenting tones",
            ],
        },
    },
    "cinematic": {
        "name": "Cinematic Ambient",
        "bpm_range": [80, 120],
        "aliases": ["cinematic ambient", "film score ambient"],
        "instrumentation": {
            "roles": [
                "strings", "pad", "piano", "brass", "percussion",
                "vocal", "fx", "texture", "field_recording",
            ]
        },
        "harmony": {
            "scales": ["lydian", "major", "natural_minor", "harmonic_minor"],
            "chord_types": ["maj7", "min7", "sus4", "add9", "maj9"],
            "common_progressions": [
                ["I", "IV", "vi"],
                ["vi", "IV", "I", "V"],
                ["i", "bVI", "bIII", "bVII"],
                ["I", "V", "vi", "IV"],
            ],
        },
        "arrangement": {
            "sections": [
                {"name": "intro", "bars": 8},
                {"name": "theme", "bars": 16},
                {"name": "development", "bars": 32},
                {"name": "climax", "bars": 16},
                {"name": "resolution", "bars": 16},
                {"name": "outro", "bars": 8},
            ]
        },
        "mixing": {
            "frequency_focus": "full orchestral range 40-16kHz, cinematic sub-bass impacts 20-60Hz, clear mids 1-4kHz",
            "stereo_field": "orchestral width, depth through reverb, centered solo instruments",
            "common_effects": ["reverb", "delay", "compression", "EQ", "spatial processing"],
            "compression_style": "gentle bus compression for cohesion, preserve wide dynamic range",
        },
        "production_tips": {
            "techniques": [
                "use orchestral libraries with expression mapping",
                "build dynamic arcs from quiet to powerful",
                "layer synthetic textures under acoustic instruments",
                "use reverb to create sense of space and scale",
                "combine ambient textures with melodic themes",
            ],
            "pitfalls": [
                "too many instruments creating a wall of sound",
                "dynamics too flat losing the cinematic impact",
                "reverb masking clarity of melodic elements",
                "percussion too prominent breaking the ambient quality",
            ],
        },
    },
}
