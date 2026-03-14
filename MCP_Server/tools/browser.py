"""Browser tools: tree navigation, path browsing, drum kit loading."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_browser_tree(ctx: Context, category_type: str = "all") -> str:
    """Get a hierarchical tree of browser categories from Ableton.

    Parameters:
    - category_type: Type of categories ('all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects')
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_tree", {"category_type": category_type})

        # Check if we got any categories
        if "available_categories" in result and len(result.get("categories", [])) == 0:
            available_cats = result.get("available_categories", [])
            return (
                f"No categories found for '{category_type}'. "
                f"Available browser categories: {', '.join(available_cats)}"
            )

        # Format the tree in a more readable way
        total_folders = result.get("total_folders", 0)
        formatted_output = (
            f"Browser tree for '{category_type}' (showing {total_folders} folders):\n\n"
        )

        def format_tree(item, indent=0):
            output = ""
            if item:
                prefix = "  " * indent
                name = item.get("name", "Unknown")
                path = item.get("path", "")
                has_more = item.get("has_more", False)

                # Add this item
                output += f"{prefix}• {name}"
                if path:
                    output += f" (path: {path})"
                if has_more:
                    output += " [...]"
                output += "\n"

                # Add children
                for child in item.get("children", []):
                    output += format_tree(child, indent + 1)
            return output

        # Format each category
        for category in result.get("categories", []):
            formatted_output += format_tree(category)
            formatted_output += "\n"

        return formatted_output
    except Exception as e:
        error_msg = str(e)
        if "Browser is not available" in error_msg:
            return format_error(
                "Ableton browser is not available",
                detail=error_msg,
                suggestion="Make sure Ableton Live is fully loaded and try again",
            )
        elif "Could not access Live application" in error_msg:
            return format_error(
                "Could not access Ableton Live application",
                detail=error_msg,
                suggestion="Make sure Ableton Live is running and Remote Script is loaded",
            )
        else:
            return format_error(
                "Failed to get browser tree",
                detail=error_msg,
                suggestion="Verify connection with get_connection_status",
            )


@mcp.tool()
def get_browser_items_at_path(ctx: Context, path: str) -> str:
    """Get browser items at a specific path in Ableton's browser.

    Parameters:
    - path: Path in the format "category/folder/subfolder"
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_items_at_path", {"path": path})

        # Check if there was an error with available categories
        if "error" in result and "available_categories" in result:
            error = result.get("error", "")
            available_cats = result.get("available_categories", [])
            return f"Error: {error}\nAvailable browser categories: {', '.join(available_cats)}"

        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = str(e)
        if "Browser is not available" in error_msg:
            return format_error(
                "Ableton browser is not available",
                detail=error_msg,
                suggestion="Make sure Ableton Live is fully loaded and try again",
            )
        elif "Could not access Live application" in error_msg:
            return format_error(
                "Could not access Ableton Live application",
                detail=error_msg,
                suggestion="Make sure Ableton Live is running and Remote Script is loaded",
            )
        elif "Unknown or unavailable category" in error_msg:
            return format_error(
                "Invalid browser category",
                detail=error_msg,
                suggestion="Check available categories using get_browser_tree",
            )
        elif "Path part" in error_msg and "not found" in error_msg:
            return format_error(
                "Browser path not found",
                detail=error_msg,
                suggestion="Check the path and try again",
            )
        else:
            return format_error(
                "Failed to get browser items at path",
                detail=error_msg,
                suggestion="Verify connection with get_connection_status",
            )


@mcp.tool()
def load_drum_kit(ctx: Context, track_index: int, rack_uri: str, kit_path: str) -> str:
    """Load a drum rack and then load a specific drum kit into it.

    Parameters:
    - track_index: The index of the track to load on
    - rack_uri: The URI of the drum rack to load (e.g., 'Drums/Drum Rack')
    - kit_path: Path to the drum kit in the browser (e.g., 'drums/acoustic/kit1')
    """
    try:
        ableton = get_ableton_connection()

        # Step 1: Load the drum rack
        result = ableton.send_command(
            "load_browser_item", {"track_index": track_index, "item_uri": rack_uri}
        )

        if not result.get("loaded", False):
            return f"Failed to load drum rack with URI '{rack_uri}'"

        # Step 2: Get the drum kit items at the specified path
        kit_result = ableton.send_command("get_browser_items_at_path", {"path": kit_path})

        if "error" in kit_result:
            return f"Loaded drum rack but failed to find drum kit: {kit_result.get('error')}"

        # Step 3: Find a loadable drum kit
        kit_items = kit_result.get("items", [])
        loadable_kits = [item for item in kit_items if item.get("is_loadable", False)]

        if not loadable_kits:
            return f"Loaded drum rack but no loadable drum kits found at '{kit_path}'"

        # Step 4: Load the first loadable kit
        kit_uri = loadable_kits[0].get("uri")
        ableton.send_command("load_browser_item", {"track_index": track_index, "item_uri": kit_uri})

        return f"Loaded drum rack and kit '{loadable_kits[0].get('name')}' on track {track_index}"
    except Exception as e:
        return format_error(
            "Failed to load drum kit",
            detail=str(e),
            suggestion="Verify the rack_uri and kit_path using get_browser_items_at_path first",
        )
