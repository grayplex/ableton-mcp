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
