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


@mcp.tool()
def duplicate_scene(ctx: Context, scene_index: int) -> str:
    """Duplicate a scene by index. Creates a copy of the scene and all its clips.

    Parameters:
    - scene_index: The index of the scene to duplicate
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("duplicate_scene", {"scene_index": scene_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to duplicate scene",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )


# --- Phase 13: Scene Extended ---


@mcp.tool()
def set_scene_color(ctx: Context, scene_index: int, color: str) -> str:
    """Set the color of a scene by friendly name.

    Parameters:
    - scene_index: Index of the scene
    - color: Color name (e.g. 'red', 'blue', 'green')
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "set_scene_color", {"scene_index": scene_index, "color": color}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set scene color",
            detail=str(e),
            suggestion="Use get_scene_color to see available colors",
        )


@mcp.tool()
def get_scene_color(ctx: Context, scene_index: int) -> str:
    """Get the current color of a scene.

    Parameters:
    - scene_index: Index of the scene
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_scene_color", {"scene_index": scene_index}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to get scene color",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )


@mcp.tool()
def set_scene_tempo(ctx: Context, scene_index: int, tempo: float, enabled: bool = True) -> str:
    """Set per-scene tempo. Scene tempo overrides global tempo when fired.

    Parameters:
    - scene_index: Index of the scene
    - tempo: Tempo in BPM
    - enabled: Whether scene tempo is active (default: True)
    """
    try:
        ableton = get_ableton_connection()
        params = {"scene_index": scene_index, "tempo": tempo, "enabled": enabled}
        result = ableton.send_command("set_scene_tempo", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set scene tempo",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )


@mcp.tool()
def set_scene_time_signature(
    ctx: Context,
    scene_index: int,
    numerator: int | None = None,
    denominator: int | None = None,
    enabled: bool = True,
) -> str:
    """Set per-scene time signature. Overrides global time signature when scene is fired.

    Parameters:
    - scene_index: Index of the scene
    - numerator: Time signature numerator (e.g. 3 for 3/4)
    - denominator: Time signature denominator (e.g. 4 for 3/4)
    - enabled: Whether scene time signature is active (default: True)
    """
    try:
        ableton = get_ableton_connection()
        params: dict = {"scene_index": scene_index, "enabled": enabled}
        if numerator is not None:
            params["numerator"] = numerator
        if denominator is not None:
            params["denominator"] = denominator
        result = ableton.send_command("set_scene_time_signature", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set scene time signature",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )


@mcp.tool()
def fire_scene_as_selected(ctx: Context, scene_index: int, force_legato: bool = False) -> str:
    """Fire the selected scene and advance selection to the next scene.

    Parameters:
    - scene_index: Index of the scene to fire
    - force_legato: If True, force legato transition (default: False)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "fire_scene_as_selected",
            {"scene_index": scene_index, "force_legato": force_legato},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to fire scene as selected",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )


@mcp.tool()
def get_scene_is_empty(ctx: Context, scene_index: int) -> str:
    """Check if a scene has no clips.

    Parameters:
    - scene_index: Index of the scene
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command(
            "get_scene_is_empty", {"scene_index": scene_index}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to check if scene is empty",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )
