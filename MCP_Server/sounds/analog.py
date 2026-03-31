"""Analog instrument profile: sonic character, strengths, browser paths."""

PROFILE = {
    "id": "analog",
    "name": "Analog",
    "aliases": ["analog", "al"],
    "sonic_character": "Analog is Ableton's virtual analog synthesizer, faithfully emulating classic subtractive synthesis hardware. It delivers warm, rich tones through two oscillators, two filters, and two amplifiers, each with their own envelopes. Analog excels at thick basses, warm leads, and classic keyboard sounds with authentic analog character -- tube distortion, noise generation, and per-oscillator envelope control give it organic warmth that digital synths often lack.",
    "strengths": [
        "warm authentic analog bass and lead tones",
        "rich harmonic content from dual oscillators",
        "organic character with tube saturation and noise",
        "flexible dual-filter routing for tonal shaping",
        "classic keyboard and synth pad sounds",
    ],
    "weaknesses": [
        "no wavetable morphing or FM modulation",
        "limited modulation routing compared to modular-style synths",
        "not suited for complex evolving textures or metallic timbres",
    ],
    "descriptor_affinities": {
        "role": {
            "bass": 0.85,
            "lead": 0.8,
            "keys": 0.7,
            "pad": 0.55,
            "texture": 0.3,
        },
        "character": {
            "warm": 0.9,
            "punchy": 0.7,
            "dark": 0.65,
            "bright": 0.6,
            "aggressive": 0.6,
            "evolving": 0.3,
        },
    },
    "browser": {
        "root": "Instruments/Analog",
        "categories": {
            "bass": "Bass",
            "lead": "Leads",
            "keys": "Keys",
            "pad": "Pads",
        },
    },
}
