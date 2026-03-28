"""Mix recipe MCP tool."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.mixing.catalog import get_recipe


@mcp.tool()
def get_mix_recipe(ctx: Context, role: str, genre: str) -> str:
    """Get mix recipe for a role in a genre. Returns device parameter values
    (EQ, compression, reverb/delay, panning, dynamics) in natural units.

    Parameters:
    - role: Mixing role (kick, bass, lead, pad, chords, vocal, atmospheric, return, master)
    - genre: Genre (house, techno, ambient, dnb/drum_and_bass)
    """
    result = get_recipe(role, genre)
    if result is None:
        return format_error(
            f"No recipe found for role='{role}', genre='{genre}'",
            suggestion="Roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master. "
                       "Genres: house, techno, ambient, dnb",
        )
    return json.dumps(result, indent=2)
