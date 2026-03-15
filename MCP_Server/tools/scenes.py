"""Scene tools: creation, naming, firing, and deletion of scenes."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp


@mcp.tool()
def create_scene(ctx: Context, index: int = -1, name: str | None = None) -> str:
    """Create a new scene at the specified index. Use index=-1 (default) to append at the end.

    Parameters:
    - index: Position to insert the scene (-1 to append at end, default: -1)
    - name: Optional name for the new scene
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"index": index}
        if name is not None:
            params["name"] = name
        result = ableton.send_command("create_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to create scene",
            detail=str(e),
            suggestion="Use index=-1 to append or a valid scene index",
        )


@mcp.tool()
def set_scene_name(ctx: Context, scene_index: int, name: str) -> str:
    """Rename a scene.

    Parameters:
    - scene_index: The index of the scene to rename
    - name: The new name for the scene
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_scene_name", {"scene_index": scene_index, "name": name})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set scene name",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )


@mcp.tool()
def fire_scene(ctx: Context, scene_index: int) -> str:
    """Fire (launch) a scene, triggering all clips in that scene row.

    Parameters:
    - scene_index: The index of the scene to fire
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("fire_scene", {"scene_index": scene_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to fire scene",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )


@mcp.tool()
def delete_scene(ctx: Context, scene_index: int) -> str:
    """Delete a scene. Cannot delete the last remaining scene.

    Parameters:
    - scene_index: The index of the scene to delete
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("delete_scene", {"scene_index": scene_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to delete scene",
            detail=str(e),
            suggestion="Verify scene_index is valid. Cannot delete the last scene.",
        )
