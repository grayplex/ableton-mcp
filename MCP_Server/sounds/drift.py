"""Drift instrument profile: sonic character, strengths, browser paths."""

PROFILE = {
    "id": "drift",
    "name": "Drift",
    "aliases": ["drift"],
    "sonic_character": "Drift is Ableton's vintage-inspired analog-modeled synthesizer, introduced in Live 11.3. Its defining feature is oscillator drift -- subtle pitch instability that gives it the organic, breathing character of classic hardware. Built around a single oscillator with sub oscillator and noise source, Drift uses a ladder-style filter and gentle chorus/unison to produce the characteristically warm, slightly imperfect sound of vintage synthesizers. It excels at organic basses, drifting pads, and warm leads with life and movement.",
    "strengths": [
        "authentic vintage analog warmth with oscillator drift",
        "organic breathing character from pitch instability",
        "warm ladder filter with classic resonance behavior",
        "natural-sounding basses and pads with movement",
        "simple architecture that rewards intuitive patching",
    ],
    "weaknesses": [
        "single oscillator limits harmonic richness",
        "less suited for bright metallic or FM-style tones",
        "not designed for heavily modulated evolving textures",
    ],
    "descriptor_affinities": {
        "role": {
            "bass": 0.8,
            "lead": 0.75,
            "keys": 0.7,
            "pad": 0.65,
            "texture": 0.5,
        },
        "character": {
            "warm": 0.85,
            "dark": 0.7,
            "evolving": 0.6,
            "punchy": 0.55,
            "bright": 0.45,
            "aggressive": 0.4,
        },
    },
    "browser": {
        "root": "Instruments/Drift",
        "categories": {
            "bass": "Bass",
            "lead": "Leads",
            "keys": "Keys",
            "pad": "Pads",
        },
    },
}
