"""Signal lexicon for the prompt parser.

Maps normalized terms (lowercase, underscores for spaces/hyphens) to signal values
across five signal types: genre, mood, instrument, effect, and tempo.

Normalization convention: terms use underscores as separators internally;
the parser normalizes input tokens to this form before lookup.
"""

# ---------------------------------------------------------------------------
# Genre map: normalized alias → genre blueprint id
# ---------------------------------------------------------------------------
# Keys use underscores. Longer phrases must be listed explicitly so the parser
# can try longer matches first.

GENRE_MAP: dict[str, str] = {
    # lo_fi — multi-word phrases first
    "lo_fi_hip_hop": "lo_fi",
    "lo_fi_jazz": "lo_fi",
    "lo_fi_beats": "lo_fi",
    "lo_fi_music": "lo_fi",
    "lo_fi_hip_hop_beats": "lo_fi",
    "lo_fi": "lo_fi",
    "lofi": "lo_fi",
    "chillhop": "lo_fi",
    # hip_hop_trap
    "hip_hop_trap": "hip_hop_trap",
    "hip_hop": "hip_hop_trap",
    "hiphop": "hip_hop_trap",
    "trap_music": "hip_hop_trap",
    "trap_beat": "hip_hop_trap",
    "trap": "hip_hop_trap",
    "rap": "hip_hop_trap",
    "boom_bap_hip_hop": "hip_hop_trap",
    # house
    "house_music": "house",
    "deep_house": "house",
    "tech_house": "house",
    "house": "house",
    # techno
    "techno_music": "techno",
    "minimal_techno": "techno",
    "industrial_techno": "techno",
    "techno": "techno",
    # drum_and_bass
    "drum_and_bass": "drum_and_bass",
    "drum_n_bass": "drum_and_bass",
    "dnb": "drum_and_bass",
    # dubstep
    "dubstep_music": "dubstep",
    "brostep": "dubstep",
    "dubstep": "dubstep",
    # trance
    "trance_music": "trance",
    "psytrance": "trance",
    "progressive_trance": "trance",
    "trance": "trance",
    # ambient
    "ambient_music": "ambient",
    "atmospheric_ambient": "ambient",
    "dark_ambient": "ambient",
    "ambient": "ambient",
    "atmospheric": "ambient",
    "drone": "ambient",
    # synthwave
    "synthwave_music": "synthwave",
    "synth_wave": "synthwave",
    "retro_synth": "synthwave",
    "retrowave": "synthwave",
    "synthwave": "synthwave",
    # future_bass
    "future_bass": "future_bass",
    "futurewave": "future_bass",
    # neo_soul_rnb
    "neo_soul_rnb": "neo_soul_rnb",
    "neo_soul": "neo_soul_rnb",
    "rhythm_and_blues": "neo_soul_rnb",
    "rnb": "neo_soul_rnb",
    "soul_music": "neo_soul_rnb",
    "soul": "neo_soul_rnb",
    # disco_funk
    "disco_funk": "disco_funk",
    "funk_music": "disco_funk",
    "disco_music": "disco_funk",
    "disco": "disco_funk",
    "funk": "disco_funk",
}

# ---------------------------------------------------------------------------
# Mood map: normalized adjective → {energy_level, scale_bias}
# scale_bias: "major" | "minor" | "phrygian" | "dorian" | "lydian" | None
# ---------------------------------------------------------------------------

MOOD_MAP: dict[str, dict] = {
    # Euphoric / uplifting
    "euphoric": {"energy_level": 8, "scale_bias": "major"},
    "uplifting": {"energy_level": 7, "scale_bias": "major"},
    "happy": {"energy_level": 6, "scale_bias": "major"},
    "joyful": {"energy_level": 6, "scale_bias": "major"},
    "bright": {"energy_level": 6, "scale_bias": "major"},
    "sunny": {"energy_level": 5, "scale_bias": "major"},
    "triumphant": {"energy_level": 9, "scale_bias": "major"},
    # Dark / melancholic
    "dark": {"energy_level": 5, "scale_bias": "minor"},
    "melancholic": {"energy_level": 3, "scale_bias": "minor"},
    "sad": {"energy_level": 2, "scale_bias": "minor"},
    "moody": {"energy_level": 4, "scale_bias": "minor"},
    "haunting": {"energy_level": 4, "scale_bias": "phrygian"},
    "mysterious": {"energy_level": 4, "scale_bias": "phrygian"},
    "sinister": {"energy_level": 5, "scale_bias": "phrygian"},
    "ominous": {"energy_level": 5, "scale_bias": "phrygian"},
    "heavy": {"energy_level": 7, "scale_bias": "minor"},
    "aggressive": {"energy_level": 9, "scale_bias": "minor"},
    "intense": {"energy_level": 8, "scale_bias": "minor"},
    "eerie": {"energy_level": 4, "scale_bias": "phrygian"},
    # Chill / relaxed
    "chill": {"energy_level": 3, "scale_bias": None},
    "chilled": {"energy_level": 3, "scale_bias": None},
    "relaxed": {"energy_level": 2, "scale_bias": None},
    "mellow": {"energy_level": 2, "scale_bias": None},
    "dreamy": {"energy_level": 3, "scale_bias": "lydian"},
    "hazy": {"energy_level": 2, "scale_bias": None},
    "lazy": {"energy_level": 2, "scale_bias": None},
    "smooth": {"energy_level": 3, "scale_bias": None},
    "soft": {"energy_level": 2, "scale_bias": None},
    "gentle": {"energy_level": 2, "scale_bias": None},
    "nostalgic": {"energy_level": 3, "scale_bias": None},
    "vintage": {"energy_level": 4, "scale_bias": None},
    "warm": {"energy_level": 4, "scale_bias": None},
    # Energetic / driving
    "driving": {"energy_level": 8, "scale_bias": None},
    "energetic": {"energy_level": 8, "scale_bias": None},
    "pumping": {"energy_level": 8, "scale_bias": None},
    "hard": {"energy_level": 8, "scale_bias": "minor"},
    "pounding": {"energy_level": 9, "scale_bias": "minor"},
    "hard_hitting": {"energy_level": 9, "scale_bias": "minor"},
    # Groove / feel
    "minimal": {"energy_level": 5, "scale_bias": None},
    "groovy": {"energy_level": 6, "scale_bias": None},
    "funky": {"energy_level": 6, "scale_bias": "dorian"},
    "jazzy": {"energy_level": 5, "scale_bias": "dorian"},
    "soulful": {"energy_level": 5, "scale_bias": "dorian"},
    "bouncy": {"energy_level": 6, "scale_bias": None},
    "punchy": {"energy_level": 7, "scale_bias": None},
}

# ---------------------------------------------------------------------------
# Instrument map: normalized reference → {role, descriptor}
# ---------------------------------------------------------------------------

INSTRUMENT_MAP: dict[str, dict] = {
    # Keys / melodic
    "rhodes": {"role": "keys", "descriptor": "warm"},
    "electric_piano": {"role": "keys", "descriptor": "warm"},
    "piano": {"role": "piano", "descriptor": "melodic"},
    "keys": {"role": "keys", "descriptor": "warm"},
    "organ": {"role": "keys", "descriptor": "organ"},
    "synth": {"role": "synth_lead", "descriptor": "lead"},
    "lead_synth": {"role": "synth_lead", "descriptor": "bright"},
    "pad": {"role": "pad", "descriptor": "warm_pad"},
    "strings": {"role": "strings", "descriptor": "lush"},
    "choir": {"role": "choir", "descriptor": "vocal"},
    "pluck": {"role": "synth_lead", "descriptor": "pluck"},
    "arp": {"role": "arp", "descriptor": "arpeggiated"},
    "flute": {"role": "lead", "descriptor": "bright"},
    "brass": {"role": "lead", "descriptor": "punchy"},
    # Bass
    "bass": {"role": "bass", "descriptor": "bass"},
    "808": {"role": "bass", "descriptor": "808"},
    "sub_bass": {"role": "bass", "descriptor": "sub"},
    "bassline": {"role": "bass", "descriptor": "bass"},
    "sub": {"role": "bass", "descriptor": "sub"},
    "wobble_bass": {"role": "bass", "descriptor": "wobble"},
    # Drums / percussion
    "drums": {"role": "drums", "descriptor": "drum_kit"},
    "drum_kit": {"role": "drums", "descriptor": "drum_kit"},
    "kick": {"role": "kick", "descriptor": "punchy"},
    "snare": {"role": "snare", "descriptor": "snappy"},
    "hi_hats": {"role": "hi_hats", "descriptor": "crispy"},
    "hihat": {"role": "hi_hats", "descriptor": "crispy"},
    "hi_hat": {"role": "hi_hats", "descriptor": "crispy"},
    "hats": {"role": "hi_hats", "descriptor": "crispy"},
    "cymbal": {"role": "hi_hats", "descriptor": "open"},
    "clap": {"role": "snare", "descriptor": "snappy"},
    "percussion": {"role": "percussion", "descriptor": "percussive"},
    "perc": {"role": "percussion", "descriptor": "percussive"},
    # Guitar
    "guitar": {"role": "guitar", "descriptor": "electric_guitar"},
    "acoustic_guitar": {"role": "guitar", "descriptor": "acoustic"},
    "acoustic": {"role": "guitar", "descriptor": "acoustic"},
    "sample": {"role": "sample", "descriptor": "sample"},
}

# ---------------------------------------------------------------------------
# Effect map: normalized reference → effect descriptor string
# ---------------------------------------------------------------------------

EFFECT_MAP: dict[str, str] = {
    "vinyl_crackle": "vinyl_crackle",
    "vinyl_noise": "vinyl_crackle",
    "vinyl": "vinyl_crackle",
    "tape_saturation": "tape_saturation",
    "tape": "tape_saturation",
    "tape_hiss": "tape_saturation",
    "saturation": "tape_saturation",
    "reverb": "reverb",
    "delay": "delay",
    "echo": "delay",
    "sidechain_compression": "sidechain_compression",
    "sidechain": "sidechain_compression",
    "distortion": "distortion",
    "overdrive": "distortion",
    "bitcrusher": "bitcrusher",
    "bitcrush": "bitcrusher",
    "lo_fi_filter": "lo_fi_filter",
    "low_pass_filter": "lo_fi_filter",
    "lowpass": "lo_fi_filter",
    "chorus": "chorus",
    "flanger": "flanger",
    "phaser": "phaser",
    "compression": "compression",
    "compressor": "compression",
    "limiter": "limiter",
    "glitch": "glitch_fx",
    "stutter": "glitch_fx",
    "wobble": "wobble_bass",
    "growl": "growl_bass",
    "filter": "lo_fi_filter",
}

# ---------------------------------------------------------------------------
# Tempo map: normalized term → BPM offset modifier
# Applied to genre BPM range after energy adjustment.
# ---------------------------------------------------------------------------

TEMPO_MAP: dict[str, int] = {
    "slow": -15,
    "slow_tempo": -15,
    "plodding": -25,
    "dragging": -25,
    "mid_tempo": 0,
    "midtempo": 0,
    "moderate": 0,
    "medium_tempo": 0,
    "fast": 15,
    "fast_tempo": 15,
    "quick": 10,
    "rapid": 20,
    "frantic": 30,
    "uptempo": 12,
    "up_tempo": 12,
    "breakneck": 35,
}

# ---------------------------------------------------------------------------
# Structural hints: non-semantic production context terms
# ---------------------------------------------------------------------------

STRUCTURAL_HINTS: set[str] = {
    "beat", "beats", "track", "tracks", "song", "anthem", "banger", "vibe",
    "vibes", "tune", "groove", "grooves", "club", "dancefloor", "dance",
    "floor", "mix", "remix", "edit", "rework", "bootleg", "loop", "loops",
    "intro", "drop", "build", "buildup", "breakdown", "outro", "bridge",
    "verse", "chorus", "hook", "pattern", "jam", "session", "jam_session",
    "boom_bap", "boom-bap", "four_on_the_floor", "half_time", "breakbeat",
}

# ---------------------------------------------------------------------------
# Groove hint overrides: structural terms that directly map to groove parameters
# ---------------------------------------------------------------------------

GROOVE_HINTS: dict[str, tuple] = {
    "boom_bap": ("boom_bap", 65),
    "four_on_the_floor": ("four_on_floor", 0),
    "four_on_floor": ("four_on_floor", 0),
    "breakbeat": ("breakbeat", 15),
    "half_time": ("half_time", 0),
    "straight": ("straight_16th", 0),
}
