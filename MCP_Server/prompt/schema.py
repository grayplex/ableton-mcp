"""Prompt interpretation schema: SignalSet and ProductionBrief TypedDicts.

All types are TypedDicts for JSON-serializable construction without .asdict().

SignalSet: Raw classified signals extracted from a free-text prompt.
ProductionBrief: Fully derived production parameters from a prompt.
"""

from typing import Optional, TypedDict


class SignalSet(TypedDict):
    """Raw signals classified from a free-text prompt. No derivation — just extraction."""
    genre_signals: list        # list of genre blueprint IDs matched
    mood_signals: list         # list of {term, energy_level, scale_bias} dicts
    instrument_signals: list   # list of {term, role, descriptor} dicts
    effect_signals: list       # list of effect descriptor strings
    tempo_signals: list        # list of {term, bpm_modifier} dicts
    structural_hints: list     # list of non-semantic structural terms
    raw_descriptors: list      # unrecognized tokens passed through unchanged
    confidence: float          # 0.0–1.0 parse confidence


class ProductionBrief(TypedDict):
    """Fully derived production parameters from a natural-language music prompt."""
    raw_prompt: str
    primary_genre: Optional[str]     # genre blueprint id or None when unresolved
    tempo_range: dict                # {"min_bpm": int, "max_bpm": int}
    key_feel: dict                   # {"scale": str, "mode": str}  mode: "major"|"minor"
    groove_feel: dict                # {"pattern_type": str, "swing_pct": int}
    energy_level: int                # 1–10
    instrument_hints: list           # list of {"role": str, "descriptor": str}
    effect_hints: list               # list of effect descriptor strings
    velocity_style: str              # "laid_back" | "medium" | "driving"
    confidence: float                # 0.0–1.0
    reasoning: list                  # list of plain-English derivation notes
