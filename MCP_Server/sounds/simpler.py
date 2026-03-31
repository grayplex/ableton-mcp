"""Simpler instrument profile: sonic character, strengths, browser paths.

Per D-01: Pure Python dict (no classes).
Per D-02: Data only (no helper functions).
"""

PROFILE = {
    "id": "simpler",
    "name": "Simpler",
    "aliases": ["simpler", "smplr"],
    "sonic_character": "Simpler is Ableton's sample-based instrument, turning any audio file into a playable instrument across three modes. In Classic mode, samples are pitched chromatically for melodic playing of keys, pads, and basses. In One-Shot mode, the sample plays in full as a single trigger, ideal for drums, hits, and sound effects. In Slice mode, the sample is chopped into segments and mapped to MIDI notes for rhythmic re-arrangement and groove manipulation. Simpler's sonic character is entirely defined by the source sample -- it can replicate any instrument or texture.",
    "strengths": [
        "infinite sonic palette from any audio sample",
        "Classic mode for pitched melodic instruments from samples",
        "One-Shot mode for precise drum hits and single-trigger sounds",
        "Slice mode for rhythmic chopping and groove manipulation",
        "native Ableton integration with direct drag-and-drop from browser",
    ],
    "weaknesses": [
        "character is entirely sample-dependent -- no synthesis",
        "less suited when a consistent synthesized tone is needed",
        "complex sample prep required for high-quality pitched playback",
    ],
    "descriptor_affinities": {
        "role": {
            "keys": 0.7,
            "bass": 0.7,
            "lead": 0.65,
            "pad": 0.6,
            "texture": 0.55,
        },
        "character": {
            "organic": 0.75,
            "warm": 0.6,
            "bright": 0.6,
            "punchy": 0.5,
            "evolving": 0.4,
            "aggressive": 0.35,
        },
    },
    "browser": {
        "root": "Instruments/Simpler",
        "categories": {
            "keys": "Keys & Plucks",
            "bass": "Bass",
            "pad": "Pads",
            "one_shot": "One Shots",
        },
    },
}
