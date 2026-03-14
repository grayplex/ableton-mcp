"""Shared mixer helper functions.

These live in a separate module to avoid circular imports between
mixer.py (imports _resolve_track from tracks.py) and tracks.py
(imports _to_db/_pan_label for get_track_info enrichment).
"""

import math


def _to_db(value):
    """Convert normalized 0.0-1.0 volume to dB approximation string.

    Ableton's volume is linear in dB: 0.85 = 0 dB, 1.0 = +6 dB.
    """
    if value <= 0:
        return "-inf dB"
    return f"{40 * value - 34:.1f} dB"


def _pan_label(value):
    """Convert pan value to human-readable label."""
    if value == 0.0:
        return "center"
    pct = int(abs(value) * 100)
    if value < 0:
        return f"{pct}% left"
    return f"{pct}% right"
