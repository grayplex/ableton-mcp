"""Operator instrument profile: sonic character, strengths, browser paths."""

PROFILE = {
    "id": "operator",
    "name": "Operator",
    "aliases": ["operator", "op"],
    "sonic_character": "Operator is Ableton's FM (frequency modulation) synthesizer, built around four oscillators that can modulate each other in six configurable algorithms. It produces the characteristic metallic, glassy, and percussive timbres of classic FM synthesis -- electric pianos, bells, metallic basses, and punchy leads. A filter and LFO section add classic subtractive shaping on top of the FM engine, making Operator versatile across both organic keyboard sounds and aggressive digital textures.",
    "strengths": [
        "authentic FM electric piano and bell tones",
        "punchy metallic basses and percussive sounds",
        "bright aggressive leads with harmonic complexity",
        "six configurable FM algorithms for varied timbres",
        "built-in filter and LFO for hybrid FM/subtractive shaping",
    ],
    "weaknesses": [
        "FM programming has a steep learning curve",
        "less suited for warm organic analog tones",
        "complex harmonic content can clash in dense mixes",
    ],
    "descriptor_affinities": {
        "role": {
            "keys": 0.85,
            "bass": 0.8,
            "lead": 0.75,
            "pad": 0.5,
            "texture": 0.4,
        },
        "character": {
            "bright": 0.85,
            "punchy": 0.75,
            "aggressive": 0.65,
            "warm": 0.5,
            "dark": 0.45,
            "evolving": 0.45,
        },
    },
    "browser": {
        "root": "Instruments/Operator",
        "categories": {
            "keys": "Keys",
            "bass": "Bass",
            "lead": "Leads",
            "bell": "Bell & Mallet",
            "pad": "Pads",
        },
    },
}
