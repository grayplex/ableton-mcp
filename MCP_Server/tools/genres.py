"""Genre blueprint tools: discovery and retrieval of genre conventions."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.genres import get_blueprint, list_genres

# Metadata keys always included in filtered results
META_KEYS = {"id", "name", "bpm_range"}

# Valid section names (from schema _SECTION_SPEC)
SECTION_KEYS = {
    "instrumentation", "harmony", "rhythm",
    "arrangement", "mixing", "production_tips",
}


@mcp.tool()
def list_genre_blueprints(ctx: Context) -> str:
    """List all available genre blueprints. Returns genre ID, display name, BPM range, and available subgenres for each registered genre."""
    try:
        return json.dumps(list_genres())
    except Exception as e:
        return format_error(
            "Failed to list genre blueprints",
            detail=str(e),
            suggestion="This tool takes no parameters",
        )


@mcp.tool()
def get_genre_blueprint(
    ctx: Context,
    genre: str,
    subgenre: str | None = None,
    sections: list[str] | None = None,
) -> str:
    """Get a genre blueprint with full instrumentation, harmony, rhythm, arrangement, mixing, and production tips. Supports subgenres and section filtering.

    Parameters:
    - genre: Genre name or alias (e.g., "house", "deep house", "tech_house")
    - subgenre: Optional subgenre ID (e.g., "deep_house"). If genre is itself a subgenre alias, this is auto-resolved
    - sections: Optional list of sections to return (e.g., ["harmony", "rhythm"]). Valid: instrumentation, harmony, rhythm, arrangement, mixing, production_tips
    """
    try:
        blueprint = get_blueprint(genre, subgenre)
        if blueprint is None:
            return format_error(
                "Genre not found",
                detail=f"'{genre}' is not a registered genre or alias",
                suggestion="Use list_genre_blueprints to see available genres",
            )

        if sections is not None:
            valid_sections = [s for s in sections if s in SECTION_KEYS]
            if not valid_sections:
                return format_error(
                    "No valid sections requested",
                    detail=f"Requested: {sections}",
                    suggestion=f"Valid sections: {', '.join(sorted(SECTION_KEYS))}",
                )
            filtered = {
                k: v for k, v in blueprint.items()
                if k in META_KEYS or k in valid_sections
            }
            return json.dumps(filtered)

        return json.dumps(blueprint)
    except Exception as e:
        return format_error(
            "Failed to get genre blueprint",
            detail=str(e),
            suggestion="Use list_genre_blueprints to see available genres",
        )
