"""Shared mixer helper functions.

These live in a separate module to avoid circular imports between
mixer.py (imports _resolve_track from tracks.py) and tracks.py
(imports _to_db/_pan_label for get_track_info enrichment).
"""

import math

# Lower-range coefficients (log + quadratic, constrained to f(0.4) = -18)
_A = 1.1141800562
_B = -182.5062752046
_C = 187.6312710131
_D = -62.8305915134


def _to_db(value):
    """Convert normalized 0.0-1.0 volume to dB string.

    Two-piece formula fitted to 77 calibration points from Ableton Live.
    Upper range (v >= 0.4): linear, dB = 40v - 34 (exact).
    Lower range (v < 0.4): log + quadratic taper.
    RMS 0.13 dB, max 0.35 dB across all calibration points.
    """
    if value <= 0:
        return "-inf dB"
    if value >= 0.4:
        db = 40.0 * value - 34.0
    else:
        db = _A * math.log(value) + _B * value * value + _C * value + _D
    return f"{db:.1f} dB"


def _pan_label(value):
    """Convert pan value to human-readable label."""
    if value == 0.0:
        return "center"
    pct = int(abs(value) * 100)
    if value < 0:
        return f"{pct}% left"
    return f"{pct}% right"
