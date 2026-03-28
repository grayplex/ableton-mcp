"""Device catalog and role taxonomy MCP tools."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.devices import get_catalog_entry, get_roles


@mcp.tool()
def get_device_catalog(ctx: Context, device_name: str) -> str:
    """Get the parameter catalog for a built-in Ableton device. Returns exact API parameter names,
    value ranges, and normalized-to-natural-unit conversion formulas.

    Parameters:
    - device_name: Device display name (e.g., 'EQ Eight') or class name (e.g., 'Eq8')
    """
    entry = get_catalog_entry(device_name)
    if entry is None:
        return format_error(
            f"Device '{device_name}' not found in catalog",
            suggestion="Available devices: EQ Eight, Compressor, Glue Compressor, Drum Buss, "
                       "Multiband Dynamics, Reverb, Delay, Auto Filter, Gate, Limiter, "
                       "Envelope Follower, Utility",
        )
    return json.dumps(entry, indent=2)


@mcp.tool()
def get_role_taxonomy(ctx: Context) -> str:
    """Get the canonical mixing role taxonomy for recipe lookup. Returns the role identifiers
    used as keys for mix recipes across all genres."""
    return json.dumps({"roles": get_roles()})
