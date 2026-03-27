"""Disco/Funk genre blueprint: instrumentation, harmony, rhythm, arrangement, mixing, tips.

Disco/Funk hybrid genre with four subgenres: nu-disco, funk, boogie, and electro funk.

Per D-06: Canonical genre ID is disco_funk. Wide BPM range 100-130 in base;
subgenres tighten: funk 95-110, nu-disco 118-128, boogie 108-120, electro funk 100-118.
"""

GENRE = {
    "name": "Disco/Funk",
    "id": "disco_funk",
    "bpm_range": [100, 130],
    "aliases": ["disco funk", "disco/funk", "disco", "funk music"],
    "instrumentation": {
        "roles": [
            "bass_guitar", "rhythm_guitar", "kick", "snare", "hi-hats",
            "brass", "strings", "keys", "clav", "percussion", "vocal", "fx",
        ]
    },
    "harmony": {
        "scales": ["major", "dorian", "mixolydian", "minor_pentatonic"],
        "chord_types": ["dom7", "min7", "maj7", "9", "min9", "13"],
        "common_progressions": [
            ["I7", "IV7"],
            ["ii7", "V7", "I7"],
            ["i7", "iv7", "bVII7"],
            ["vi7", "ii7", "V7", "I7"],
        ],
    },
    "rhythm": {
        "time_signature": "4/4",
        "bpm_range": [100, 130],
        "swing": "light",
        "note_values": ["1/4", "1/8", "1/16"],
        "drum_pattern": "four-on-the-floor kick, syncopated bass, open hi-hat on upbeats, snare on 2 and 4",
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
        "frequency_focus": "punchy bass 60-150Hz, warm guitar and keys 200Hz-2kHz, brass presence 2-6kHz, crisp hi-hats 8-12kHz",
        "stereo_field": "mono bass, wide strings and brass, centered vocals and kick, panned guitars left/right",
        "common_effects": ["compression", "reverb", "delay", "chorus", "phaser", "wah pedal"],
        "compression_style": "punchy drum compression, warm bass compression, light bus glue, live dynamic range preserved",
    },
    "production_tips": {
        "techniques": [
            "use syncopated bass lines that lock with the kick drum",
            "layer brass stabs for impact in chorus sections",
            "add rhythmic guitar scratching on 16th notes for groove",
            "use wah and phaser effects on guitar for classic funk tone",
            "keep live instrument feel — avoid overly quantized MIDI",
        ],
        "pitfalls": [
            "bass line too simple losing the funk groove",
            "over-quantizing drums killing the live feel",
            "brass and strings competing for same frequency space",
            "too many elements cluttering the mix — funk breathes",
        ],
    },
}

SUBGENRES = {
    "nu_disco": {
        "name": "Nu-Disco",
        "bpm_range": [118, 128],
        "aliases": ["nu disco", "nu-disco", "new disco", "nudisco"],
        "instrumentation": {
            "roles": [
                "bass_synth", "rhythm_guitar", "kick", "snare", "hi-hats",
                "synth_pad", "strings", "keys", "vocal_chop", "percussion", "fx",
            ]
        },
        "harmony": {
            "scales": ["major", "dorian", "mixolydian"],
            "chord_types": ["maj7", "min7", "dom7", "9", "add9"],
            "common_progressions": [
                ["I", "V", "vi", "IV"],
                ["ii", "V", "I"],
                ["vi", "ii", "V", "I"],
            ],
        },
        "mixing": {
            "frequency_focus": "electronic sub-bass 40-80Hz, filtered synths 500Hz-4kHz, bright hi-hats 10-14kHz",
            "stereo_field": "wide synth pads, mono bass, centered vocals, stereo guitar layers",
            "common_effects": ["sidechain compression", "reverb", "delay", "filter sweeps", "chorus"],
            "compression_style": "sidechain bass and pads to kick, modern electronic production with disco warmth",
        },
    },
    "funk": {
        "name": "Funk",
        "bpm_range": [95, 110],
        "aliases": ["funk", "raw funk", "classic funk"],
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [95, 110],
            "swing": "heavy",
            "note_values": ["1/4", "1/8", "1/16"],
            "drum_pattern": "syncopated kick, ghost notes on snare, open and closed hi-hat interplay, tight groove",
        },
        "harmony": {
            "scales": ["dorian", "mixolydian", "minor_pentatonic", "blues"],
            "chord_types": ["dom7", "min7", "9", "13", "min9"],
            "common_progressions": [
                ["I7"],
                ["I7", "IV7"],
                ["i7", "iv7"],
            ],
        },
        "production_tips": {
            "techniques": [
                "emphasize the 'one' — heavy downbeat with syncopation after",
                "use ghost notes on snare for groove complexity",
                "slap bass technique for punchy, percussive bass lines",
                "wah pedal on guitar for classic funk tone",
            ],
            "pitfalls": [
                "groove too straight losing the syncopated feel",
                "bass and guitar fighting for rhythmic space",
                "too much reverb killing the tight, dry funk sound",
            ],
        },
    },
    "boogie": {
        "name": "Boogie",
        "bpm_range": [108, 120],
        "aliases": ["boogie", "boogie funk", "post-disco"],
        "instrumentation": {
            "roles": [
                "bass_synth", "bass_guitar", "rhythm_guitar", "kick", "snare",
                "hi-hats", "synth_pad", "keys", "clav", "vocal", "percussion",
            ]
        },
        "harmony": {
            "scales": ["major", "dorian", "mixolydian"],
            "chord_types": ["maj7", "min7", "dom7", "9", "13", "add9"],
            "common_progressions": [
                ["ii7", "V7", "I7"],
                ["I7", "vi7", "ii7", "V7"],
                ["I", "IV", "V"],
            ],
        },
    },
    "electro_funk": {
        "name": "Electro Funk",
        "bpm_range": [100, 118],
        "aliases": ["electro funk", "electrofunk", "synth funk"],
        "instrumentation": {
            "roles": [
                "bass_synth", "vocoder", "drum_machine", "kick", "snare",
                "hi-hats", "synth_lead", "keys", "clap", "fx", "percussion",
            ]
        },
        "harmony": {
            "scales": ["dorian", "mixolydian", "minor_pentatonic"],
            "chord_types": ["min7", "dom7", "9", "min9", "sus4"],
            "common_progressions": [
                ["i7", "iv7"],
                ["i7", "bVII7"],
                ["ii7", "V7", "I7"],
            ],
        },
        "mixing": {
            "frequency_focus": "synth bass 40-100Hz, vocoder presence 1-4kHz, drum machine punch 200-500Hz",
            "stereo_field": "wide synth pads, mono bass, centered vocoder and drums",
            "common_effects": ["vocoder", "chorus", "phaser", "compression", "reverb", "talkbox"],
            "compression_style": "tight drum machine compression, warm synth bass, vocoder forward in mix",
        },
        "production_tips": {
            "techniques": [
                "use vocoder for robotic vocal textures (Zapp style)",
                "program drum machine patterns with live feel",
                "layer analog synths for warm, rich bass",
                "use talkbox for expressive synth melodies",
            ],
            "pitfalls": [
                "vocoder too dominant masking other elements",
                "drum machine too rigid without humanization",
                "synth bass too aggressive losing the groove",
            ],
        },
    },
}
