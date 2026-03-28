"""Scaffold tools: write production plans into Ableton Arrangement view.

Pure helper functions (_deduplicate_roles, _bar_to_beat) are used by the
scaffold_arrangement MCP tool to convert plan data into Ableton commands.
"""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


def _deduplicate_roles(sections: list[dict]) -> list[str]:
    """Flatten section roles into unique track names with dedup suffixes.

    Each unique role gets one track. If a role appears in multiple sections,
    additional occurrences get numbered suffixes: "lead", "lead 2", "lead 3".

    Track names are ordered by first appearance across sections.

    Args:
        sections: List of section dicts, each with a "roles" list.

    Returns:
        List of deduplicated track name strings.
    """
    role_counts: dict[str, int] = {}
    for section in sections:
        section_seen: set[str] = set()
        for role in section.get("roles", []):
            if role not in section_seen:
                section_seen.add(role)
                role_counts[role] = role_counts.get(role, 0) + 1

    # Build output: for each role, emit base name + numbered variants
    # Preserve first-seen order from sections
    seen_roles: list[str] = []
    for section in sections:
        for role in section.get("roles", []):
            if role not in seen_roles:
                seen_roles.append(role)

    result: list[str] = []
    for role in seen_roles:
        count = role_counts.get(role, 0)
        if count <= 0:
            continue
        result.append(role)
        for i in range(2, count + 1):
            result.append(f"{role} {i}")

    return result


def _beat_to_bar(beat_position: float, beats_per_bar: float) -> int:
    """Convert a 0-indexed beat position to a 1-indexed bar number.

    Uses floor division so fractional positions map to the bar they fall within.

    Args:
        beat_position: Beat position (0-indexed, from Ableton cue point time).
        beats_per_bar: Number of beats per bar, derived from time signature
                       as numerator * (4 / denominator).

    Returns:
        1-indexed bar number.
    """
    import math
    return math.floor(beat_position / beats_per_bar) + 1


def _bar_to_beat(bar_start: int, beats_per_bar: float) -> float:
    """Convert a 1-based bar number to a 0-based beat position.

    Args:
        bar_start: 1-based bar number (bar 1 = beat 0).
        beats_per_bar: Number of beats per bar, derived from time signature
                       as numerator * (4 / denominator).

    Returns:
        Beat position as float.
    """
    return (bar_start - 1) * beats_per_bar


@mcp.tool()
def scaffold_arrangement(ctx: Context, plan: dict) -> str:
    """Write a production plan into Ableton as locators and MIDI tracks.

    Accepts the JSON output of generate_production_plan. Creates one locator
    per section at the correct beat position and one MIDI track per unique
    role occurrence. Reads the session time signature from Ableton.

    Args:
        plan: Production plan dict with "sections" array. Each section must
              have "name", "bar_start", "bars", and "roles" keys.
    """
    try:
        sections = plan.get("sections")
        if not sections:
            return format_error(
                "Plan must contain a 'sections' array",
                suggestion="Pass the output of generate_production_plan",
            )

        ableton = get_ableton_connection()

        # 1. Get session time signature
        session = ableton.send_command("get_session_info")
        numerator = session["signature_numerator"]
        denominator = session["signature_denominator"]
        beats_per_bar = numerator * (4.0 / denominator)

        # 2. Create locators for each section
        locators_created = []
        locator_errors = []
        for section in sections:
            beat_pos = _bar_to_beat(section["bar_start"], beats_per_bar)
            try:
                result = ableton.send_command(
                    "create_locator_at",
                    {
                        "beat_position": beat_pos,
                        "name": section["name"],
                    },
                )
                locators_created.append(result)
            except Exception as e:
                locator_errors.append(
                    {"section": section["name"], "error": str(e)}
                )

        # 3. Deduplicate roles and create tracks
        track_names = _deduplicate_roles(sections)
        tracks_result = ableton.send_command(
            "scaffold_tracks",
            {"track_names": track_names},
        )

        response = {
            "locators_created": len(locators_created),
            "tracks_created": tracks_result["count"],
            "track_names": track_names,
        }
        if locator_errors:
            response["locator_errors"] = locator_errors
        return json.dumps(response)
    except Exception as e:
        return format_error(
            "Failed to scaffold arrangement",
            detail=str(e),
            suggestion="Verify Ableton connection with get_connection_status",
        )


@mcp.tool()
def get_arrangement_overview(ctx: Context) -> str:
    """Get arrangement state: locators, tracks, session length in bars.

    Returns locators with 1-indexed bar positions, flat track name list,
    and session length in bars for mid-session re-orientation.
    """
    try:
        ableton = get_ableton_connection()
        state = ableton.send_command("get_arrangement_state")

        numerator = state["signature_numerator"]
        denominator = state["signature_denominator"]
        beats_per_bar = numerator * (4.0 / denominator)

        locators = []
        for cp in state["cue_points"]:
            locators.append({
                "name": cp["name"],
                "bar": _beat_to_bar(cp["time"], beats_per_bar),
            })

        # D-15: session_length_bars is song_length / beats_per_bar (length, not position)
        # Use int() division, NOT _beat_to_bar (which adds +1 for position-to-bar)
        session_length_bars = int(state["song_length"] / beats_per_bar)

        return json.dumps({
            "locators": locators,
            "tracks": [t["name"] for t in state["tracks"]],
            "session_length_bars": session_length_bars,
        })
    except Exception as e:
        return format_error(
            "Failed to get arrangement overview",
            detail=str(e),
            suggestion="Verify Ableton connection with get_connection_status",
        )
