"""Sound selection tools: descriptor taxonomy and instrument recommendations."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.sounds.catalog import list_descriptors


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
