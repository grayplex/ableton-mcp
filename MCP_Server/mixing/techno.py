# Techno genre mix recipe
# Per D-01: All values in natural units (Hz, dB, ms, %, 0-1 for raw params)
# Per D-02: Sound-shaping params only (no Device On, S/C Listen, etc.)
# Per D-03: All 9 roles present
# Per D-04: Omit devices not applicable (no None markers)
#
# Techno: harder, tighter, more aggressive than house.
# More compression, darker reverb, rhythmic delay, DrumBuss saturation.
#
# Eq8 Filter Types: 0=48dB/oct, 1=12dB/oct, 2=Low Shelf, 3=Bell, 4=Notch,
#                   5=High Shelf, 6=LP (12dB), 7=HP (12dB)
# Compressor2 Model: 0=Peak, 1=RMS, 2=Expand
# DrumBuss Drive Type: 0=Soft, 1=Medium, 2=Hard

RECIPE = {
    # -----------------------------------------------------------------------
    # KICK: Aggressive, punchy, saturated
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
            "2 Frequency A": 55,        # Hz - lower than house
            "2 Gain A": 4.0,            # dB - stronger boost
            "2 Resonance A": 0.6,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - aggressive mud cut
            "3 Frequency A": 350,       # Hz
            "3 Gain A": -4.0,           # dB
            "3 Resonance A": 0.5,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - click emphasis
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
            "Threshold": -22,           # dB - heavier
            "Ratio": 0.7,             # ~5:1
            "Attack": 5,               # ms - fast
            "Release": 60,             # ms - short
            "Output Gain": 2.0,        # dB - compensate
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,               # harder knee
            "Model": 0,                # Peak
            "Env Mode": 0,
        },
        "DrumBuss": {
            "Drive": 0.65,             # high drive
            "Drive Type": 2,           # Hard
            "Crunch": 0.4,             # more crunch
            "Damping Freq": 0.6,
            "Transients": 0.5,         # strong transient boost
            "Boom Freq": 0.35,
            "Boom Amt": 0.4,
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
    # BASS: Tight, controlled, aggressive
    # -----------------------------------------------------------------------
    "bass": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 30,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - body
            "2 Frequency A": 70,        # Hz
            "2 Gain A": 3.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP 12dB - tighter
            "3 Frequency A": 160,       # Hz - more aggressive filtering
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
            "Threshold": -24,           # dB - tight
            "Ratio": 0.65,            # ~4.5:1
            "Attack": 8,               # ms - fast
            "Release": 70,             # ms - short
            "Output Gain": 2.0,        # dB
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,
            "Model": 0,
            "Env Mode": 0,
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
    # LEAD: Sharp, present, tighter effects
    # -----------------------------------------------------------------------
    "lead": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 250,       # Hz - aggressive HP
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - sharp presence
            "2 Frequency A": 3500,      # Hz
            "2 Gain A": 3.0,            # dB - sharper
            "2 Resonance A": 0.6,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf
            "3 Frequency A": 9000,      # Hz
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
            "Threshold": -20,           # dB
            "Ratio": 0.55,            # ~3.5:1
            "Attack": 10,              # ms - fast
            "Release": 80,             # ms
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
            "HiFilter Freq": 0.55,     # darker than house
            "HiShelf Gain": -4.0,      # dB
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -4.0,
            "Decay Time": 0.25,         # ~1s - shorter
            "Diffusion": 0.6,
            "Scale": 0.6,
            "Room Size": 0.35,
            "Stereo Image": 0.6,
            "Density": 1,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.5,
            "Dry/Wet": 12,              # % - less reverb
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 2,               # 1/16 note - rhythmic
            "R 16th": 3,               # 1/8 note
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.35,
            "Filter On": 1,
            "Filter Freq": 0.45,        # darker
            "Filter Width": 0.5,
            "Dry/Wet": 20,              # % - more delay focus
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

    # -----------------------------------------------------------------------
    # PAD: Subtle, dark, background
    # -----------------------------------------------------------------------
    "pad": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 120,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 6,       # LP - darken
            "2 Frequency A": 8000,      # Hz
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
        "Compressor2": {
            "Threshold": -16,           # dB
            "Ratio": 0.35,            # ~2:1 gentle
            "Attack": 40,              # ms
            "Release": 250,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 8.0,
            "Model": 1,                # RMS
            "Env Mode": 1,
        },
        "Reverb": {
            "Predelay": 0.15,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.35,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.5,
            "ER Shape": 0.5,
            "HiFilter On": 1,
            "HiFilter Freq": 0.55,     # darker
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.4,          # ~1.8s
            "Diffusion": 0.7,
            "Scale": 0.7,
            "Room Size": 0.5,
            "Stereo Image": 0.8,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.6,
            "Dry/Wet": 20,              # % - subtler
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.4,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # CHORDS: Stab-like, tight, rhythmic
    # -----------------------------------------------------------------------
    "chords": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 180,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell
            "2 Frequency A": 600,       # Hz - mid emphasis
            "2 Gain A": 1.0,
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP - tame highs
            "3 Frequency A": 10000,     # Hz
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
            "Threshold": -18,           # dB
            "Ratio": 0.5,             # ~3:1
            "Attack": 8,               # ms - tight
            "Release": 80,             # ms
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
            "In Filter Freq": 0.4,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.4,
            "ER Shape": 0.4,
            "HiFilter On": 1,
            "HiFilter Freq": 0.55,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.2,          # ~0.8s - short
            "Diffusion": 0.6,
            "Scale": 0.5,
            "Room Size": 0.3,
            "Stereo Image": 0.5,
            "Density": 1,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.4,
            "Dry/Wet": 10,              # % - minimal
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 2,               # 1/16 - rhythmic
            "R 16th": 2,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.25,
            "Filter On": 1,
            "Filter Freq": 0.4,
            "Filter Width": 0.5,
            "Dry/Wet": 12,
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

    # -----------------------------------------------------------------------
    # VOCAL: Minimal -- clean utility EQ + light compression per D-03
    # -----------------------------------------------------------------------
    "vocal": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 100,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - presence
            "2 Frequency A": 3000,      # Hz
            "2 Gain A": 1.5,            # dB - subtle
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
        "Compressor2": {
            "Threshold": -16,           # dB - light
            "Ratio": 0.35,            # ~2:1
            "Attack": 15,              # ms
            "Release": 120,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 6.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.8,
            "Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # ATMOSPHERIC: Dark, delay-focused, wide
    # -----------------------------------------------------------------------
    "atmospheric": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 100,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 6,       # LP - darker
            "2 Frequency A": 10000,     # Hz
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
            "HiFilter Freq": 0.5,       # dark
            "HiShelf Gain": -5.0,        # dB - very dark
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.55,          # ~2.5s
            "Diffusion": 0.85,
            "Scale": 0.85,
            "Room Size": 0.7,
            "Stereo Image": 0.9,
            "Density": 2,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.7,
            "Dry/Wet": 35,               # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 3,               # 1/8 note
            "R 16th": 5,               # dotted 1/4
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.5,            # high feedback
            "Filter On": 1,
            "Filter Freq": 0.4,         # dark
            "Filter Width": 0.5,
            "Mod Freq": 0.3,            # modulated
            "Dly < Mod": 0.2,
            "Dry/Wet": 30,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.7,        # very wide
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # RETURN: Darker, shorter reverb; rhythmic delay
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
            "HiFilter Freq": 0.5,       # darker than house
            "HiShelf Gain": -4.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -4.0,
            "Decay Time": 0.35,          # ~1.5s - shorter
            "Diffusion": 0.7,
            "Scale": 0.7,
            "Room Size": 0.4,
            "Stereo Image": 0.7,
            "Density": 1,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.5,
            "Dry/Wet": 100,             # % - send
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 2,               # 1/16 - rhythmic
            "R 16th": 3,               # 1/8
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.4,
            "Filter On": 1,
            "Filter Freq": 0.4,
            "Filter Width": 0.5,
            "Dry/Wet": 100,             # % - send
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.0,
            "Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # MASTER: Minimal (Phase 34 adds full master chain)
    # -----------------------------------------------------------------------
    "master": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - subtle
            "2 Frequency A": 4000,      # Hz
            "2 Gain A": 0.5,
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
            "Gain": 0.0,
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
# Hard, loud, aggressive -- typical techno master chain
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -8.0,       # dB
        "Ratio": 0.6,            # approx 4:1
        "Attack": 0.2,           # fast
        "Release": 0.3,
        "Makeup": 3.0,           # dB
        "Dry/Wet": 100.0,        # % (100% wet)
        "Peak Clip In": 0,
        "Range": 0.5,
    },
    "MultibandDynamics": {
        "Master Output": 0.0,
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": -14.0,
        "Above Ratio (Low)": 0.7,
        "Above Threshold (Mid)": -12.0,
        "Above Ratio (Mid)": 0.6,
        "Above Threshold (High)": -10.0,
        "Above Ratio (High)": 0.6,
        "Input Gain (Low)": 0.0,
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": 5.0,       # dB
        "Ceiling": 0.9,          # near unity
        "Link": 1.0,
        "Lookahead": 1,
    },
}
