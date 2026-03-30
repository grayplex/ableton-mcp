# Dubstep genre mix recipe
# Per D-01: All values in natural units (Hz, dB, ms, %, 0-1 for raw params)
# Per D-02: Sound-shaping params only (no Device On, S/C Listen, etc.)
# Per D-03: All 9 roles present
# Per D-04: Omit devices not applicable (no None markers)
#
# Dubstep: Aggressive bass, heavy sub, distorted mids, punchy drums.
# Aggressive compression, heavy saturation, tight low-end control.
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
    # KICK: Very punchy, mono, aggressive saturation
    # -----------------------------------------------------------------------
    "kick": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 28,        # Hz - tight sub control
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - punch
            "2 Frequency A": 60,        # Hz
            "2 Gain A": 4.0,            # dB - heavy boost
            "2 Resonance A": 0.6,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - cut mud
            "3 Frequency A": 250,       # Hz
            "3 Gain A": -4.0,           # dB - aggressive cut
            "3 Resonance A": 0.5,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - click
            "4 Frequency A": 4500,      # Hz
            "4 Gain A": 3.5,            # dB
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
            "Threshold": -22,           # dB - heavy
            "Ratio": 0.7,              # ~5:1
            "Attack": 5,               # ms - fast
            "Release": 50,             # ms
            "Output Gain": 2.0,        # dB
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,               # hard knee
            "Model": 0,                # Peak
            "Env Mode": 0,
        },
        "DrumBuss": {
            "Drive": 0.7,              # aggressive
            "Drive Type": 2,           # Hard
            "Crunch": 0.4,
            "Damping Freq": 0.6,
            "Transients": 0.5,
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
    # BASS: Heavy sub, aggressive processing, distorted mids
    # -----------------------------------------------------------------------
    "bass": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 22,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 2,       # Low Shelf - sub boost
            "2 Frequency A": 60,        # Hz
            "2 Gain A": 3.0,            # dB - heavy sub
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - mid aggression
            "3 Frequency A": 800,       # Hz
            "3 Gain A": 2.0,            # dB - distorted mids
            "3 Resonance A": 0.5,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - cut harshness
            "4 Frequency A": 3000,      # Hz
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
            "Threshold": -24,           # dB - heavy compression
            "Ratio": 0.8,              # ~8:1 aggressive
            "Attack": 8,               # ms
            "Release": 60,             # ms - fast
            "Output Gain": 3.0,        # dB - makeup
            "Makeup": 0,
            "Dry/Wet": 100,
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
    # LEAD: Mid-heavy, distorted feel, aggressive presence
    # -----------------------------------------------------------------------
    "lead": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 200,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - aggressive mids
            "2 Frequency A": 1500,      # Hz
            "2 Gain A": 3.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - presence
            "3 Frequency A": 6000,      # Hz
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
            "Threshold": -20,           # dB
            "Ratio": 0.6,              # ~4:1
            "Attack": 10,              # ms
            "Release": 80,             # ms
            "Output Gain": 1.0,
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
            "In Filter Freq": 0.5,
            "In Filter Width": 0.5,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.4,
            "ER Shape": 0.4,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -3.0,       # dark reverb
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -4.0,
            "Decay Time": 0.25,         # ~1s short
            "Diffusion": 0.6,
            "Scale": 0.5,
            "Room Size": 0.4,
            "Stereo Image": 0.6,
            "Density": 2,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.5,
            "Dry/Wet": 12,              # % - subtle
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.0,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.45,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # PAD: Dark, atmospheric, wide
    # -----------------------------------------------------------------------
    "pad": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 150,       # Hz - clear of bass
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - mid body
            "2 Frequency A": 600,       # Hz
            "2 Gain A": 1.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP 12dB - darken
            "3 Frequency A": 8000,      # Hz
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
            "Threshold": -14,           # dB
            "Ratio": 0.4,             # ~2.5:1
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
            "In Filter Freq": 0.4,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.4,
            "ER Spin Amount": 0.5,
            "ER Shape": 0.5,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -3.0,       # dark reverb
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.45,         # ~2s
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
            "Stereo Width": 1.4,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.45,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # CHORDS: Aggressive, compressed, wide
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
            "2 Frequency A": 700,       # Hz
            "2 Gain A": 2.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf
            "3 Frequency A": 5000,      # Hz
            "3 Gain A": 1.5,            # dB
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
            "Ratio": 0.6,              # ~4:1
            "Attack": 15,              # ms
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
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.3,          # ~1.2s short
            "Diffusion": 0.6,
            "Scale": 0.6,
            "Room Size": 0.4,
            "Stereo Image": 0.6,
            "Density": 2,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.5,
            "Dry/Wet": 15,              # %
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.2,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.45,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # VOCAL: Clear, aggressive, present
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
            "2 Frequency A": 3500,      # Hz
            "2 Gain A": 3.0,            # dB - aggressive presence
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 8000,      # Hz
            "3 Gain A": 1.5,            # dB
            "3 Resonance A": 0.71,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - cut mud
            "4 Frequency A": 350,       # Hz
            "4 Gain A": -2.5,           # dB
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
            "Ratio": 0.6,              # ~4:1
            "Attack": 8,               # ms - fast
            "Release": 80,             # ms
            "Output Gain": 1.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 3.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Gate": {
            "Threshold": -30,           # dB - tight gate
            "Attack": 0.3,             # ms
            "Hold": 0.2,
            "Release": 40,             # ms
            "Return": 4.0,             # dB
            "Floor": -45.0,            # dB
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
            "HiShelf Gain": -4.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -4.0,
            "Decay Time": 0.2,          # ~0.8s very short
            "Diffusion": 0.6,
            "Scale": 0.5,
            "Room Size": 0.3,
            "Stereo Image": 0.5,
            "Density": 2,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.4,
            "Dry/Wet": 10,              # % - minimal
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.7,
            "Mono": 0,
            "Bass Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # ATMOSPHERIC: Dark, menacing, wide
    # -----------------------------------------------------------------------
    "atmospheric": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 120,       # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - mid texture
            "2 Frequency A": 1000,      # Hz
            "2 Gain A": 1.5,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP 12dB - darken
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
        "Reverb": {
            "Predelay": 0.15,
            "In LowCut On": 1,
            "In HighCut On": 1,
            "In Filter Freq": 0.45,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.3,
            "ER Spin Amount": 0.6,
            "ER Shape": 0.6,
            "HiFilter On": 1,
            "HiFilter Freq": 0.55,
            "HiShelf Gain": -4.0,       # very dark
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.5,          # ~2.2s
            "Diffusion": 0.7,
            "Scale": 0.7,
            "Room Size": 0.6,
            "Stereo Image": 0.85,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.7,
            "Dry/Wet": 35,              # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 4,               # 1/4 note
            "R 16th": 5,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.4,
            "Filter On": 1,
            "Filter Freq": 0.45,        # dark delay
            "Filter Width": 0.5,
            "Dry/Wet": 20,              # %
        },
        "AutoFilter2": {
            "Frequency": 0.5,
            "Resonance": 0.3,
            "Type": 0,           # Low-pass
            "LFO Amount": 0.2,
            "LFO Freq": 0.3,
            "LFO Phase": 0.5,
            "LFO Offset": 0.5,
            "Env Amount": 0.15,
            "Env Attack": 0.2,
            "Env Release": 0.4,
            "Dry/Wet": 100,
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 1.6,
            "Mono": 0,
            "Bass Mono": 1,
            "Bass Freq": 0.45,
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
            "ER Spin Amount": 0.5,
            "ER Shape": 0.5,
            "HiFilter On": 1,
            "HiFilter Freq": 0.6,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.35,
            "LowShelf Gain": -4.0,
            "Decay Time": 0.35,         # ~1.5s
            "Diffusion": 0.7,
            "Scale": 0.6,
            "Room Size": 0.5,
            "Stereo Image": 0.7,
            "Density": 2,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.6,
            "Dry/Wet": 100,             # % - send effect
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 3,               # 1/8 note
            "R 16th": 4,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.3,
            "Filter On": 1,
            "Filter Freq": 0.45,
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
    # MASTER: Heavy, aggressive processing
    # -----------------------------------------------------------------------
    "master": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP - subsonic
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 2,       # Low Shelf - sub boost
            "2 Frequency A": 60,        # Hz
            "2 Gain A": 1.5,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - cut mud
            "3 Frequency A": 300,       # Hz
            "3 Gain A": -1.0,           # dB
            "3 Resonance A": 0.3,
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
            "Bass Freq": 0.45,
            "Balance": 0.0,
        },
    },
}

# ---------------------------------------------------------------------------
# Master bus recipe: GlueCompressor -> MultibandDynamics -> Limiter
# Very loud, heavy limiting, strong low band compression -- dubstep master
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -8.0,       # dB - heavy glue
        "Ratio": 0.6,            # ~3:1
        "Attack": 0.2,           # fast
        "Release": 0.3,          # fast-medium
        "Makeup": 4.0,           # dB
        "Dry/Wet": 100.0,        # %
        "Peak Clip In": 0,
        "Range": 0.6,
    },
    "MultibandDynamics": {
        "Master Output": 0.0,
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": -15.0,   # heavy low compression
        "Above Ratio (Low)": 0.7,
        "Above Threshold (Mid)": -12.0,
        "Above Ratio (Mid)": 0.6,
        "Above Threshold (High)": -10.0,
        "Above Ratio (High)": 0.5,
        "Input Gain (Low)": 0.0,
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": 7.0,       # dB - very loud
        "Ceiling": 0.6,          # aggressive limiting
        "Link": 1.0,
        "Lookahead": 1,          # 1ms
    },
}
