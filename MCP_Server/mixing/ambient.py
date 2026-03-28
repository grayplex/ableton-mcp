# Ambient genre mix recipe
# Per D-01: All values in natural units (Hz, dB, ms, %, 0-1 for raw params)
# Per D-02: Sound-shaping params only (no Device On, S/C Listen, etc.)
# Per D-03: All 9 roles present
# Per D-04: Omit devices not applicable (no None markers)
#
# Ambient: spacious, ethereal, long reverb tails, minimal compression,
# wide stereo field. Gentlest processing of all genres.
#
# Structure: RECIPE[role][device_class][param_name] = value
# Device class names match CATALOG keys exactly.
# Param names match CATALOG entries exactly.
#
# Eq8 Filter Types: 0=48dB/oct, 1=12dB/oct, 2=Low Shelf, 3=Bell, 4=Notch,
#                   5=High Shelf, 6=LP (12dB), 7=HP (12dB)
# Compressor2 Model: 0=Peak, 1=RMS, 2=Expand

RECIPE = {
    # -----------------------------------------------------------------------
    # KICK: Gentle, soft attack, minimal processing
    # -----------------------------------------------------------------------
    "kick": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 30,        # Hz - remove sub rumble
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - gentle low boost
            "2 Frequency A": 50,        # Hz - soft fundamental
            "2 Gain A": 2.0,            # dB - gentle
            "2 Resonance A": 0.4,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP 12dB - roll off highs
            "3 Frequency A": 6000,      # Hz - soft top end
            "3 Gain A": 0.0,
            "3 Resonance A": 0.5,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -12,           # dB - very gentle
            "Ratio": 0.25,             # ~1.5:1 - barely touching
            "Attack": 30,              # ms - slow attack
            "Release": 200,            # ms - slow release
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 10.0,              # dB - soft knee
            "Model": 1,                # RMS - smooth
            "Env Mode": 1,
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.0,        # mono
            "Mono": 1,
            "Bass Mono": 1,
            "Bass Freq": 0.5,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # BASS: Warm, undulating, gentle
    # -----------------------------------------------------------------------
    "bass": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 25,        # Hz - remove sub rumble
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - gentle low warmth
            "2 Frequency A": 80,        # Hz
            "2 Gain A": 2.0,            # dB - gentle boost
            "2 Resonance A": 0.4,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP 12dB - roll off highs
            "3 Frequency A": 3000,      # Hz - warm, dark
            "3 Gain A": 0.0,
            "3 Resonance A": 0.5,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -14,           # dB - gentle
            "Ratio": 0.25,             # ~1.5:1
            "Attack": 40,              # ms - slow
            "Release": 250,            # ms - slow
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 10.0,
            "Model": 1,                # RMS
            "Env Mode": 1,
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.4,        # narrow
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.5,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # LEAD: Spacious, gentle presence, long reverb
    # -----------------------------------------------------------------------
    "lead": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 150,       # Hz - clear low end
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - gentle presence
            "2 Frequency A": 2500,      # Hz
            "2 Gain A": 1.5,            # dB - subtle
            "2 Resonance A": 0.4,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 8000,      # Hz
            "3 Gain A": 1.0,            # dB
            "3 Resonance A": 0.71,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -12,           # dB - very gentle
            "Ratio": 0.25,             # ~1.5:1
            "Attack": 30,              # ms - slow
            "Release": 200,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 10.0,
            "Model": 1,                # RMS
            "Env Mode": 1,
        },
        "Reverb": {
            "Predelay": 0.25,
            "In LowCut On": 1,
            "In HighCut On": 0,         # no high cut - open
            "In Filter Freq": 0.3,
            "In Filter Width": 0.7,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.7,
            "ER Shape": 0.7,
            "HiFilter On": 1,
            "HiFilter Freq": 0.85,
            "HiShelf Gain": -1.0,       # dB - gentle darken
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.65,         # ~3-4s long decay
            "Diffusion": 0.85,
            "Scale": 0.85,
            "Room Size": 0.8,
            "Stereo Image": 0.9,
            "Density": 3,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.8,
            "Dry/Wet": 35,              # % - generous wet
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 5,               # long delay
            "R 16th": 6,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.4,            # high feedback
            "Filter On": 1,
            "Filter Freq": 0.55,
            "Filter Width": 0.6,
            "Dry/Wet": 20,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.3,        # moderate width
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # PAD: Core element - very wide, very long reverb, lush
    # -----------------------------------------------------------------------
    "pad": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 60,        # Hz - gentle low cut
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf - air
            "2 Frequency A": 8000,      # Hz
            "2 Gain A": 1.5,            # dB - gentle air boost
            "2 Resonance A": 0.71,
            "3 Filter On A": 0,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -10,           # dB - very gentle
            "Ratio": 0.2,             # ~1.3:1
            "Attack": 50,              # ms - very slow
            "Release": 300,            # ms - slow
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 10.0,
            "Model": 1,                # RMS - smooth
            "Env Mode": 1,
        },
        "Reverb": {
            "Predelay": 0.3,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.25,
            "In Filter Width": 0.8,
            "ER Spin On": 1,
            "ER Spin Rate": 0.25,
            "ER Spin Amount": 0.8,
            "ER Shape": 0.8,
            "HiFilter On": 1,
            "HiFilter Freq": 0.9,
            "HiShelf Gain": -0.5,       # dB - barely darken
            "LowShelf On": 1,
            "LowShelf Freq": 0.25,
            "LowShelf Gain": -1.5,
            "Decay Time": 0.8,          # ~4-5s very long
            "Diffusion": 0.9,
            "Scale": 0.9,
            "Room Size": 0.85,
            "Stereo Image": 0.95,
            "Density": 3,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.85,
            "Dry/Wet": 40,              # % - high wet mix
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.8,        # very wide
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # CHORDS: Similar to pad but more defined
    # -----------------------------------------------------------------------
    "chords": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 100,       # Hz - gentle low cut
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - gentle clarity
            "2 Frequency A": 2000,      # Hz
            "2 Gain A": 1.0,            # dB
            "2 Resonance A": 0.4,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 8000,      # Hz
            "3 Gain A": 1.0,            # dB
            "3 Resonance A": 0.71,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -12,           # dB - gentle
            "Ratio": 0.25,             # ~1.5:1
            "Attack": 40,              # ms - slow
            "Release": 250,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 10.0,
            "Model": 1,                # RMS
            "Env Mode": 1,
        },
        "Reverb": {
            "Predelay": 0.2,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.3,
            "In Filter Width": 0.7,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.7,
            "ER Shape": 0.7,
            "HiFilter On": 1,
            "HiFilter Freq": 0.85,
            "HiShelf Gain": -1.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.6,          # ~3s long
            "Diffusion": 0.85,
            "Scale": 0.85,
            "Room Size": 0.75,
            "Stereo Image": 0.9,
            "Density": 3,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.75,
            "Dry/Wet": 30,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.5,        # wide
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # VOCAL: Ethereal, highly reverbed, diffused
    # -----------------------------------------------------------------------
    "vocal": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 80,        # Hz - low cut
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - gentle presence
            "2 Frequency A": 3000,      # Hz
            "2 Gain A": 1.5,            # dB - subtle
            "2 Resonance A": 0.4,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 8000,      # Hz
            "3 Gain A": 1.0,            # dB
            "3 Resonance A": 0.71,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -14,           # dB - gentle
            "Ratio": 0.3,             # ~2:1
            "Attack": 25,              # ms
            "Release": 200,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 8.0,
            "Model": 1,                # RMS
            "Env Mode": 1,
        },
        "Reverb": {
            "Predelay": 0.3,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.3,
            "In Filter Width": 0.7,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.7,
            "ER Shape": 0.7,
            "HiFilter On": 1,
            "HiFilter Freq": 0.85,
            "HiShelf Gain": -1.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.75,         # ~4s very long
            "Diffusion": 0.9,
            "Scale": 0.9,
            "Room Size": 0.8,
            "Stereo Image": 0.9,
            "Density": 3,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.8,
            "Dry/Wet": 35,              # % - atmospheric
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 5,               # long delay
            "R 16th": 7,               # very long R for space
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.4,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.6,
            "Dry/Wet": 20,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.2,        # moderate width
            "Mono": 0,
            "Bass Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # ATMOSPHERIC: Primary ambient element - maximum space
    # -----------------------------------------------------------------------
    "atmospheric": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 60,        # Hz - very gentle
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf - air
            "2 Frequency A": 6000,      # Hz
            "2 Gain A": 1.5,            # dB - gentle shimmer
            "2 Resonance A": 0.71,
            "3 Filter On A": 0,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Reverb": {
            "Predelay": 0.35,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.2,
            "In Filter Width": 0.9,
            "ER Spin On": 1,
            "ER Spin Rate": 0.2,
            "ER Spin Amount": 0.8,
            "ER Shape": 0.8,
            "HiFilter On": 1,
            "HiFilter Freq": 0.9,
            "HiShelf Gain": -0.5,       # dB - barely darken
            "LowShelf On": 1,
            "LowShelf Freq": 0.25,
            "LowShelf Gain": -1.0,
            "Decay Time": 0.9,          # ~5s+ maximum length
            "Diffusion": 0.95,
            "Scale": 0.95,
            "Room Size": 0.9,
            "Stereo Image": 0.98,
            "Density": 3,
            "Reflect Level": 0.2,
            "Diffuse Level": 0.9,
            "Dry/Wet": 50,              # % - high wet mix
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 6,               # long ambient delay
            "R 16th": 7,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.5,            # high feedback for wash
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.7,
            "Dry/Wet": 30,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 2.0,        # maximum width
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # RETURN: Send effects (100% wet) - very long, lush
    # -----------------------------------------------------------------------
    "return": {
        "Reverb": {
            "Predelay": 0.3,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.25,
            "In Filter Width": 0.8,
            "ER Spin On": 1,
            "ER Spin Rate": 0.25,
            "ER Spin Amount": 0.8,
            "ER Shape": 0.8,
            "HiFilter On": 1,
            "HiFilter Freq": 0.9,
            "HiShelf Gain": -0.5,
            "LowShelf On": 1,
            "LowShelf Freq": 0.25,
            "LowShelf Gain": -1.5,
            "Decay Time": 0.85,         # ~5s very long
            "Diffusion": 0.95,
            "Scale": 0.95,
            "Room Size": 0.9,
            "Stereo Image": 0.95,
            "Density": 3,
            "Reflect Level": 0.2,
            "Diffuse Level": 0.9,
            "Dry/Wet": 100,             # % - send effect
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 5,               # long delay
            "R 16th": 7,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.45,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.6,
            "Dry/Wet": 100,             # % - send effect
        },
        "StereoGain": {
            "Gain": 0.0,               # unity
            "Stereo Width": 1.0,
            "Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # MASTER: Very minimal (Phase 34 adds full master chain)
    # -----------------------------------------------------------------------
    "master": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP - subsonic
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - very gentle
            "2 Frequency A": 5000,      # Hz
            "2 Gain A": 0.5,            # dB - very subtle
            "2 Resonance A": 0.3,
            "3 Filter On A": 0,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "StereoGain": {
            "Gain": 0.0,               # unity
            "Stereo Width": 1.0,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },
}

# ---------------------------------------------------------------------------
# Master bus recipe: GlueCompressor -> MultibandDynamics -> Limiter
# Gentle, transparent, wide -- ambient master chain
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -4.0,       # dB (gentle)
        "Ratio": 0.2,            # ~1.5:1
        "Attack": 0.5,           # slow
        "Release": 0.6,
        "Makeup": 1.0,           # dB
        "Dry/Wet": 100.0,        # %
        "Peak Clip In": 0,
        "Range": 0.5,
    },
    "MultibandDynamics": {
        "Master Output": 0.0,
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": -8.0,
        "Above Ratio (Low)": 0.4,
        "Above Threshold (Mid)": -6.0,
        "Above Ratio (Mid)": 0.3,
        "Above Threshold (High)": -6.0,
        "Above Ratio (High)": 0.3,
        "Input Gain (Low)": 0.0,
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": 2.0,       # dB (gentle)
        "Ceiling": 0.5,
        "Link": 1.0,
        "Lookahead": 1,
    },
}
