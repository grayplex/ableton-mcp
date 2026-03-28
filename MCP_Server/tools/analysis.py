"""Analysis MCP tools: session mix state snapshot and gain staging check."""

import json
import math

from mcp.server.fastmcp import Context

from MCP_Server.connection import get_ableton_connection
from MCP_Server.devices.catalog import ROLES
from MCP_Server.devices.gain_targets import GAIN_TARGETS
from MCP_Server.server import mcp


def _meter_to_db(value: float) -> float | None:
    """Convert normalized 0.0-1.0 peak meter reading to dBFS.

    Uses standard linear amplitude formula: 20 * log10(value).
    Do NOT use _to_db() from mixer_helpers — that function is calibrated
    for Ableton's non-linear volume fader curve, not peak meter levels.

    Returns None for zero or negative values (silence / -inf dBFS).
    The caller treats None as status "no_signal".
    """
    if value <= 0.0:
        return None
    return 20.0 * math.log10(value)


def _infer_role(track_name: str) -> str | None:
    """Infer mixing role from track name via case-insensitive substring match.

    Iterates ROLES in order; first match wins (D-05).
    Examples: "KICK_01" -> "kick", "bass_synth" -> "bass".
    "pad_atmo" matches "pad" (index 3) before "atmospheric" (index 6).

    Returns None when no ROLES entry appears in the track name.
    Tracks with None role are included in output with status "unknown" (D-06).
    """
    name_lower = track_name.lower()
    for role in ROLES:
        if role in name_lower:
            return role
    return None


@mcp.tool()
def get_mix_state(ctx: Context) -> str:
    """Get current device parameters for every device on every track.

    Returns a complete snapshot of the session's device parameter state
    in a single call — no N sequential reads required (STATE-01).

    Includes all tracks (regular, return, master). Tracks with no devices
    return an empty devices list. Does not include mixer state (volume,
    pan, sends) — use get_track_info/get_volume for those.

    Returns JSON with structure:
    {
      "tracks": [{"index", "name", "type", "devices": [{"index",
        "class_name", "device_name", "parameters": [{"name", "value"}]}]}],
      "return_tracks": [...],
      "master_track": {...}
    }
    """
    conn = get_ableton_connection()
    result = conn.send_command("get_mix_state", {})
    return json.dumps(result, indent=2)


@mcp.tool()
def check_gain_staging(ctx: Context) -> str:
    """Check gain staging for all tracks: dBFS estimates vs role-based targets.

    Reads live output meter levels and compares to role-based dBFS target
    ranges. Roles are inferred from track names via substring match (GAIN-01).

    MIDI tracks with no instrument loaded are excluded from analysis (GAIN-02).
    Tracks whose names don't match any role are included with role=null and
    status="unknown" — no false-positive flags (D-06).

    Run with the session playing and Mixer view open for accurate readings.
    All-zero meters indicate the session is not playing (see warning field).

    Returns JSON with structure:
    {
      "tracks": [
        {
          "index": int,
          "name": str,
          "role": str | null,
          "meter_db": float | null,
          "target_range": [low, high] | null,
          "status": "ok" | "too_hot" | "too_quiet" | "no_signal" | "unknown"
        }
      ],
      "warning": str   (only present when all meters are 0.0)
    }
    """
    conn = get_ableton_connection()
    raw = conn.send_command("get_track_meters", {})

    # Flatten all track groups for processing
    all_tracks = []
    for t in raw.get("tracks", []):
        all_tracks.append(t)
    for t in raw.get("return_tracks", []):
        all_tracks.append(t)
    master = raw.get("master_track")
    if master:
        all_tracks.append(master)

    # D-04: detect all-zero condition before building per-track output
    all_zero = all(t["meter_level"] == 0.0 for t in all_tracks) if all_tracks else True

    output_tracks = []
    for t in all_tracks:
        role = _infer_role(t["name"])
        meter_db = _meter_to_db(t["meter_level"])

        # Round to 1 decimal for comparison — avoids floating-point boundary issues
        # (e.g. 0.316 → -10.009 rounds to -10.0, which is within kick target -10.0..-4.0)
        meter_db_rounded = round(meter_db, 1) if meter_db is not None else None

        if meter_db is None:
            status = "no_signal"
            target_range = GAIN_TARGETS.get(role) if role else None
        elif role is None:
            status = "unknown"
            target_range = None
        else:
            lo, hi = GAIN_TARGETS[role]
            target_range = (lo, hi)
            if meter_db_rounded < lo:
                status = "too_quiet"
            elif meter_db_rounded > hi:
                status = "too_hot"
            else:
                status = "ok"

        entry = {
            "index": t.get("index"),
            "name": t["name"],
            "role": role,
            "meter_db": meter_db_rounded,
            "target_range": list(target_range) if target_range else None,
            "status": status,
        }
        output_tracks.append(entry)

    response: dict = {"tracks": output_tracks}
    if all_zero:
        response["warning"] = (
            "All meters are 0 — play the session to get live meter readings"
        )

    return json.dumps(response, indent=2)
