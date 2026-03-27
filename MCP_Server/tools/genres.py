"""Genre blueprint tools: discovery and retrieval of genre conventions."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.genres import get_blueprint, list_genres
from MCP_Server.theory.chords import _QUALITY_MAP
from MCP_Server.theory.scales import SCALE_CATALOG
from MCP_Server.theory.progressions import generate_progression

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


@mcp.tool()
def get_genre_palette(ctx: Context, genre: str, key: str) -> str:
    """Get key-resolved harmonic palette for a genre. Returns chord names, scale names, and common progressions resolved in the given key using the theory engine.

    Parameters:
    - genre: Genre name or alias (e.g., "house", "techno", "deep house")
    - key: Musical key root (e.g., "C", "F#", "Bb")
    """
    try:
        blueprint = get_blueprint(genre)
        if blueprint is None:
            return format_error(
                "Genre not found",
                detail=f"'{genre}' is not a registered genre or alias",
                suggestion="Use list_genre_blueprints to see available genres",
            )

        harmony = blueprint["harmony"]
        unresolved = []

        # Resolve scales
        resolved_scales = []
        for scale_name in harmony["scales"]:
            if scale_name in SCALE_CATALOG:
                resolved_scales.append(f"{key} {scale_name}")
            else:
                unresolved.append({"type": "scale", "name": scale_name})

        # Resolve chord_types
        resolved_chords = []
        for quality in harmony["chord_types"]:
            if quality in _QUALITY_MAP:
                resolved_chords.append(f"{key}{quality}")
            else:
                unresolved.append({"type": "chord_type", "name": quality})

        # Quality full-word to short-form mapping for chord name display
        _quality_short = {
            "major": "maj", "minor": "min", "diminished": "dim",
            "augmented": "aug",
        }

        # Resolve progressions
        resolved_progressions = []
        for numeral_list in harmony["common_progressions"]:
            # Determine scale_type: strip leading b/# and check case
            stripped = numeral_list[0].lstrip("b#")
            scale_type = "natural_minor" if stripped[0].islower() else "major"
            try:
                prog_result = generate_progression(
                    key, numeral_list, scale_type=scale_type,
                )
                chord_names = []
                for c in prog_result["chords"]:
                    # Strip octave digit from root (e.g., "C4" -> "C")
                    root = c["root"].rstrip("0123456789")
                    # Map full quality word to short form
                    qual = _quality_short.get(c["quality"], c["quality"])
                    chord_names.append(f"{root}{qual}")
                resolved_progressions.append(chord_names)
            except ValueError as e:
                unresolved.append({"numerals": numeral_list, "error": str(e)})

        result = {
            "genre": blueprint["id"],
            "key": key,
            "scales": resolved_scales,
            "chord_types": resolved_chords,
            "progressions": resolved_progressions,
        }
        if unresolved:
            result["unresolved"] = unresolved

        return json.dumps(result)
    except Exception as e:
        return format_error(
            "Failed to get genre palette",
            detail=str(e),
            suggestion="Check genre and key are valid",
        )
