"""Drum Rack instrument profile: sonic character, strengths, browser paths.

Per D-01: Pure Python dict (no classes).
Per D-02: Data only (no helper functions).
"""

PROFILE = {
    "id": "drum_rack",
    "name": "Drum Rack",
    "aliases": ["drum rack", "drum_rack", "dr", "drumsrack"],
    "sonic_character": "Drum Rack is Ableton's dedicated percussion instrument -- a 128-pad grid where each pad hosts its own instrument chain, effects, and routing. It is the foundation for all beat-making in Ableton, mapping kick, snare, hi-hat, and percussion sounds to individual MIDI notes with per-pad volume, pitch, pan, and choke groups. Each pad can hold a Simpler, synthesizer, or audio effect chain, making Drum Rack capable of everything from sample-accurate acoustic drums to fully synthesized electronic kits.",
    "strengths": [
        "industry-standard drum sequencing and beat building",
        "per-pad instrument chains with independent processing",
        "choke groups for realistic hi-hat behavior",
        "scalable from simple sample playback to complex synthesis per pad",
        "tight integration with Ableton's step sequencer",
    ],
    "weaknesses": [
        "not suited for melodic or pitched harmonic roles",
        "complex routing can be time-consuming to configure",
        "requires samples or nested instruments for each pad",
    ],
    "descriptor_affinities": {
        "role": {
            "kick": 0.95,
            "snare": 0.95,
            "hihat": 0.9,
            "percussion": 0.9,
            "pad": 0.2,
            "lead": 0.1,
        },
        "character": {
            "punchy": 0.95,
            "tight": 0.8,
            "aggressive": 0.75,
            "bright": 0.5,
            "warm": 0.4,
            "evolving": 0.25,
        },
    },
    "browser": {
        "root": "Instruments/Drum Rack",
        "categories": {
            "kick": "Drums & Percussion",
            "snare": "Drums & Percussion",
            "hihat": "Drums & Percussion",
            "percussion": "Drums & Percussion",
        },
    },
}
