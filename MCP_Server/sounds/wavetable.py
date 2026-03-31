"""Wavetable instrument profile: sonic character, strengths, browser paths.

Per D-01: Pure Python dict (no classes).
Per D-02: Data only (no helper functions).
"""

PROFILE = {
    "id": "wavetable",
    "name": "Wavetable",
    "aliases": ["wavetable", "wt", "wave table"],
    "sonic_character": "Wavetable is Ableton's modern wavetable synthesizer, capable of rich, evolving textures through real-time morphing between waveforms. It excels at lush pads, atmospheric textures, and complex timbral movement that analog-style synths cannot achieve. Its two oscillators each support up to 256 wavetable frames with smooth interpolation, combined with a sub oscillator and versatile modulation matrix.",
    "strengths": [
        "lush evolving pads with wavetable morphing",
        "complex timbral textures and movement",
        "rich unison and stereo spread",
        "versatile modulation matrix for animated sounds",
        "built-in effects chain with high-quality reverb",
    ],
    "weaknesses": [
        "less suited for simple classic analog tones",
        "CPU-intensive with heavy unison and effects",
        "wavetable selection can be overwhelming for beginners",
    ],
    "descriptor_affinities": {
        "role": {
            "pad": 0.95,
            "texture": 0.9,
            "lead": 0.6,
            "bass": 0.5,
            "keys": 0.4,
        },
        "character": {
            "evolving": 0.95,
            "warm": 0.7,
            "bright": 0.65,
            "dark": 0.6,
            "lush": 0.9,
            "aggressive": 0.4,
        },
    },
    "browser": {
        "root": "Instruments/Wavetable",
        "categories": {
            "pad": "Pads",
            "lead": "Leads",
            "bass": "Bass",
            "keys": "Keys",
            "drone": "Drones & Atmospheres",
        },
    },
}
