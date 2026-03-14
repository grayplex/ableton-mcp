"""Shared mixer helper functions.

These live in a separate module to avoid circular imports between
mixer.py (imports _resolve_track from tracks.py) and tracks.py
(imports _to_db/_pan_label for get_track_info enrichment).
"""

# Calibrated against Ableton Live's fader curve: (parameter_value, dB)
_VOL_CURVE = [
    (0.0, None),
    (0.1, -48.6),
    (0.225, -31.5),
    (0.35, -20.6),
    (0.475, -15.0),
    (0.6, -10.0),
    (0.725, -5.0),
    (0.85, 0.0),
    (0.975, 5.0),
    (1.0, 6.0),
]


def _to_db(value):
    """Convert normalized 0.0-1.0 volume to dB string.

    Uses a lookup table calibrated against Ableton Live's fader curve
    with linear interpolation between points.
    """
    if value <= 0:
        return "-inf dB"
    for i in range(1, len(_VOL_CURVE)):
        if value <= _VOL_CURVE[i][0]:
            v0, db0 = _VOL_CURVE[i - 1]
            v1, db1 = _VOL_CURVE[i]
            if db0 is None:
                # Below lowest calibration point — extrapolate from next segment
                slope = (_VOL_CURVE[2][1] - db1) / (_VOL_CURVE[2][0] - v1)
                return f"{db1 + slope * (value - v1):.1f} dB"
            t = (value - v0) / (v1 - v0)
            return f"{db0 + t * (db1 - db0):.1f} dB"
    return f"{_VOL_CURVE[-1][1]:.1f} dB"


def _pan_label(value):
    """Convert pan value to human-readable label."""
    if value == 0.0:
        return "center"
    pct = int(abs(value) * 100)
    if value < 0:
        return f"{pct}% left"
    return f"{pct}% right"
