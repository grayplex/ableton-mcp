# House genre mix recipe
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
    # KICK: Tight low-end, punchy, mono
    # -----------------------------------------------------------------------
    "kick": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB/oct high-pass
            "1 Frequency A": 30,        # Hz - remove sub rumble
            "1 Gain A": 0.0,            # dB
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell
            "2 Frequency A": 60,        # Hz - boost fundamental
            "2 Gain A": 3.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 3,       # Bell - cut mud
            "3 Frequency A": 300,       # Hz
            "3 Gain A": -3.0,           # dB
            "3 Resonance A": 0.5,
            "4 Filter On A": 0,
            "5 Filter On A": 0,
            "6 Filter On A": 0,
            "7 Filter On A": 0,
            "8 Filter On A": 0,
            "Output Gain": 0.0,         # dB
            "Scale": 1.0,
            "Adaptive Q": 0,
        },
        "Compressor2": {
            "Threshold": -18,           # dB
            "Ratio": 0.6,              # 0-1 range (approx 4:1)
            "Attack": 10,              # ms
            "Release": 80,             # ms
            "Output Gain": 0.0,        # dB
            "Makeup": 0,               # auto makeup off
            "Dry/Wet": 100,            # %
            "Knee": 6.0,               # dB
            "Model": 0,                # Peak
            "Env Mode": 0,             # Peak
        },
        "DrumBuss": {
            "Drive": 0.4,              # moderate drive
            "Drive Type": 1,           # Medium
            "Crunch": 0.2,
            "Damping Freq": 0.7,
            "Transients": 0.3,         # boost transients
            "Boom Freq": 0.4,
            "Boom Amt": 0.3,
            "Boom Decay": 0.5,
            "Trim": 0.5,
            "Output Gain": 0.0,        # dB
            "Dry/Wet": 100,            # %
            "Compressor On": 1,
        },
        "StereoGain": {
            "Gain": 0.0,               # dB
            "Stereo Width": 0.0,        # mono
            "Mono": 1,
            "Bass Mono": 1,
            "Bass Freq": 0.5,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # BASS: Warm, controlled low-end, mono below 120Hz
    # -----------------------------------------------------------------------
    "bass": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 25,        # Hz - remove sub
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - boost body
            "2 Frequency A": 80,        # Hz
            "2 Gain A": 2.5,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 6,       # LP 12dB
            "3 Frequency A": 200,       # Hz - tame highs
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
            "Threshold": -20,           # dB
            "Ratio": 0.55,             # approx 3.5:1
            "Attack": 15,              # ms - fast
            "Release": 100,            # ms
            "Output Gain": 0.0,        # dB
            "Makeup": 0,
            "Dry/Wet": 100,            # %
            "Knee": 4.0,
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
    # LEAD: Present, clear, moderate space
    # -----------------------------------------------------------------------
    "lead": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 200,       # Hz - clear low end
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - presence
            "2 Frequency A": 3000,      # Hz
            "2 Gain A": 2.0,            # dB
            "2 Resonance A": 0.5,
            "3 Filter On A": 1,
            "3 Filter Type A": 5,       # High Shelf - air
            "3 Frequency A": 8000,      # Hz
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
            "Threshold": -16,           # dB
            "Ratio": 0.4,             # gentle ~2:1
            "Attack": 20,              # ms
            "Release": 150,            # ms
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
            "In HighCut On": 1,
            "In Filter Freq": 0.4,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.5,
            "ER Shape": 0.5,
            "HiFilter On": 1,
            "HiFilter Freq": 0.7,
            "HiShelf Gain": -2.0,       # dB - darken tail
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,      # dB - reduce low rumble
            "Decay Time": 0.35,         # ~1.5s
            "Diffusion": 0.7,
            "Scale": 0.7,
            "Room Size": 0.5,
            "Stereo Image": 0.7,
            "Density": 2,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.6,
            "Dry/Wet": 20,              # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 3,               # 1/8 note
            "R 16th": 3,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.3,
            "Filter On": 1,
            "Filter Freq": 0.6,
            "Filter Width": 0.5,
            "Dry/Wet": 15,              # %
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
    # PAD: Warm, wide, lush
    # -----------------------------------------------------------------------
    "pad": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 100,       # Hz - gentle low cut
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf - air
            "2 Frequency A": 10000,     # Hz
            "2 Gain A": 2.0,            # dB
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
            "Ratio": 0.35,            # ~2:1
            "Attack": 30,              # ms - slow
            "Release": 200,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 8.0,
            "Model": 1,                # RMS - smoother
            "Env Mode": 1,             # RMS
        },
        "Reverb": {
            "Predelay": 0.2,
            "In LowCut On": 1,
            "In HighCut On": 0,
            "In Filter Freq": 0.3,
            "In Filter Width": 0.7,
            "ER Spin On": 1,
            "ER Spin Rate": 0.4,
            "ER Spin Amount": 0.6,
            "ER Shape": 0.6,
            "HiFilter On": 1,
            "HiFilter Freq": 0.8,
            "HiShelf Gain": -1.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.55,         # ~2.5s
            "Diffusion": 0.8,
            "Scale": 0.8,
            "Room Size": 0.7,
            "Stereo Image": 0.9,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.7,
            "Dry/Wet": 30,              # %
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
    # CHORDS: Mid-focused, clear, moderate space
    # -----------------------------------------------------------------------
    "chords": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 150,       # Hz - cut low end
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - mid body
            "2 Frequency A": 500,       # Hz
            "2 Gain A": 1.5,            # dB
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
            "Threshold": -14,           # dB - gentle
            "Ratio": 0.35,
            "Attack": 20,              # ms
            "Release": 150,            # ms
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
            "In HighCut On": 1,
            "In Filter Freq": 0.4,
            "In Filter Width": 0.6,
            "ER Spin On": 1,
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.5,
            "ER Shape": 0.5,
            "HiFilter On": 1,
            "HiFilter Freq": 0.7,
            "HiShelf Gain": -2.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -2.0,
            "Decay Time": 0.4,          # ~1.8s
            "Diffusion": 0.7,
            "Scale": 0.7,
            "Room Size": 0.5,
            "Stereo Image": 0.7,
            "Density": 2,
            "Reflect Level": 0.5,
            "Diffuse Level": 0.6,
            "Dry/Wet": 20,              # %
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 4,               # 1/4 note
            "R 16th": 4,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.2,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.5,
            "Dry/Wet": 10,              # % - subtle
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
    # VOCAL: Clear, present, controlled
    # -----------------------------------------------------------------------
    "vocal": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 80,        # Hz - low cut
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
            "3 Gain A": 2.0,            # dB
            "3 Resonance A": 0.71,
            "4 Filter On A": 1,
            "4 Filter Type A": 3,       # Bell - cut nasal
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
            "Ratio": 0.5,             # ~3:1
            "Attack": 10,              # ms
            "Release": 100,            # ms
            "Output Gain": 0.0,
            "Makeup": 0,
            "Dry/Wet": 100,
            "Knee": 4.0,
            "Model": 0,
            "Env Mode": 0,
        },
        "Gate": {
            "Threshold": -35,           # dB - just clean noise
            "Attack": 0.5,             # ms - fast
            "Hold": 0.3,
            "Release": 50,             # ms
            "Return": 3.0,             # dB hysteresis
            "Floor": -40.0,            # dB
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
            "HiFilter Freq": 0.65,
            "HiShelf Gain": -3.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.3,          # ~1.2s plate-like
            "Diffusion": 0.8,
            "Scale": 0.6,
            "Room Size": 0.4,
            "Stereo Image": 0.6,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.5,
            "Dry/Wet": 15,              # %
        },
        "Delay": {
            "Ping Pong": 0,
            "L 16th": 3,               # 1/8 note
            "R 16th": 3,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.2,
            "Filter On": 1,
            "Filter Freq": 0.5,
            "Filter Width": 0.5,
            "Dry/Wet": 10,              # % - subtle
        },
        "StereoGain": {
            "Gain": 0.0,
            "Stereo Width": 0.8,        # near center
            "Mono": 0,
            "Bass Mono": 0,
            "Balance": 0.0,
        },
    },

    # -----------------------------------------------------------------------
    # ATMOSPHERIC: Wide, spacious, ethereal
    # -----------------------------------------------------------------------
    "atmospheric": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP
            "1 Frequency A": 80,        # Hz - gentle low cut
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 5,       # High Shelf - air
            "2 Frequency A": 8000,      # Hz
            "2 Gain A": 2.0,            # dB
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
            "Decay Time": 0.7,          # ~3s+ long tail
            "Diffusion": 0.9,
            "Scale": 0.9,
            "Room Size": 0.8,
            "Stereo Image": 0.95,
            "Density": 3,
            "Reflect Level": 0.3,
            "Diffuse Level": 0.8,
            "Dry/Wet": 40,              # %
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 5,               # long delay
            "R 16th": 6,
            "L Offset": 0.5,
            "R Offset": 0.5,
            "Feedback": 0.45,           # high feedback
            "Filter On": 1,
            "Filter Freq": 0.55,
            "Filter Width": 0.6,
            "Dry/Wet": 25,              # %
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
            "ER Spin Rate": 0.5,
            "ER Spin Amount": 0.5,
            "ER Shape": 0.5,
            "HiFilter On": 1,
            "HiFilter Freq": 0.7,
            "HiShelf Gain": -2.0,
            "LowShelf On": 1,
            "LowShelf Freq": 0.3,
            "LowShelf Gain": -3.0,
            "Decay Time": 0.5,          # ~2.2s
            "Diffusion": 0.8,
            "Scale": 0.8,
            "Room Size": 0.6,
            "Stereo Image": 0.8,
            "Density": 2,
            "Reflect Level": 0.4,
            "Diffuse Level": 0.7,
            "Dry/Wet": 100,             # % - send effect
        },
        "Delay": {
            "Ping Pong": 1,
            "L 16th": 3,               # 1/8 note
            "R 16th": 4,               # 1/4 note
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
    # MASTER: Minimal (Phase 34 adds full master chain)
    # -----------------------------------------------------------------------
    "master": {
        "Eq8": {
            "1 Filter On A": 1,
            "1 Filter Type A": 1,       # 12dB HP - subsonic
            "1 Frequency A": 25,        # Hz
            "1 Gain A": 0.0,
            "1 Resonance A": 0.71,
            "2 Filter On A": 1,
            "2 Filter Type A": 3,       # Bell - gentle broad
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
# Punchy, glued, loud -- classic house master chain
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": -6.0,       # dB (-40 to 0)
        "Ratio": 0.4,            # 0-2 range (approx 2:1)
        "Attack": 0.3,           # 0-6 raw range (medium-fast)
        "Release": 0.4,          # 0-6 raw range (auto-ish)
        "Makeup": 2.0,           # dB (-15 to 15 natural)
        "Dry/Wet": 100.0,        # % (0-100 natural -> linear)
        "Peak Clip In": 0,       # off
        "Range": 0.5,            # 0-70 raw range
    },
    "MultibandDynamics": {
        "Master Output": 0.0,    # dB (-24 to 24)
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": -12.0,   # dB
        "Above Ratio (Low)": 0.6,         # -1 to 1
        "Above Threshold (Mid)": -10.0,
        "Above Ratio (Mid)": 0.5,
        "Above Threshold (High)": -8.0,
        "Above Ratio (High)": 0.5,
        "Input Gain (Low)": 0.0,          # dB
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": 4.0,       # dB (-15 to 15 natural)
        "Ceiling": 0.7,          # 0-1 raw (lower = more limiting)
        "Link": 1.0,             # 0-1
        "Lookahead": 1,          # quantized 0-2 (0=off, 1=1ms, 2=6ms)
    },
}
