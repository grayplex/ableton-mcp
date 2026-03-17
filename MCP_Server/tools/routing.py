"""Routing tools: get and set track input/output routing types."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_input_routing_types(ctx: Context, track_index: int, track_type: str = "track") -> str:
    """Get available input routing types for a track. Returns the current input routing and a list of all available options.

    Parameters:
    - track_index: Index of the track
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_input_routing_types",
            {"track_index": track_index, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get input routing types",
            detail=str(e),
            suggestion="Check track_index with get_all_tracks.",
        )


@mcp.tool()
def set_input_routing(ctx: Context, track_index: int, routing_name: str, track_type: str = "track") -> str:
    """Set the input routing of a track by routing type name (case-insensitive match). Returns the previous and new routing.

    Parameters:
    - track_index: Index of the track
    - routing_name: Display name of the routing type (e.g. 'Ext. In', 'Track 1-Audio'). Use get_input_routing_types to see available options.
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_input_routing",
            {"track_index": track_index, "routing_name": routing_name, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set input routing",
            detail=str(e),
            suggestion="Use get_input_routing_types to see available routing options for this track.",
        )


@mcp.tool()
def get_output_routing_types(ctx: Context, track_index: int, track_type: str = "track") -> str:
    """Get available output routing types for a track. Returns the current output routing and a list of all available options.

    Parameters:
    - track_index: Index of the track
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_output_routing_types",
            {"track_index": track_index, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get output routing types",
            detail=str(e),
            suggestion="Check track_index with get_all_tracks.",
        )


@mcp.tool()
def set_output_routing(ctx: Context, track_index: int, routing_name: str, track_type: str = "track") -> str:
    """Set the output routing of a track by routing type name (case-insensitive match). Returns the previous and new routing.

    Parameters:
    - track_index: Index of the track
    - routing_name: Display name of the routing type (e.g. 'Master', 'Ext. Out', 'Sends Only'). Use get_output_routing_types to see available options.
    - track_type: Type of track - 'track' (default), 'return', or 'master'
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_output_routing",
            {"track_index": track_index, "routing_name": routing_name, "track_type": track_type},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set output routing",
            detail=str(e),
            suggestion="Use get_output_routing_types to see available routing options for this track.",
        )
