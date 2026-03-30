# Hip-Hop/Trap genre mix recipe
# Per D-01: All values in natural units (Hz, dB, ms, %, 0-1 for raw params)
# Per D-02: Sound-shaping params only (no Device On, S/C Listen, etc.)
# Per D-03: All 9 roles present
# Per D-04: Omit devices not applicable (no None markers)
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
    # KICK: Hard-hitting, punchy, aggressive compression, mono
    # -----------------------------------------------------------------------
    "kick": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB/oct high-pass
            "1 Frequency A": 28,        # Hz - remove sub rumble
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - boost fundamental
            "2 Frequency A": 55,        # Hz - deep 808 thump
            "2 Gain A": 4.0,            # dB - strong boost
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - cut mud
            "3 Frequency A": 250,       # Hz
            "3 Gain A": -4.0,           # dB - aggressive cut
            "3 Resonance A": 0.5,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - attack click
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
            "Threshold": -20,           # dB
            "Ratio": 0.65,             # 0-1 range (approx 4.5:1) - aggressive
            "Attack": 5,               # ms - very fast
            "Release": 60,             # ms - quick release
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,            # %
            "Knee": 3.0,               # dB - hard knee
            "Model": 0,                # Peak
            "Env Mode": 0,             # Peak
        },
        "DrumBuss": {
            "Drive": 0.6,              # aggressive drive
            "Drive Type": 2,           # Hard
            "Crunch": 0.35,
            "Damping Freq": 0.6,
            "Transients": 0.5,         # strong transient boost
            "Boom Freq": 0.35,
            "Boom Amt": 0.4,
            "Boom Decay": 0.6,
            "Trim": 0.5,
            "Output Gain": 0.0,
            "Dry/Wet": 100,            # %
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
    # BASS: Heavy 808 sub, mono, deep and controlled
    # -----------------------------------------------------------------------
    "bass": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 22,        # Hz - keep deep sub
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 2,       # Low Shelf - boost sub
            "2 Frequency A": 60,        # Hz
            "2 Gain A": 3.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP 12dB - tame highs
            "3 Frequency A": 180,       # Hz
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
            "Threshold": -22,           # dB
            "Ratio": 0.6,              # approx 4:1
            "Attack": 10,              # ms
            "Release": 80,             # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,            # %
            "Knee": 3.0,
            "Model": 0,                # Peak
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
    # LEAD: Bright, crisp, present melody
    # -----------------------------------------------------------------------
    "lead": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 250,       # Hz - clear low end
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - presence
            "2 Frequency A": 3500,      # Hz
            "2 Gain A": 3.0,            # dB - crisp
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
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
            "Threshold": -16,
            "Ratio": 0.45,             # ~2.5:1
            "Attack": 15,
            "Release": 120,
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 6.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 3,               # 1/8 note
            "R 16th": 3,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.2,
            "Filter On": 1,
            "Filter Freq": 0.55,
            "Filter Width": 0.5,
            "Dry/Wet": 12,              # % - subtle
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.0,        # normal
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # PAD: Warm, wide, atmospheric background
    # -----------------------------------------------------------------------
    "pad": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 120,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf
            "2 Frequency A": 8000,      # Hz
            "2 Gain A": -1.0,           # dB - slightly dark
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
            "Threshold": -14,
            "Ratio": 0.35,             # ~2:1
            "Attack": 30,
            "Release": 200,
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
            "In HighCut On": 0,
            "In Filter Freq": 0.3,
            "In Filter Width": 0.7,
            "ER Spin On": 1,
            "ER Spin Rate": 0.4,
            "ER Spin Amount": 0.5,
            "ER Shape": 0.5,
            "HiFilter On": 1,
            "HiFilter Freq": 0.7,
            "HiShelf Gain": -2.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.3,          # ~1.2s - short for trap
            "Diffusion": 0.6,
            "Scale": 0.6,
            "Room Size": 0.4,
            "Stereo Image": 0.8,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.5,
            "Dry/Wet": 18,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.4,        # wide
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.4,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # CHORDS: Clean, mid-focused, slightly dark
    # -----------------------------------------------------------------------
    "chords": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 180,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - mid body
            "2 Frequency A": 600,       # Hz
            "2 Gain A": 1.0,
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf
            "3 Frequency A": 7000,      # Hz
            "3 Gain A": -1.0,           # dB - slightly dark
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
            "Threshold": -14,
            "Ratio": 0.35,
            "Attack": 20,
            "Release": 150,
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 6.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 4,               # 1/4 note
            "R 16th": 4,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.15,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.5,
            "Dry/Wet": 8,              # % - subtle
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
    # VOCAL: Crisp, present, gated, star of the mix
    # -----------------------------------------------------------------------
    "vocal": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 90,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - presence
            "2 Frequency A": 4000,      # Hz
            "2 Gain A": 3.0,            # dB - crisp
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 10000,     # Hz
            "3 Gain A": 2.5,            # dB - bright
            "3 Resonance A": 0.71,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - cut nasal
            "4 Frequency A": 350,       # Hz
            "4 Gain A": -3.0,           # dB
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
            "Threshold": -20,           # dB - aggressive
            "Ratio": 0.55,             # ~3.5:1
            "Attack": 5,               # ms - fast
            "Release": 80,             # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,               # dB - hard knee
            "Model": 0,
            "Env Mode": 0,
        },
        "Gate": {
            "Threshold": -30,           # dB
            "Attack": 0.3,             # ms - very fast
            "Hold": 0.4,
            "Release": 40,             # ms
            "Return": 4.0,             # dB hysteresis
            "Floor": -50.0,            # dB - deep gate
        },
        "Reverb": {
            "Predelay": 0.08,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.5,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.4,
            "ER Shape": 0.4,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.2,          # ~0.8s - short plate
            "Diffusion": 0.7,
            "Scale": 0.5,
            "Room Size": 0.3,
            "Stereo Image": 0.5,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.4,
            "Dry/Wet": 10,              # % - mostly dry
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 3,               # 1/8 note
            "R 16th": 3,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.15,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.5,
            "Dry/Wet": 8,              # % - very subtle
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.7,        # near center
            "Mono": 0,
            "Bass Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # ATMOSPHERIC: Dark, spacious, filtered
    # -----------------------------------------------------------------------
    "atmospheric": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 100,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf - dark
            "2 Frequency A": 6000,      # Hz
            "2 Gain A": -2.0,           # dB - cut highs
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
            "Predelay": 0.2,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.35,
            "In Filter Width": 0.7,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.6,
            "ER Shape": 0.6,
            "HiFilter On": 1,
            "HiFilter Freq": 0.7,
            "HiShelf Gain": -2.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.5,          # ~2.2s
            "Diffusion": 0.8,
            "Scale": 0.7,
            "Room Size": 0.6,
            "Stereo Image": 0.85,
            "Density": 2,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.7,
            "Dry/Wet": 30,              # %
        },
        "AutoFilter2": {
            "Frequency": 0.5,
            "Resonance": 0.3,
            "Type": 0,                  # low-pass
            "LFO Amount": 0.2,
            "LFO Freq": 0.3,
            "LFO Phase": 0.5,
            "LFO Offset": 0.0,
            "Env Amount": 0.15,
            "Env Attack": 0.3,
            "Env Release": 0.5,
            "Dry/Wet": 100,
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.6,        # wide
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
            "HiFilter Freq": 0.65,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.25,         # ~1s - short for trap
            "Diffusion": 0.7,
            "Scale": 0.6,
            "Room Size": 0.4,
            "Stereo Image": 0.7,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.5,
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
    # MASTER: Minimal EQ, mono bass
    # -----------------------------------------------------------------------
    "master": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP - subsonic
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - punch
            "2 Frequency A": 3000,      # Hz
            "2 Gain A": 1.0,            # dB
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
# Hard-hitting, loud, aggressive -- classic hip-hop/trap master chain
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -8.0,       # dB (-40 to 0)
        "Ratio": 0.6,            # 0-2 range (approx 3:1)
        "Attack": 0.2,           # 0-6 raw range (fast)
        "Release": 0.3,          # 0-6 raw range
        "Makeup": 4.0,           # dB (-15 to 15 natural)
        "Dry/Wet": 100.0,        # % (0-100 natural -> linear)
        "Peak Clip In": 0,       # off
        "Range": 0.4,            # 0-70 raw range
    },
    "MultibandDynamics": {
        "Master Output": 0.0,    # dB (-24 to 24)
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": -10.0,
        "Above Ratio (Low)": 0.7,
        "Above Threshold (Mid)": -8.0,
        "Above Ratio (Mid)": 0.6,
        "Above Threshold (High)": -6.0,
        "Above Ratio (High)": 0.55,
        "Input Gain (Low)": 0.0,
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": 8.0,       # dB - very loud
        "Ceiling": 0.75,         # 0-1 raw
        "Link": 1.0,
        "Lookahead": 1,          # 1ms
    },
}
