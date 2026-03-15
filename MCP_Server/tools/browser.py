"""Browser tools: tree navigation and path browsing."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def get_browser_tree(
    ctx: Context, category_type: str = "all", max_depth: int = 1
) -> str:
    """Get a hierarchical tree of browser categories from Ableton.

    Controls how deep to traverse children in the browser tree. Default is 1
    (top-level items only). Maximum depth is 5 to prevent performance issues.

    Parameters:
    - category_type: Type of categories ('all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects')
    - max_depth: Depth of child traversal (default 1 = top level only, max 5)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_browser_tree",
            {"category_type": category_type, "max_depth": max_depth},
        )

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
