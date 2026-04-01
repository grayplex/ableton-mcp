"""Refinement lexicon: aesthetic adjectives -> multi-domain RefinementVector deltas.

Each entry maps a normalized adjective (lowercase, underscores) to a RefinementVector
dict. All delta fields use signed proportional values -- never absolute targets.
None fields indicate the adjective does not affect that dimension.

Language: English-only. All adjective keys are English. Non-English
refinement terms will not match any entry.
"""

from typing import Optional, TypedDict


class HarmonicDelta(TypedDict):
    register_shift_semitones: Optional[int]  # positive=up, negative=down
    mode_bias: Optional[str]                  # "minor" | "major" | None
    density_delta: Optional[int]              # +1 denser, -1 sparser


class TimbralDelta(TypedDict):
    filter_cutoff_delta_pct: Optional[float]  # percent of current cutoff
    brightness_db: Optional[float]            # EQ high shelf dB adjustment
    reverb_wet_delta: Optional[float]         # 0.0-1.0 normalized delta


class DynamicDelta(TypedDict):
    velocity_shift: Optional[int]             # +/- MIDI velocity
    compression_ratio_delta: Optional[float]  # normalized compressor ratio delta


class RefinementVector(TypedDict):
    harmonic: Optional[HarmonicDelta]
    timbral: Optional[TimbralDelta]
    dynamic: Optional[DynamicDelta]


REFINEMENT_LEXICON: dict[str, RefinementVector] = {
    "darker": {
        "harmonic": {"register_shift_semitones": -3, "mode_bias": "minor", "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": -25.0, "brightness_db": -2.0, "reverb_wet_delta": 0.05},
        "dynamic": {"velocity_shift": -8, "compression_ratio_delta": 0.05},
    },
    "brighter": {
        "harmonic": {"register_shift_semitones": 3, "mode_bias": "major", "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": 25.0, "brightness_db": 2.0, "reverb_wet_delta": -0.05},
        "dynamic": {"velocity_shift": 5, "compression_ratio_delta": -0.03},
    },
    "warmer": {
        "harmonic": {"register_shift_semitones": -1, "mode_bias": None, "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": -15.0, "brightness_db": -1.0, "reverb_wet_delta": 0.03},
        "dynamic": {"velocity_shift": 0, "compression_ratio_delta": 0.02},
    },
    "colder": {
        "harmonic": {"register_shift_semitones": 1, "mode_bias": None, "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": 10.0, "brightness_db": 1.5, "reverb_wet_delta": -0.03},
        "dynamic": {"velocity_shift": -3, "compression_ratio_delta": -0.02},
    },
    "harder": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": 1},
        "timbral": {"filter_cutoff_delta_pct": 20.0, "brightness_db": 1.0, "reverb_wet_delta": -0.08},
        "dynamic": {"velocity_shift": 15, "compression_ratio_delta": 0.08},
    },
    "softer": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": -1},
        "timbral": {"filter_cutoff_delta_pct": -20.0, "brightness_db": -1.0, "reverb_wet_delta": 0.08},
        "dynamic": {"velocity_shift": -15, "compression_ratio_delta": -0.08},
    },
    "heavier": {
        "harmonic": {"register_shift_semitones": -2, "mode_bias": "minor", "density_delta": 1},
        "timbral": {"filter_cutoff_delta_pct": -10.0, "brightness_db": -1.5, "reverb_wet_delta": 0.04},
        "dynamic": {"velocity_shift": 10, "compression_ratio_delta": 0.06},
    },
    "lighter": {
        "harmonic": {"register_shift_semitones": 2, "mode_bias": "major", "density_delta": -1},
        "timbral": {"filter_cutoff_delta_pct": 10.0, "brightness_db": 1.5, "reverb_wet_delta": -0.04},
        "dynamic": {"velocity_shift": -10, "compression_ratio_delta": -0.06},
    },
    "sparser": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": -2},
        "timbral": None,
        "dynamic": {"velocity_shift": -5, "compression_ratio_delta": None},
    },
    "denser": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": 2},
        "timbral": None,
        "dynamic": {"velocity_shift": 5, "compression_ratio_delta": None},
    },
    "higher": {
        "harmonic": {"register_shift_semitones": 5, "mode_bias": None, "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": 15.0, "brightness_db": None, "reverb_wet_delta": None},
        "dynamic": None,
    },
    "lower": {
        "harmonic": {"register_shift_semitones": -5, "mode_bias": None, "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": -15.0, "brightness_db": None, "reverb_wet_delta": None},
        "dynamic": None,
    },
    "more_energetic": {
        "harmonic": {"register_shift_semitones": 1, "mode_bias": "major", "density_delta": 1},
        "timbral": {"filter_cutoff_delta_pct": 15.0, "brightness_db": 1.0, "reverb_wet_delta": -0.05},
        "dynamic": {"velocity_shift": 12, "compression_ratio_delta": 0.04},
    },
    "less_energetic": {
        "harmonic": {"register_shift_semitones": -1, "mode_bias": "minor", "density_delta": -1},
        "timbral": {"filter_cutoff_delta_pct": -15.0, "brightness_db": -1.0, "reverb_wet_delta": 0.05},
        "dynamic": {"velocity_shift": -12, "compression_ratio_delta": -0.04},
    },
    "more_melodic": {
        "harmonic": {"register_shift_semitones": 2, "mode_bias": None, "density_delta": 1},
        "timbral": {"filter_cutoff_delta_pct": 5.0, "brightness_db": 0.5, "reverb_wet_delta": 0.05},
        "dynamic": {"velocity_shift": -5, "compression_ratio_delta": None},
    },
    "more_rhythmic": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": 2},
        "timbral": None,
        "dynamic": {"velocity_shift": 8, "compression_ratio_delta": 0.03},
    },
    "more_spacious": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": -1},
        "timbral": {"filter_cutoff_delta_pct": -5.0, "brightness_db": -0.5, "reverb_wet_delta": 0.15},
        "dynamic": {"velocity_shift": -3, "compression_ratio_delta": None},
    },
    "tighter": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": 5.0, "brightness_db": 0.5, "reverb_wet_delta": -0.1},
        "dynamic": {"velocity_shift": 3, "compression_ratio_delta": 0.05},
    },
    "dirtier": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": -10.0, "brightness_db": 1.5, "reverb_wet_delta": 0.0},
        "dynamic": {"velocity_shift": 5, "compression_ratio_delta": 0.04},
    },
    "cleaner": {
        "harmonic": {"register_shift_semitones": 0, "mode_bias": None, "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": 10.0, "brightness_db": -1.0, "reverb_wet_delta": -0.05},
        "dynamic": {"velocity_shift": -3, "compression_ratio_delta": -0.04},
    },
    # Multi-word aliases
    "more_dark": {
        "harmonic": {"register_shift_semitones": -3, "mode_bias": "minor", "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": -25.0, "brightness_db": -2.0, "reverb_wet_delta": 0.05},
        "dynamic": {"velocity_shift": -8, "compression_ratio_delta": 0.05},
    },
    "more_bright": {
        "harmonic": {"register_shift_semitones": 3, "mode_bias": "major", "density_delta": 0},
        "timbral": {"filter_cutoff_delta_pct": 25.0, "brightness_db": 2.0, "reverb_wet_delta": -0.05},
        "dynamic": {"velocity_shift": 5, "compression_ratio_delta": -0.03},
    },
}
