"""Parameter derivation engine: translate a free-text prompt into a ProductionBrief.

Implements all five DERV-* requirements:
- DERV-01: Tempo range from explicit BPM or genre blueprint + energy modifier
- DERV-02: Key feel from genre convention + mood signal override
- DERV-03: Groove feel (pattern_type + swing_pct) from genre + structural hints
- DERV-04: Instrument hints from explicit references + genre blueprint roles
- DERV-05: Velocity style from energy level + mood signal override

Each derivation step appends a plain-English note to the `reasoning` list.
All logic is deterministic — same prompt always yields same ProductionBrief.
"""

import re
from typing import Optional

from MCP_Server.genres.catalog import get_blueprint
from MCP_Server.prompt.lexicon import GROOVE_HINTS
from MCP_Server.prompt.parser import classify_prompt
from MCP_Server.prompt.schema import ProductionBrief

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default BPM range when no genre is resolved
_FALLBACK_BPM = (80, 130)

# Default energy level when no mood signals
_DEFAULT_ENERGY = 5

# Scales classified as minor-mode
_MINOR_SCALES = {
    "natural_minor", "dorian", "phrygian", "harmonic_minor",
    "minor_pentatonic", "aeolian", "locrian",
}

# Scale bias → preferred scale name (major / minor override)
_SCALE_BIAS_MAP = {
    "major": "major",
    "minor": "natural_minor",
    "phrygian": "phrygian",
    "dorian": "dorian",
    "lydian": "lydian",
    "mixolydian": "mixolydian",
}

# Genre blueprint id → (pattern_type, swing_pct)
_GROOVE_MAP: dict[str, tuple] = {
    "lo_fi": ("boom_bap", 65),
    "hip_hop_trap": ("boom_bap", 20),
    "house": ("four_on_floor", 0),
    "disco_funk": ("four_on_floor", 10),
    "techno": ("four_on_floor", 0),
    "drum_and_bass": ("breakbeat", 15),
    "dubstep": ("half_time", 0),
    "future_bass": ("half_time", 0),
    "trance": ("straight_16th", 0),
    "synthwave": ("straight_16th", 0),
    "ambient": ("minimal", 0),
    "neo_soul_rnb": ("laid_back_groove", 40),
}

# Genre blueprint role → {role, descriptor} for instrument hint derivation
_ROLE_DESCRIPTOR_MAP: dict[str, dict] = {
    "vinyl_noise": {"role": "vinyl_noise", "descriptor": "vinyl_crackle"},
    "piano": {"role": "piano", "descriptor": "warm"},
    "keys": {"role": "keys", "descriptor": "warm"},
    "bass": {"role": "bass", "descriptor": "bass"},
    "guitar": {"role": "guitar", "descriptor": "electric_guitar"},
    "kick": {"role": "kick", "descriptor": "punchy"},
    "snare": {"role": "snare", "descriptor": "snappy"},
    "hi-hats": {"role": "hi_hats", "descriptor": "crispy"},
    "hi_hats": {"role": "hi_hats", "descriptor": "crispy"},
    "pad": {"role": "pad", "descriptor": "warm_pad"},
    "synth": {"role": "synth_lead", "descriptor": "lead"},
    "synth_lead": {"role": "synth_lead", "descriptor": "lead"},
    "sample": {"role": "sample", "descriptor": "sample"},
    "fx": {"role": "fx", "descriptor": "fx"},
    "strings": {"role": "strings", "descriptor": "lush"},
    "choir": {"role": "choir", "descriptor": "vocal"},
    "organ": {"role": "organ", "descriptor": "organ"},
    "clap": {"role": "clap", "descriptor": "snappy"},
    "lead": {"role": "lead", "descriptor": "bright"},
    "arp": {"role": "arp", "descriptor": "arpeggiated"},
    "perc": {"role": "percussion", "descriptor": "percussive"},
    "percussion": {"role": "percussion", "descriptor": "percussive"},
    "808": {"role": "bass", "descriptor": "808"},
    "sub": {"role": "bass", "descriptor": "sub"},
}


# ---------------------------------------------------------------------------
# Individual derivation helpers
# ---------------------------------------------------------------------------


def _derive_energy_level(mood_signals: list) -> tuple[int, str]:
    """Derive energy level 1–10 from mood signals.

    Returns (energy_level, reasoning_note).
    """
    if not mood_signals:
        return _DEFAULT_ENERGY, f"no mood signals → energy_level={_DEFAULT_ENERGY} (neutral default)"

    avg = sum(m["energy_level"] for m in mood_signals) / len(mood_signals)
    energy = max(1, min(10, round(avg)))
    terms = ", ".join(m["term"] for m in mood_signals)
    return energy, f"mood signals [{terms}] → energy_level={energy}"


def _derive_tempo(
    genre_id: Optional[str],
    mood_signals: list,
    tempo_signals: list,
    energy_level: int,
    raw_prompt: str,
) -> tuple[dict, str]:
    """Derive tempo range.

    Priority: explicit BPM in prompt > genre blueprint + energy modifier.
    Returns ({"min_bpm": int, "max_bpm": int}, reasoning_note).
    """
    # DERV-01a: explicit BPM number in prompt
    bpm_match = re.search(r"\b(\d{2,3})\s*(?:bpm|beats?\s+per\s+minute)\b", raw_prompt, re.IGNORECASE)
    if bpm_match:
        explicit_bpm = int(bpm_match.group(1))
        explicit_bpm = max(40, min(200, explicit_bpm))
        result = {"min_bpm": max(40, explicit_bpm - 5), "max_bpm": min(200, explicit_bpm + 5)}
        return result, f"explicit BPM {explicit_bpm} in prompt → tempo_range {result['min_bpm']}–{result['max_bpm']}"

    # DERV-01b: genre blueprint BPM range
    if genre_id:
        bp = get_blueprint(genre_id)
        if bp:
            min_bpm, max_bpm = bp["bpm_range"]
            note = f"genre {genre_id} blueprint BPM range [{min_bpm}–{max_bpm}]"
        else:
            min_bpm, max_bpm = _FALLBACK_BPM
            note = "no genre blueprint → fallback BPM range [80–130]"
    else:
        min_bpm, max_bpm = _FALLBACK_BPM
        note = "no genre resolved → fallback BPM range [80–130]"

    # Apply energy modifier: ±10% of range per energy point from neutral (5)
    energy_delta = (energy_level - 5) * 0.10
    min_bpm = int(max(40, min_bpm * (1 + energy_delta)))
    max_bpm = int(min(200, max_bpm * (1 + energy_delta)))

    # Apply tempo signal modifier
    if tempo_signals:
        total_modifier = sum(t["bpm_modifier"] for t in tempo_signals)
        min_bpm = max(40, min_bpm + total_modifier)
        max_bpm = min(200, max_bpm + total_modifier)
        tempo_terms = ", ".join(t["term"] for t in tempo_signals)
        note += f"; tempo signals [{tempo_terms}] applied +{total_modifier} BPM offset"

    if energy_level != _DEFAULT_ENERGY:
        note += f"; energy_level={energy_level} applied ±{energy_delta * 100:.0f}% modifier"

    result = {"min_bpm": int(min_bpm), "max_bpm": int(max_bpm)}
    return result, note


def _derive_key_feel(genre_id: Optional[str], mood_signals: list) -> tuple[dict, str]:
    """Derive key feel (scale + mode) from genre convention and mood override.

    DERV-02: genre default scale first, mood scale_bias overrides if present.
    Returns ({"scale": str, "mode": str}, reasoning_note).
    """
    # Determine genre default scale
    genre_scale = None
    if genre_id:
        bp = get_blueprint(genre_id)
        if bp:
            scales = bp.get("harmony", {}).get("scales", [])
            genre_scale = scales[0] if scales else None

    default_scale = genre_scale or "natural_minor"
    default_mode = "minor" if default_scale in _MINOR_SCALES else "major"
    note = f"genre {genre_id} default scale → {default_scale} ({default_mode})"

    # Mood scale_bias override
    biases = [m["scale_bias"] for m in mood_signals if m.get("scale_bias")]
    if biases:
        # Use the first non-None bias; if contradictory, first wins
        bias = biases[0]
        override_scale = _SCALE_BIAS_MAP.get(bias, default_scale)
        override_mode = "minor" if override_scale in _MINOR_SCALES else "major"
        bias_terms = [m["term"] for m in mood_signals if m.get("scale_bias") == bias]
        note += f"; mood signal {bias_terms[0]} overrides scale_bias={bias} → {override_scale} ({override_mode})"
        return {"scale": override_scale, "mode": override_mode}, note

    return {"scale": default_scale, "mode": default_mode}, note


def _derive_groove_feel(
    genre_id: Optional[str],
    structural_hints: list,
    raw_descriptors: list,
) -> tuple[dict, str]:
    """Derive groove feel (pattern_type + swing_pct) from genre and structural hints.

    DERV-03: Start with genre default, override from explicit groove hints in prompt.
    Returns ({"pattern_type": str, "swing_pct": int}, reasoning_note).
    """
    # Genre default
    if genre_id and genre_id in _GROOVE_MAP:
        pattern_type, swing_pct = _GROOVE_MAP[genre_id]
        note = f"genre {genre_id} → pattern_type={pattern_type}, swing_pct={swing_pct}"
    else:
        pattern_type, swing_pct = "four_on_floor", 0
        note = "no genre resolved → default four_on_floor, 0% swing"

    # Check structural hints for explicit groove overrides
    all_hints = structural_hints + raw_descriptors
    for hint in all_hints:
        hint_norm = hint.replace("-", "_")
        if hint_norm in GROOVE_HINTS:
            override_type, override_swing = GROOVE_HINTS[hint_norm]
            note += f"; structural hint '{hint}' overrides → {override_type}, {override_swing}% swing"
            pattern_type, swing_pct = override_type, override_swing
            break

    return {"pattern_type": pattern_type, "swing_pct": swing_pct}, note


def _derive_instrument_hints(
    genre_id: Optional[str],
    instrument_signals: list,
) -> tuple[list, str]:
    """Build instrument hints by merging explicit prompt refs with genre blueprint roles.

    DERV-04: Explicit prompt signals take precedence; genre roles fill in the gaps.
    Returns (instrument_hints_list, reasoning_note).
    """
    hints: list[dict] = []
    seen_roles: set[str] = set()

    # (a) Explicit instrument references from prompt (highest priority)
    for sig in instrument_signals:
        role = sig["role"]
        descriptor = sig["descriptor"]
        if role not in seen_roles:
            hints.append({"role": role, "descriptor": descriptor})
            seen_roles.add(role)

    # (b) Genre blueprint canonical roles (fill gaps)
    if genre_id:
        bp = get_blueprint(genre_id)
        if bp:
            roles = bp.get("instrumentation", {}).get("roles", [])
            for role_name in roles:
                if role_name in seen_roles:
                    continue
                mapping = _ROLE_DESCRIPTOR_MAP.get(role_name)
                if mapping:
                    hints.append({"role": mapping["role"], "descriptor": mapping["descriptor"]})
                    seen_roles.add(mapping["role"])

    source = f"{len(instrument_signals)} explicit + {len(hints) - len(instrument_signals)} from {genre_id} blueprint"
    note = f"instrument_hints built: {source} → {len(hints)} total"
    return hints, note


def _derive_velocity_style(energy_level: int, mood_signals: list) -> tuple[str, str]:
    """Derive velocity style from energy level with mood override.

    DERV-05: energy 1-3 → laid_back, 4-6 → medium, 7-10 → driving.
    Explicit mood signals 'soft'/'gentle' → laid_back; 'hard'/'aggressive' → driving.
    Returns (velocity_style, reasoning_note).
    """
    # Mood override takes priority
    for mood in mood_signals:
        term = mood.get("term", "")
        if term in ("soft", "gentle", "relaxed", "mellow", "lazy"):
            return "laid_back", f"mood signal '{term}' → velocity_style=laid_back"
        if term in ("hard", "aggressive", "pounding", "intense", "hard_hitting"):
            return "driving", f"mood signal '{term}' → velocity_style=driving"

    # Energy derivation
    if energy_level <= 3:
        style = "laid_back"
    elif energy_level <= 6:
        style = "medium"
    else:
        style = "driving"

    return style, f"energy_level={energy_level} → velocity_style={style}"


def _derive_effect_hints(effect_signals: list) -> tuple[list, str]:
    """Collect effect hints from extracted effect signals.

    Returns (effect_hints list, reasoning_note).
    """
    if not effect_signals:
        return [], "no effect signals in prompt"
    unique = list(dict.fromkeys(effect_signals))  # deduplicate, preserve order
    return unique, f"effect signals extracted: {unique}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def derive(text: str) -> ProductionBrief:
    """Derive a fully-populated ProductionBrief from a free-text music prompt.

    Runs signal classification then applies all five DERV-* derivation steps.
    Returns a ProductionBrief with all fields populated and a reasoning list
    explaining each parameter choice.

    Low-confidence results (no genre, no mood) return primary_genre=None
    and confidence < 0.3 without raising an exception.
    """
    signal_set = classify_prompt(text)
    reasoning: list[str] = []

    # Resolve primary genre (first genre signal wins)
    genre_signals = signal_set["genre_signals"]
    primary_genre = genre_signals[0] if genre_signals else None
    if primary_genre:
        reasoning.append(f"genre signal '{primary_genre}' detected → primary_genre={primary_genre}")
    else:
        reasoning.append("no genre signal detected → primary_genre=None")

    # Energy level
    energy_level, energy_note = _derive_energy_level(signal_set["mood_signals"])
    reasoning.append(energy_note)

    # Tempo range
    tempo_range, tempo_note = _derive_tempo(
        primary_genre,
        signal_set["mood_signals"],
        signal_set["tempo_signals"],
        energy_level,
        text,
    )
    reasoning.append(tempo_note)

    # Key feel
    key_feel, key_note = _derive_key_feel(primary_genre, signal_set["mood_signals"])
    reasoning.append(key_note)

    # Groove feel
    groove_feel, groove_note = _derive_groove_feel(
        primary_genre,
        signal_set["structural_hints"],
        signal_set["raw_descriptors"],
    )
    reasoning.append(groove_note)

    # Instrument hints
    instrument_hints, inst_note = _derive_instrument_hints(
        primary_genre,
        signal_set["instrument_signals"],
    )
    reasoning.append(inst_note)

    # Effect hints
    effect_hints, effect_note = _derive_effect_hints(signal_set["effect_signals"])
    reasoning.append(effect_note)

    # Velocity style
    velocity_style, vel_note = _derive_velocity_style(energy_level, signal_set["mood_signals"])
    reasoning.append(vel_note)

    return ProductionBrief(
        raw_prompt=text,
        primary_genre=primary_genre,
        tempo_range=tempo_range,
        key_feel=key_feel,
        groove_feel=groove_feel,
        energy_level=energy_level,
        instrument_hints=instrument_hints,
        effect_hints=effect_hints,
        velocity_style=velocity_style,
        confidence=signal_set["confidence"],
        reasoning=reasoning,
    )
