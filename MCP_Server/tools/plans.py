"""Production plan builder tools: generate full-track and single-section plans.

These are pure computation tools — no Ableton socket calls. They transform
genre blueprint arrangement data into flat, token-efficient production plans
with cumulative bar positions starting at bar 1.

Per PLAN-01: generate_production_plan returns all sections with bar positions.
Per PLAN-02: generate_section_plan returns a single section's plan entry.
"""

import copy
import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.genres import get_blueprint


def _build_plan_sections(
    sections: list,
    section_bar_overrides: dict | None = None,
    add_sections: list | None = None,
    remove_sections: list | None = None,
) -> tuple:
    """Build output section list with optional overrides and cumulative bar_start values.

    Override application order (D-09):
      1. Remove sections by name
      2. Insert new sections after specified anchor
      3. Resize sections via bar count overrides
      4. Calculate cumulative bar_start positions

    Args:
        sections: List of ArrangementEntry dicts from a genre blueprint.
                  Must be a deep copy (call copy.deepcopy before passing).
        section_bar_overrides: Optional dict of section_name -> new bar count.
        add_sections: Optional list of dicts with keys: name, bars, after (anchor name).
        remove_sections: Optional list of section names to drop.

    Returns:
        Tuple of (plan_sections, warnings) where plan_sections is a list of dicts
        with keys: name, bar_start, bars, roles, and optionally transition_in.
        warnings is a list of warning strings for nonexistent references.

    Raises:
        ValueError: When add_sections contains a name that duplicates an existing section.
    """
    warnings = []

    # Step 1: Remove sections by name
    if remove_sections:
        existing_names = {s["name"] for s in sections}
        for name in remove_sections:
            if name not in existing_names:
                warnings.append(
                    f"remove_sections: '{name}' not found in blueprint"
                )
        remove_set = set(remove_sections)
        sections = [s for s in sections if s["name"] not in remove_set]

    # Step 2: Add sections after named anchor
    if add_sections:
        for entry in add_sections:
            new_name = entry["name"]
            anchor = entry["after"]
            # Check for duplicate name
            existing_names = {s["name"] for s in sections}
            if new_name in existing_names:
                raise ValueError(
                    f"Duplicate section name: '{new_name}' already exists in arrangement"
                )
            # Find anchor index
            anchor_idx = next(
                (i for i, s in enumerate(sections) if s["name"] == anchor),
                None,
            )
            if anchor_idx is None:
                warnings.append(
                    f"add_sections: anchor '{anchor}' not found, skipping '{new_name}'"
                )
                continue
            new_section = {
                "name": new_name,
                "bars": entry["bars"],
                "energy": 5,
                "roles": [],
                # No transition_in for custom sections (no blueprint data)
            }
            sections.insert(anchor_idx + 1, new_section)

    # Step 3: Resize sections via bar count overrides
    if section_bar_overrides:
        existing_names = {s["name"] for s in sections}
        for name, bar_count in section_bar_overrides.items():
            if name not in existing_names:
                warnings.append(
                    f"section_bar_overrides: '{name}' not found in blueprint"
                )
                continue
            for s in sections:
                if s["name"] == name:
                    s["bars"] = bar_count
                    break

    # Step 4: Build output entries with cumulative bar_start positions
    result = []
    bar = 1
    for s in sections:
        entry = {
            "name": s["name"],
            "bar_start": bar,
            "bars": s["bars"],
            "roles": s.get("roles", []),
        }
        # Only include transition_in when present in source (intro never has one,
        # custom added sections never have one either)
        if "transition_in" in s:
            entry["transition_in"] = s["transition_in"]
        result.append(entry)
        bar += s["bars"]

    return result, warnings


@mcp.tool()
def generate_production_plan(
    ctx: Context,
    genre: str,
    key: str,
    bpm: int,
    vibe: str | None = None,
    time_signature: str | None = None,
    section_bar_overrides: dict | None = None,
    add_sections: list | None = None,
    remove_sections: list | None = None,
) -> str:
    """Generate a full production plan from genre conventions. Returns all sections with bar positions and per-section instrument checklists.

    Parameters:
    - genre: Genre ID or alias (e.g., "house", "techno", "deep house")
    - key: Musical key root (e.g., "Am", "C", "F#")
    - bpm: Tempo in beats per minute
    - vibe: Optional mood/vibe description echoed verbatim into the plan
    - time_signature: Time signature string (default "4/4")
    - section_bar_overrides: (Plan 02) Dict of section_name -> bar count overrides
    - add_sections: (Plan 02) List of section dicts to append to arrangement
    - remove_sections: (Plan 02) List of section names to remove from arrangement
    """
    try:
        blueprint = get_blueprint(genre)
        if blueprint is None:
            return format_error(
                "Genre not found",
                detail=f"'{genre}' is not a registered genre or alias",
                suggestion="Use list_genre_blueprints to see available genres",
            )

        # Deep copy prevents blueprint registry mutation across repeated calls
        sections = copy.deepcopy(blueprint["arrangement"]["sections"])

        try:
            plan_sections, warnings = _build_plan_sections(
                sections,
                section_bar_overrides=section_bar_overrides,
                add_sections=add_sections,
                remove_sections=remove_sections,
            )
        except ValueError as e:
            return format_error(
                "Duplicate section name",
                detail=str(e),
                suggestion="Use a unique name for added sections",
            )

        result = {
            "genre": blueprint["id"],
            "key": key,
            "bpm": bpm,
            "time_signature": time_signature or "4/4",
            "sections": plan_sections,
        }

        # Vibe is conditional: include only when caller provides it
        if vibe is not None:
            result["vibe"] = vibe

        # Warnings are conditional: include only when overrides referenced nonexistent sections
        if warnings:
            result["warnings"] = warnings

        return json.dumps(result)
    except Exception as e:
        return format_error(
            "Failed to generate production plan",
            detail=str(e),
            suggestion="Check genre is valid using list_genre_blueprints",
        )


@mcp.tool()
def generate_section_plan(
    ctx: Context,
    genre: str,
    key: str,
    bpm: int,
    section_name: str,
    time_signature: str | None = None,
) -> str:
    """Generate a targeted plan for a single arrangement section. Returns one section's bar position, roles, and transition without planning the full track.

    Parameters:
    - genre: Genre ID or alias (e.g., "house", "techno", "deep house")
    - key: Musical key root (e.g., "Am", "C", "F#")
    - bpm: Tempo in beats per minute
    - section_name: Name of the section to retrieve (e.g., "intro", "drop", "breakdown")
    - time_signature: Time signature string (default "4/4")
    """
    try:
        blueprint = get_blueprint(genre)
        if blueprint is None:
            return format_error(
                "Genre not found",
                detail=f"'{genre}' is not a registered genre or alias",
                suggestion="Use list_genre_blueprints to see available genres",
            )

        sections = blueprint["arrangement"]["sections"]

        # Iterate sections tracking cumulative bar position
        bar = 1
        found_section = None
        available_names = []
        for s in sections:
            available_names.append(s["name"])
            if s["name"] == section_name:
                found_section = s
                break
            bar += s["bars"]

        if found_section is None:
            available = ", ".join(available_names)
            return format_error(
                "Section not found",
                detail=f"'{section_name}' not in {genre} arrangement",
                suggestion=f"Available sections: {available}",
            )

        section_entry = {
            "name": found_section["name"],
            "bar_start": bar,
            "bars": found_section["bars"],
            "roles": found_section.get("roles", []),
        }
        # Include transition_in only when present in source section
        if "transition_in" in found_section:
            section_entry["transition_in"] = found_section["transition_in"]

        result = {
            "genre": blueprint["id"],
            "key": key,
            "bpm": bpm,
            "time_signature": time_signature or "4/4",
            "section": section_entry,
        }

        return json.dumps(result)
    except Exception as e:
        return format_error(
            "Failed to generate section plan",
            detail=str(e),
            suggestion="Check genre and section_name are valid",
        )
