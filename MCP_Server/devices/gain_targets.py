"""Role-based gain staging target ranges for check_gain_staging (GAIN-01).

Each entry maps a mixing role to a (low_dBFS, high_dBFS) tuple.
Tracks below low_dBFS are flagged "too_quiet".
Tracks above high_dBFS are flagged "too_hot".
Tracks within the range are "ok".

Roles match the ROLES list in MCP_Server/devices/catalog.py.
"""

GAIN_TARGETS: dict[str, tuple[float, float]] = {
    "kick": (-10.0, -4.0),
    "bass": (-14.0, -8.0),
    "lead": (-14.0, -8.0),
    "pad": (-18.0, -12.0),
    "chords": (-16.0, -10.0),
    "vocal": (-14.0, -6.0),
    "atmospheric": (-20.0, -12.0),
    "return": (-18.0, -6.0),
    "master": (-6.0, -1.0),
}
