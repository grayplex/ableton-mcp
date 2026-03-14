"""Device tools: instrument and effect loading."""

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def load_instrument_or_effect(ctx: Context, track_index: int, uri: str) -> str:
    """Load an instrument or effect onto a track using its browser URI.

    Parameters:
    - track_index: The index of the track to load the instrument on
    - uri: The URI of the instrument or effect (e.g., 'query:Synths#Instrument%20Rack:Bass:FileId_5116')
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "load_browser_item", {"track_index": track_index, "item_uri": uri}
        )

        # Check if the instrument was loaded successfully
        if result.get("loaded", False):
            item_name = result.get("item_name", "unknown")
            device_chain = result.get("devices", [])
            track_name = result.get("track_name", f"track {track_index}")
            if device_chain:
                return (
                    f"Loaded '{item_name}' on {track_name} "
                    f"(device chain: {', '.join(device_chain)})"
                )
            else:
                return f"Loaded '{item_name}' on {track_name}"
        else:
            error_msg = result.get("error", "Unknown reason")
            return format_error(
                f"Failed to load instrument with URI '{uri}'",
                detail=error_msg,
                suggestion="Verify the URI using get_browser_items_at_path first",
            )
    except Exception as e:
        return format_error(
            "Failed to load instrument",
            detail=str(e),
            suggestion="Verify the URI using get_browser_items_at_path first",
        )
