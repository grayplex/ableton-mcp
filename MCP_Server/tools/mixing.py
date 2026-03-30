"""Mix recipe MCP tools: lookup, apply, and sidechain routing."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.devices.convert import convert_recipe_to_payload
from MCP_Server.mixing.catalog import get_master_recipe, get_recipe, list_recipes
from MCP_Server.server import mcp


@mcp.tool()
def get_mix_recipe(ctx: Context, role: str, genre: str) -> str:
    """Get mix recipe for a role in a genre. Returns device parameter values
    (EQ, compression, reverb/delay, panning, dynamics) in natural units.

    Parameters:
    - role: Mixing role (kick, bass, lead, pad, chords, vocal, atmospheric, return, master)
    - genre: Genre (use list_recipes() to see all available genres)
    """
    result = get_recipe(role, genre)
    if result is None:
        return format_error(
            f"No recipe found for role='{role}', genre='{genre}'",
            suggestion=f"Roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master. "
                       f"Genres: {', '.join(list_recipes())}",
        )
    return json.dumps(result, indent=2)


@mcp.tool()
def apply_mix_recipe(ctx: Context, track_index: int, role: str, genre: str) -> str:
    """Apply a mix recipe to a track: loads required devices and sets all parameters.

    Looks up the role x genre recipe, converts natural-unit values to normalized,
    sends a single apply_recipe command to load missing devices and set all params atomically.

    Parameters:
    - track_index: Index of the track to apply the recipe to
    - role: Mixing role (kick, bass, lead, pad, chords, vocal, atmospheric, return)
    - genre: Genre (use list_recipes() to see all available genres)
    """
    recipe = get_recipe(role, genre)
    if recipe is None:
        return format_error(
            f"No recipe found for role='{role}', genre='{genre}'",
            suggestion=f"Roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master. "
                       f"Genres: {', '.join(list_recipes())}",
        )

    devices_payload = convert_recipe_to_payload(recipe)

    conn = get_ableton_connection()
    result = conn.send_command("apply_recipe", {
        "track_index": track_index,
        "track_type": "track",
        "devices": devices_payload,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
def apply_master_recipe(ctx: Context, genre: str) -> str:
    """Apply a master bus recipe to the master track: loads GlueCompressor,
    MultibandDynamics, and Limiter with genre-appropriate settings.

    Parameters:
    - genre: Genre (use list_recipes() to see all available genres)
    """
    recipe = get_master_recipe(genre)
    if recipe is None:
        return format_error(
            f"No master recipe found for genre='{genre}'",
            suggestion=f"Genres with master recipes: {', '.join(list_recipes())}",
        )

    devices_payload = convert_recipe_to_payload(recipe)

    conn = get_ableton_connection()
    result = conn.send_command("apply_recipe", {
        "track_index": 0,
        "track_type": "master",
        "devices": devices_payload,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
def set_sidechain_source(
    ctx: Context,
    track_index: int,
    device_index: int,
    source_track_name: str,
    track_type: str = "track",
) -> str:
    """Set a compressor's sidechain input source by track name.

    Resolves the source track name to the correct routing at apply time.

    Parameters:
    - track_index: Index of the track containing the compressor
    - device_index: Index of the compressor device on the track
    - source_track_name: Name of the track to use as sidechain source
    - track_type: "track", "return", or "master" (default "track")
    """
    conn = get_ableton_connection()
    result = conn.send_command("set_sidechain_source", {
        "track_index": track_index,
        "device_index": device_index,
        "track_type": track_type,
        "source_track_name": source_track_name,
    })
    return json.dumps(result, indent=2)
