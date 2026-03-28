# Drum and Bass genre mix recipe
# Per D-01: All values in natural units (Hz, dB, ms, %, 0-1 for raw params)
# Per D-02: Sound-shaping params only (no Device On, S/C Listen, etc.)
# Per D-03: All 9 roles present
# Per D-04: Omit devices not applicable (no None markers)
#
# DnB: fast, punchy, aggressive drums, heavy sub-bass, tight low end.
# Fast attack/release on drums, heavy compression, short-medium reverbs.
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
    # KICK: Punchy, fast, saturated
    # -----------------------------------------------------------------------
    "kick": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 28,        # Hz - tight sub control
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - boost fundamental
            "2 Frequency A": 65,        # Hz - punchy fundamental
            "2 Gain A": 4.0,            # dB - strong boost
            "2 Resonance A": 0.6,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - cut mud
            "3 Frequency A": 250,       # Hz
            "3 Gain A": -4.0,           # dB - aggressive cut
            "3 Resonance A": 0.5,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - click emphasis
            "4 Frequency A": 4000,      # Hz
            "4 Gain A": 3.0,            # dB - strong click
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
            "Threshold": -24,           # dB - heavy
            "Ratio": 0.7,              # ~5:1
            "Attack": 3,               # ms - very fast
            "Release": 40,             # ms - fast
            "Output Gain": 2.0,        # dB - makeup
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,               # dB - hard knee
            "Model": 0,                # Peak - transient
            "Env Mode": 0,
        },
        "DrumBuss": {
            "Drive": 0.5,              # moderate-strong drive
            "Drive Type": 1,           # Medium
            "Crunch": 0.3,
            "Damping Freq": 0.6,
            "Transients": 0.5,         # strong transient boost
            "Boom Freq": 0.4,
            "Boom Amt": 0.35,
            "Boom Decay": 0.4,
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
    # BASS: Heavy sub, tight, controlled
    # -----------------------------------------------------------------------
    "bass": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - strong sub boost
            "2 Frequency A": 50,        # Hz
            "2 Gain A": 4.0,            # dB - heavy sub
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - cut mud
            "3 Frequency A": 200,       # Hz
            "3 Gain A": -3.0,           # dB
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
            "Threshold": -22,           # dB - heavy
            "Ratio": 0.75,             # ~6:1
            "Attack": 5,               # ms - fast
            "Release": 60,             # ms
            "Output Gain": 2.0,        # dB
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,
            "Model": 0,                # Peak
            "Env Mode": 0,
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.0,        # mono
            "Mono": 1,
            "Bass Mono": 1,
            "Bass Freq": 0.6,          # ~150Hz bass mono
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # LEAD: Cutting, present, short reverb
    # -----------------------------------------------------------------------
    "lead": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 150,       # Hz - clear low end
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - strong presence
            "2 Frequency A": 3000,      # Hz
            "2 Gain A": 3.0,            # dB - cutting
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - brightness
            "3 Frequency A": 8000,      # Hz
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
            "Threshold": -18,           # dB
            "Ratio": 0.5,              # ~3:1
            "Attack": 10,              # ms - medium
            "Release": 100,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 4.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Reverb": {
            "Predelay": 0.1,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.45,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.4,
            "ER Shape": 0.4,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -3.0,       # dB - dark reverb tail
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -4.0,      # dB - tight low end
            "Decay Time": 0.25,         # ~0.8-1.2s short
            "Diffusion": 0.6,
            "Scale": 0.5,
            "Room Size": 0.4,
            "Stereo Image": 0.6,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.5,
            "Dry/Wet": 15,              # % - subtle
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 2,               # short rhythmic
            "R 16th": 3,               # 1/8 note
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.25,
            "Filter On": 1,
            "Filter Freq": 0.55,
            "Filter Width": 0.5,
            "Dry/Wet": 12,              # % - subtle
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.2,        # moderate width
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # PAD: Atmospheric backdrop, medium reverb
    # -----------------------------------------------------------------------
    "pad": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 120,       # Hz - clear low end for bass
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf - air
            "2 Frequency A": 8000,      # Hz
            "2 Gain A": 1.5,            # dB
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
            "Threshold": -14,           # dB - gentle
            "Ratio": 0.35,             # ~2:1
            "Attack": 30,              # ms
            "Release": 200,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 8.0,
            "Model": 1,                # RMS
            "Env Mode": 1,
        },
        "Reverb": {
            "Predelay": 0.2,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.35,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.4,
            "ER Spin Amount": 0.6,
            "ER Shape": 0.6,
            "HiFilter On": 1,
            "HiFilter Freq": 0.75,
            "HiShelf Gain": -2.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.45,         # ~2s medium
            "Diffusion": 0.7,
            "Scale": 0.7,
            "Room Size": 0.6,
            "Stereo Image": 0.8,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.6,
            "Dry/Wet": 25,              # %
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
    # CHORDS: Stab-like, mid-forward, short reverb
    # -----------------------------------------------------------------------
    "chords": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 180,       # Hz - tight low cut
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - mid-forward
            "2 Frequency A": 1000,      # Hz
            "2 Gain A": 2.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf
            "3 Frequency A": 6000,      # Hz
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
            "Threshold": -16,           # dB - moderate
            "Ratio": 0.45,             # ~2.5:1
            "Attack": 15,              # ms
            "Release": 120,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 6.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Reverb": {
            "Predelay": 0.1,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.4,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.4,
            "ER Shape": 0.4,
            "HiFilter On": 1,
            "HiFilter Freq": 0.65,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.3,          # ~1s short
            "Diffusion": 0.6,
            "Scale": 0.5,
            "Room Size": 0.4,
            "Stereo Image": 0.6,
            "Density": 2,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.5,
            "Dry/Wet": 15,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.0,        # moderate
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # VOCAL: Clean, present, gated
    # -----------------------------------------------------------------------
    "vocal": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 100,       # Hz - low cut
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
            "3 Gain A": 1.5,            # dB
            "3 Resonance A": 0.71,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - nasal cut
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
            "Threshold": -18,           # dB
            "Ratio": 0.5,              # ~3:1
            "Attack": 8,               # ms
            "Release": 80,             # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 4.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Gate": {
            "Threshold": -35,           # dB
            "Attack": 0.5,             # ms - fast
            "Hold": 0.3,
            "Release": 40,             # ms
            "Return": 3.0,             # dB
            "Floor": -40.0,            # dB
        },
        "Reverb": {
            "Predelay": 0.08,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.45,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.4,
            "ER Shape": 0.4,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -4.0,
            "Decay Time": 0.2,          # ~0.8s short
            "Diffusion": 0.7,
            "Scale": 0.5,
            "Room Size": 0.35,
            "Stereo Image": 0.5,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.5,
            "Dry/Wet": 12,              # % - subtle
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 2,               # short rhythmic
            "R 16th": 3,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.15,           # subtle
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.5,
            "Dry/Wet": 8,               # % - very subtle
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.6,        # near center
            "Mono": 0,
            "Bass Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # ATMOSPHERIC: Dark, textural, wide
    # -----------------------------------------------------------------------
    "atmospheric": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 80,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 6,       # LP 12dB - dark, rolled-off highs
            "2 Frequency A": 6000,      # Hz
            "2 Gain A": 0.0,
            "2 Resonance A": 0.5,
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
            "Predelay": 0.2,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.35,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.6,
            "ER Shape": 0.6,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -4.0,       # dB - very dark
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.6,          # ~3s long
            "Diffusion": 0.8,
            "Scale": 0.8,
            "Room Size": 0.7,
            "Stereo Image": 0.85,
            "Density": 2,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.7,
            "Dry/Wet": 35,              # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 4,               # 1/4 note
            "R 16th": 5,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.4,            # high feedback
            "Filter On": 1,
            "Filter Freq": 0.45,        # darker filter
            "Filter Width": 0.5,
            "Dry/Wet": 20,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.7,        # wide
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # RETURN: Send effects (100% wet) - medium-short, rhythmic
    # -----------------------------------------------------------------------
    "return": {
        "Reverb": {
            "Predelay": 0.1,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.4,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.4,
            "ER Shape": 0.4,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -4.0,
            "Decay Time": 0.35,         # ~1.5s medium-short
            "Diffusion": 0.7,
            "Scale": 0.6,
            "Room Size": 0.45,
            "Stereo Image": 0.7,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.6,
            "Dry/Wet": 100,             # % - send effect
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 2,               # short rhythmic
            "R 16th": 3,               # 1/8 note
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.35,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.5,
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
    # MASTER: Tight low end control (Phase 34 adds full master chain)
    # -----------------------------------------------------------------------
    "master": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP - subsonic
            "1 Frequency A": 28,        # Hz - tight
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - low tightness
            "2 Frequency A": 200,       # Hz
            "2 Gain A": -1.0,           # dB - subtle mud cut
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
            "Bass Freq": 0.5,
            "Balance": 0.0,
        },
    },
}

# ---------------------------------------------------------------------------
# Master bus recipe: GlueCompressor -> MultibandDynamics -> Limiter
# Punchy, aggressive, loud -- DnB master chain
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -10.0,      # dB
        "Ratio": 0.6,            # approx 4:1
        "Attack": 0.15,          # very fast
        "Release": 0.25,
        "Makeup": 4.0,           # dB
        "Dry/Wet": 100.0,        # %
        "Peak Clip In": 0,
        "Range": 0.5,
    },
    "MultibandDynamics": {
        "Master Output": 0.0,
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": -16.0,
        "Above Ratio (Low)": 0.7,
        "Above Threshold (Mid)": -12.0,
        "Above Ratio (Mid)": 0.6,
        "Above Threshold (High)": -10.0,
        "Above Ratio (High)": 0.55,
        "Input Gain (Low)": 0.0,
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": 6.0,       # dB
        "Ceiling": 0.9,
        "Link": 1.0,
        "Lookahead": 1,
    },
}
