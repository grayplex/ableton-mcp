"""Sound selection tools: descriptor taxonomy and instrument recommendations."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.sounds.catalog import get_profile, list_descriptors, list_profiles, recommend


@mcp.tool()
def list_sound_descriptors(ctx: Context) -> str:
    """List all supported sound descriptor tags grouped by axis.

    Returns role tags (bass, lead, pad, keys, kick, snare, hihat, percussion,
    texture) and character tags (warm, bright, dark, evolving, punchy,
    aggressive, lush, organic, tight) derived from all registered instrument
    profiles.

    Use these tags as input to get_sound_recommendation() to find the best
    Ableton native instrument for a sound design goal.

    Returns JSON with keys:
    - role: sorted list of role descriptor tags
    - character: sorted list of character descriptor tags
    """
    try:
        return json.dumps(list_descriptors())
    except Exception as e:
        return format_error(
            "Failed to list sound descriptors",
            detail=str(e),
            suggestion="This tool takes no parameters",
        )


@mcp.tool()
def get_sound_recommendation(ctx: Context, descriptor: str) -> str:
    """Recommend the best native Ableton instrument for a sound design descriptor.

    Tokenizes the descriptor, scores all 6 native instruments by summing their
    affinity weights, and returns the top match with browser load path and reasoning.

    The returned browser_path is directly usable with load_instrument_or_effect()
    to load the instrument into the selected track.

    Parameters:
    - descriptor: Natural-language sound description, e.g. "warm pad", "punchy kick",
      "bright lead", "dark bass". Use list_sound_descriptors() to see all valid tags.

    Returns JSON with keys:
    - id: instrument identifier
    - name: display name
    - score: total affinity score
    - browser_path: Ableton browser root path (use with load_instrument_or_effect)
    - category_hint: suggested browser category folder
    - reasoning: one-line plain-language explanation
    """
    try:
        result = recommend(descriptor)
        if result is None:
            return format_error(
                f"No instrument match found for '{descriptor}'",
                detail="All instruments scored 0 for the given descriptor",
                suggestion="Use list_sound_descriptors() to see valid role and character tags",
            )
        return json.dumps(result)
    except Exception as e:
        return format_error(
            "Failed to get sound recommendation",
            detail=str(e),
            suggestion="Provide a descriptor string like 'warm pad' or 'punchy kick'",
        )


@mcp.tool()
def get_instrument_profile(ctx: Context, instrument: str) -> str:
    """Get the full character profile for a native Ableton instrument.

    Returns sonic character description, strengths, weaknesses, descriptor
    affinities (role and character axes with 0.0-1.0 weights), and browser
    category paths for the specified instrument.

    Parameters:
    - instrument: Instrument name or alias. Supported: wavetable (wt), analog (al),
      operator (op), drift, simpler (smplr), drum_rack (dr)

    Returns JSON with the full instrument profile including:
    - id, name, aliases
    - sonic_character: paragraph describing the instrument's identity
    - strengths: list of strength phrases
    - weaknesses: list of weakness phrases
    - descriptor_affinities: role and character axes with weights
    - browser: root path and category folder mapping
    """
    try:
        profile = get_profile(instrument)
        if profile is None:
            available = [p["id"] for p in list_profiles()]
            return format_error(
                f"Unknown instrument '{instrument}'",
                detail=f"Available instruments: {', '.join(sorted(available))}",
                suggestion="Use the instrument id or alias, e.g. 'wavetable', 'wt', 'analog', 'op'",
            )
        return json.dumps(profile)
    except Exception as e:
        return format_error(
            "Failed to get instrument profile",
            detail=str(e),
            suggestion="Provide an instrument name like 'wavetable', 'analog', or 'drum_rack'",
        )
