"""Synthwave genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

Synthwave with four subgenres: retrowave, darksynth, outrun, and synthpop.

Per D-01: Pure Python dicts (no classes).
Per D-02: Data only (no helper functions).
Per D-05: Subgenres live in the same file as their parent genre.
"""

GENRE = {
    "name": "Synthwave",
    "id": "synthwave",
    "bpm_range": [80, 130],
    "aliases": ["synthwave", "synth wave", "retro synth", "synthwave music"],
    "instrumentation": {
        "roles": [
            "analog_synth_pad", "bass_synth", "arpeggio_lead", "drum_machine",
            "gated_reverb_snare", "hi-hats", "clap", "lead", "fx", "strings", "percussion",
        ]
    },
    "harmony": {
        "scales": ["major", "natural_minor", "dorian", "mixolydian"],
        "chord_types": ["maj", "min", "maj7", "min7", "sus4", "add9"],
        "common_progressions": [
            ["I", "V", "vi", "IV"],
            ["i", "bVII", "bVI", "V"],
            ["vi", "IV", "I", "V"],
            ["i", "iv", "bVII", "bIII"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [80, 130],
        "swing": "none",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "four-on-the-floor or half-time kick, gated reverb snare on 2 and 4, steady 16th hi-hats",
    },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 8},
            {"name": "verse", "bars": 16},
            {"name": "chorus", "bars": 16},
            {"name": "verse2", "bars": 16},
            {"name": "chorus2", "bars": 16},
            {"name": "bridge", "bars": 8},
            {"name": "chorus3", "bars": 16},
            {"name": "outro", "bars": 8},
        ]
    },
    "mixing": {
        "frequency_focus": "warm lows 60-150Hz, lush mids 500Hz-2kHz, sparkling highs 8-14kHz from arpeggios",
        "stereo_field": "wide pads and reverb, mono bass, centered lead and drums",
        "common_effects": ["reverb", "delay", "chorus", "gated reverb", "sidechain compression"],
        "compression_style": "gated reverb on snare, light sidechain on pads, warm analog saturation",
    },
    "production_tips": {
        "techniques": [
            "use analog-style synth patches with saw and square waves",
            "layer arpeggiated sequences at different octaves",
            "apply gated reverb to snare for iconic 80s sound",
            "use slow attack pads for atmospheric washes",
            "automate filter cutoff on bass for movement",
        ],
        "pitfalls": [
            "synth patches too digital sounding — use analog emulation",
            "reverb too wet drowning the mix",
            "arpeggio patterns too busy competing with melody",
            "arrangement too repetitive without dynamic variation",
        ],
    },
}

SUBGENRES = {
    "retrowave": {
        "name": "Retrowave",
        "bpm_range": [95, 120],
        "aliases": ["retrowave", "retro wave"],
        # Retrowave: nostalgic, upbeat, pop-influenced 80s sound
    },
    "darksynth": {
        "name": "Darksynth",
        "bpm_range": [100, 130],
        "aliases": ["darksynth", "dark synth", "dark synthwave"],
        "harmony": {
            "scales": ["natural_minor", "phrygian", "harmonic_minor"],
            "chord_types": ["min", "min7", "dim", "dom7", "sus4"],
            "common_progressions": [
                ["i", "bVI", "bVII"],
                ["i", "iv", "bVI"],
                ["i", "bII", "bVII"],
            ],
        },
        "mixing": {
            "frequency_focus": "heavy sub-bass 40-80Hz, aggressive mids 1-4kHz, dark atmosphere",
            "stereo_field": "wide distorted synths, mono bass, centered drums",
            "common_effects": ["distortion", "reverb", "delay", "bitcrusher", "sidechain compression"],
            "compression_style": "aggressive compression on bass, heavy limiting, distorted synths",
        },
    },
    "outrun": {
        "name": "Outrun",
        "bpm_range": [110, 130],
        "aliases": ["outrun", "outrun electro"],
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [110, 130],
            "swing": "none",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "driving four-on-the-floor kick, energetic hi-hats, punchy snare on 2 and 4",
        },
    },
    "synthpop": {
        "name": "Synthpop",
        "bpm_range": [100, 125],
        "aliases": ["synthpop", "synth pop", "electropop"],
        "harmony": {
            "scales": ["major", "mixolydian", "dorian"],
            "chord_types": ["maj", "min", "maj7", "sus4", "add9"],
            "common_progressions": [
                ["I", "V", "vi", "IV"],
                ["I", "IV", "vi", "V"],
                ["vi", "IV", "I", "V"],
            ],
        },
    },
}
