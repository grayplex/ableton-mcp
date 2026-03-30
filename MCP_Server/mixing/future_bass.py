# Future Bass genre mix recipe
# Per D-01: All values in natural units (Hz, dB, ms, %, 0-1 for raw params)
# Per D-02: Sound-shaping params only (no Device On, S/C Listen, etc.)
# Per D-03: All 9 roles present
# Per D-04: Omit devices not applicable (no None markers)
#
# Future Bass: Heavy sidechain feel, lush chords (the star), wide stereo,
# aggressive chord compression, reverb-heavy pads, modern clean bass.
#
# Structure: RECIPE[role][device_class][param_name] = value
# Device class names match CATALOG keys exactly.
# Param names match CATALOG entries exactly.
#
# Eq8 Filter Types: 0=48dB/oct, 1=12dB/oct, 2=Low Shelf, 3=Bell, 4=Notch,
#                   5=High Shelf, 6=LP (12dB), 7=HP (12dB)
# Compressor2 Model: 0=Peak, 1=RMS, 2=Expand
# DrumBuss Drive Type: 0=Soft, 1=Medium, 2=Hard

RECIPE = {
    # -----------------------------------------------------------------------
    # KICK: Punchy but not as aggressive as dubstep
    # -----------------------------------------------------------------------
    "kick": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 30,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - punch
            "2 Frequency A": 60,        # Hz
            "2 Gain A": 3.0,            # dB
            "2 Resonance A": 0.55,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - cut mud
            "3 Frequency A": 280,       # Hz
            "3 Gain A": -3.0,           # dB
            "3 Resonance A": 0.5,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - click
            "4 Frequency A": 4000,      # Hz
            "4 Gain A": 2.0,            # dB
            "4 Resonance A": 0.5,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -18,           # dB
            "Ratio": 0.55,             # ~3.5:1
            "Attack": 10,              # ms
            "Release": 70,             # ms
            "Output Gain": 1.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 4.0,
            "Model": 0,                # Peak
            "Env Mode": 0,
        },
        "DrumBuss": {
            "Drive": 0.35,             # moderate
            "Drive Type": 1,           # Medium
            "Crunch": 0.2,
            "Damping Freq": 0.65,
            "Transients": 0.3,
            "Boom Freq": 0.4,
            "Boom Amt": 0.3,
            "Boom Decay": 0.45,
            "Trim": 0.5,
            "Output Gain": 0.0,
            "Dry/Wet": 100,
            "Compressor On": 1,
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
    # BASS: Modern, clean, controlled
    # -----------------------------------------------------------------------
    "bass": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - sub body
            "2 Frequency A": 70,        # Hz
            "2 Gain A": 2.5,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - mid clarity
            "3 Frequency A": 400,       # Hz
            "3 Gain A": -1.5,           # dB
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
            "Threshold": -18,           # dB
            "Ratio": 0.5,             # ~3:1
            "Attack": 12,              # ms
            "Release": 90,             # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 4.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.0,
            "Mono": 1,
            "Bass Mono": 1,
            "Bass Freq": 0.5,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # LEAD: Bright, present, spacious
    # -----------------------------------------------------------------------
    "lead": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 200,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - presence
            "2 Frequency A": 2500,      # Hz
            "2 Gain A": 2.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 8000,      # Hz
            "3 Gain A": 2.5,            # dB
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
            "Threshold": -16,           # dB
            "Ratio": 0.45,            # ~2.5:1
            "Attack": 18,              # ms
            "Release": 140,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 6.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Reverb": {
            "Predelay": 0.15,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.4,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.45,
            "ER Spin Amount": 0.55,
            "ER Shape": 0.55,
            "HiFilter On": 1,
            "HiFilter Freq": 0.8,
            "HiShelf Gain": -1.5,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.5,
            "Decay Time": 0.5,          # ~2.2s
            "Diffusion": 0.8,
            "Scale": 0.75,
            "Room Size": 0.6,
            "Stereo Image": 0.8,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.65,
            "Dry/Wet": 22,              # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 3,               # 1/8 note
            "R 16th": 3,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.25,
            "Filter On": 1,
            "Filter Freq": 0.6,
            "Filter Width": 0.5,
            "Dry/Wet": 15,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.2,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # PAD: Lush, wide, reverb-heavy
    # -----------------------------------------------------------------------
    "pad": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 130,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - warmth
            "2 Frequency A": 500,       # Hz
            "2 Gain A": 1.0,            # dB
            "2 Resonance A": 0.4,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - shimmer
            "3 Frequency A": 10000,     # Hz
            "3 Gain A": 2.0,            # dB
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
            "Threshold": -12,           # dB
            "Ratio": 0.35,            # ~2:1
            "Attack": 30,              # ms
            "Release": 220,            # ms
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
            "In HighCut On": 0,
            "In Filter Freq": 0.3,
            "In Filter Width": 0.8,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.7,
            "ER Shape": 0.7,
            "HiFilter On": 1,
            "HiFilter Freq": 0.85,
            "HiShelf Gain": -1.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.25,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.7,          # ~3.5s
            "Diffusion": 0.9,
            "Scale": 0.85,
            "Room Size": 0.75,
            "Stereo Image": 0.9,
            "Density": 3,
            "Reflect Level": 0.35,
            "Diffuse Level": 0.75,
            "Dry/Wet": 30,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.6,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # CHORDS: The star -- heavy compression, wide stereo, reverb
    # -----------------------------------------------------------------------
    "chords": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 150,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - mid body
            "2 Frequency A": 700,       # Hz
            "2 Gain A": 2.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - brightness
            "3 Frequency A": 6000,      # Hz
            "3 Gain A": 2.5,            # dB - bright chords
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
            "Threshold": -20,           # dB - heavy
            "Ratio": 0.65,             # ~4.5:1 - aggressive
            "Attack": 10,              # ms - fast for sidechain feel
            "Release": 80,             # ms - fast release
            "Output Gain": 2.0,        # dB - makeup
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Reverb": {
            "Predelay": 0.15,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.4,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.55,
            "ER Shape": 0.55,
            "HiFilter On": 1,
            "HiFilter Freq": 0.8,
            "HiShelf Gain": -1.5,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.5,
            "Decay Time": 0.5,          # ~2.2s
            "Diffusion": 0.8,
            "Scale": 0.75,
            "Room Size": 0.6,
            "Stereo Image": 0.85,
            "Density": 2,
            "Reflect Level": 0.45,
            "Diffuse Level": 0.65,
            "Dry/Wet": 25,              # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 4,               # 1/4 note
            "R 16th": 4,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.2,
            "Filter On": 1,
            "Filter Freq": 0.55,
            "Filter Width": 0.5,
            "Dry/Wet": 12,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.6,        # very wide - chords are the star
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # VOCAL: Clear, airy, wide
    # -----------------------------------------------------------------------
    "vocal": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 80,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - presence
            "2 Frequency A": 3000,      # Hz
            "2 Gain A": 2.5,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 8000,      # Hz
            "3 Gain A": 2.5,            # dB - airy
            "3 Resonance A": 0.71,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - cut mud
            "4 Frequency A": 400,       # Hz
            "4 Gain A": -2.0,           # dB
            "4 Resonance A": 0.5,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -16,           # dB
            "Ratio": 0.45,            # ~2.5:1
            "Attack": 12,              # ms
            "Release": 110,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 5.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Gate": {
            "Threshold": -35,           # dB
            "Attack": 0.5,             # ms
            "Hold": 0.3,
            "Release": 50,             # ms
            "Return": 3.0,             # dB
            "Floor": -40.0,            # dB
        },
        "Reverb": {
            "Predelay": 0.12,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.45,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.45,
            "ER Shape": 0.45,
            "HiFilter On": 1,
            "HiFilter Freq": 0.7,
            "HiShelf Gain": -2.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.35,         # ~1.5s
            "Diffusion": 0.8,
            "Scale": 0.65,
            "Room Size": 0.5,
            "Stereo Image": 0.7,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.55,
            "Dry/Wet": 18,              # %
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 3,               # 1/8 note
            "R 16th": 3,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.2,
            "Filter On": 1,
            "Filter Freq": 0.55,
            "Filter Width": 0.5,
            "Dry/Wet": 10,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.9,
            "Mono": 0,
            "Bass Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # ATMOSPHERIC: Lush, wide, textural
    # -----------------------------------------------------------------------
    "atmospheric": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 100,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf - shimmer
            "2 Frequency A": 8000,      # Hz
            "2 Gain A": 2.5,            # dB
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
            "Predelay": 0.25,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.3,
            "In Filter Width": 0.8,
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
            "Decay Time": 0.75,         # ~4s
            "Diffusion": 0.9,
            "Scale": 0.85,
            "Room Size": 0.8,
            "Stereo Image": 0.95,
            "Density": 3,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.8,
            "Dry/Wet": 40,              # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 5,
            "R 16th": 6,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.4,
            "Filter On": 1,
            "Filter Freq": 0.55,
            "Filter Width": 0.6,
            "Dry/Wet": 22,              # %
        },
        "AutoFilter2": {
            "Frequency": 0.6,
            "Resonance": 0.2,
            "Type": 0,           # Low-pass
            "LFO Amount": 0.15,
            "LFO Rate": 0.2,
            "LFO Phase": 0.5,
            "LFO Offset": 0.5,
            "Env Amount": 0.1,
            "Env Attack": 0.3,
            "Env Release": 0.5,
            "Dry/Wet": 100,
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
    # RETURN: Send effects (100% wet)
    # -----------------------------------------------------------------------
    "return": {
        "Reverb": {
            "Predelay": 0.15,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.4,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.45,
            "ER Spin Amount": 0.55,
            "ER Shape": 0.55,
            "HiFilter On": 1,
            "HiFilter Freq": 0.75,
            "HiShelf Gain": -1.5,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.5,
            "Decay Time": 0.5,          # ~2.2s
            "Diffusion": 0.8,
            "Scale": 0.75,
            "Room Size": 0.6,
            "Stereo Image": 0.8,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.65,
            "Dry/Wet": 100,             # % - send effect
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 3,               # 1/8 note
            "R 16th": 4,               # 1/4 note
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.3,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.5,
            "Dry/Wet": 100,             # % - send effect
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.0,
            "Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # MASTER: Loud but not crushed, wide stereo image
    # -----------------------------------------------------------------------
    "master": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP - subsonic
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - gentle low
            "2 Frequency A": 80,        # Hz
            "2 Gain A": 0.5,            # dB
            "2 Resonance A": 0.3,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - brightness
            "3 Frequency A": 10000,     # Hz
            "3 Gain A": 0.5,            # dB
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
        "StereoGain": {
            "Gain": 0.0,
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
# Loud but not crushed, wide stereo image -- future bass master chain
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -5.0,       # dB
        "Ratio": 0.4,            # ~2:1
        "Attack": 0.3,           # medium-fast
        "Release": 0.4,
        "Makeup": 2.5,           # dB
        "Dry/Wet": 100.0,        # %
        "Peak Clip In": 0,
        "Range": 0.5,
    },
    "MultibandDynamics": {
        "Master Output": 0.0,
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": -12.0,
        "Above Ratio (Low)": 0.6,
        "Above Threshold (Mid)": -10.0,
        "Above Ratio (Mid)": 0.5,
        "Above Threshold (High)": -8.0,
        "Above Ratio (High)": 0.45,
        "Input Gain (Low)": 0.0,
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": 4.5,       # dB - loud but not crushed
        "Ceiling": 0.7,          # moderate limiting
        "Link": 1.0,
        "Lookahead": 1,          # 1ms
    },
}
