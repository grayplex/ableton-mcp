"""Execution tools: section checklists and arrangement progress checking.

Read-only tools that combine production plan data with live Ableton track
state to support methodical section-by-section production workflow.
"""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp
from MCP_Server.tools.scaffold import _deduplicate_roles


def _map_section_roles_to_tracks(plan_sections: list[dict], section_name: str) -> list[dict]:
    """Map a section's roles to their Ableton track names using dedup logic.

    Uses the same counting algorithm as _deduplicate_roles: each role is counted
    once per section it appears in, and the N-th section containing that role
    maps to "role N" (or bare "role" for N=1).

    Args:
        plan_sections: Full sections array from a production plan.
        section_name: Name of the target section.

    Returns:
        List of {"role": str, "track_name": str} dicts. Empty if section not found.
    """
    target = None
    for s in plan_sections:
        if s["name"] == section_name:
            target = s
            break
    if target is None:
        return []

    result = []
    seen_in_target: set[str] = set()
    for role in target.get("roles", []):
        if role in seen_in_target:
            continue  # Defensive dedup within section
        seen_in_target.add(role)

        # Count which occurrence this section is for this role
        occurrence = 0
        for s in plan_sections:
            section_roles_unique: set[str] = set()
            for r in s.get("roles", []):
                if r not in section_roles_unique:
                    section_roles_unique.add(r)
                    if r == role:
                        occurrence += 1
            if s["name"] == section_name:
                break

        track_name = role if occurrence <= 1 else f"{role} {occurrence}"
        result.append({"role": role, "track_name": track_name})

    return result


@mcp.tool()
def get_section_checklist(ctx: Context, plan: dict, section_name: str) -> str:
    """Get execution checklist for a named section: pending instrument roles.

    Accepts the JSON output of generate_production_plan plus a section name.
    For each role in the section, checks whether the corresponding Ableton
    track has an instrument loaded.

    Args:
        plan: Production plan dict with "sections" array.
        section_name: Name of the section to check (e.g. "intro", "drop").
    """
    try:
        sections = plan.get("sections")
        if not sections:
            return format_error(
                "Plan must contain a 'sections' array",
                suggestion="Pass the output of generate_production_plan",
            )

        # Validate section exists
        section_names = [s["name"] for s in sections]
        if section_name not in section_names:
            return format_error(
                f"Section '{section_name}' not found in plan",
                suggestion=f"Available sections: {', '.join(section_names)}",
            )

        # Map roles to track names
        role_tracks = _map_section_roles_to_tracks(sections, section_name)

        # Get live track state from Ableton
        ableton = get_ableton_connection()
        state = ableton.send_command("get_arrangement_state")
        track_map = {t["name"]: t["has_devices"] for t in state["tracks"]}

        # Build role status list
        roles = []
        pending_count = 0
        for rt in role_tracks:
            track_name = rt["track_name"]
            if track_name not in track_map:
                status = "not_found"
                pending_count += 1
            elif track_map[track_name]:
                status = "done"
            else:
                status = "pending"
                pending_count += 1
            roles.append({
                "role": rt["role"],
                "track_name": track_name,
                "status": status,
            })

        return json.dumps({
            "section": section_name,
            "roles": roles,
            "pending_count": pending_count,
            "total_count": len(roles),
        })
    except Exception as e:
        return format_error(
            "Failed to get section checklist",
            detail=str(e),
            suggestion="Verify Ableton connection with get_connection_status",
        )


@mcp.tool()
def get_arrangement_progress(ctx: Context) -> str:
    """Check arrangement progress: find scaffolded tracks with no instrument loaded.

    Reads all MIDI tracks from Ableton and returns which have no device loaded,
    flagging tracks that will produce silence if left empty.
    """
    try:
        ableton = get_ableton_connection()
        state = ableton.send_command("get_arrangement_state")

        tracks = state["tracks"]
        empty_tracks = [t["name"] for t in tracks if not t["has_devices"]]

        return json.dumps({
            "empty_tracks": empty_tracks,
            "total_tracks": len(tracks),
            "empty_count": len(empty_tracks),
        })
    except Exception as e:
        return format_error(
            "Failed to check arrangement progress",
            detail=str(e),
            suggestion="Verify Ableton connection with get_connection_status",
        )
