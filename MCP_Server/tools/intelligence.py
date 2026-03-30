"""Mix adjustment intelligence: suggest parameter changes by diffing state vs recipe."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import get_ableton_connection, format_error
from MCP_Server.devices.catalog import CATALOG
from MCP_Server.devices.convert import natural_to_normalized, normalized_to_natural
from MCP_Server.mixing.catalog import get_recipe, list_recipes
from MCP_Server.server import mcp
from MCP_Server.tools.analysis import _infer_role

DIFF_THRESHOLD = 0.03


def _find_track(mix_state: dict, track_name: str) -> dict | None:
    """Find track by case-insensitive substring match across all track groups.

    Searches regular tracks, return tracks, then master. First match wins
    (consistent with check_gain_staging pattern).
    """
    name_lower = track_name.lower()

    for track in mix_state.get("tracks", []):
        if name_lower in track["name"].lower():
            return track
    for track in mix_state.get("return_tracks", []):
        if name_lower in track["name"].lower():
            return track
    master = mix_state.get("master_track")
    if master and name_lower in master.get("name", "").lower():
        return master
    return None


def _format_display(device_class: str, param_name: str, normalized: float) -> str | None:
    """Format normalized value as human-readable natural-unit string.

    Returns None if no conversion available for the parameter.
    """
    natural = normalized_to_natural(device_class, param_name, normalized)
    if natural is None:
        return None

    device_entry = CATALOG.get(device_class)
    if device_entry is None:
        return None

    param_info = None
    for p in device_entry["parameters"]:
        if p["name"] == param_name:
            param_info = p
            break

    if param_info is None:
        return None

    if param_info.get("is_quantized"):
        return str(int(round(natural)))

    conv = param_info.get("conversion")
    if conv:
        unit = conv.get("unit", "")
        if unit == "Hz":
            return f"~{natural:.0f} Hz" if natural >= 1 else f"~{natural:.2f} Hz"
        if unit == "dB":
            return f"{natural:.1f} dB"
        if unit == "ms":
            return f"{natural:.0f} ms" if natural >= 1 else f"{natural:.2f} ms"
        if unit == "%":
            return f"{natural:.0f}%"
        return f"{natural:.2f}"

    return None


def _generate_reason(
    param_name: str, current_norm: float, suggested_norm: float,
    suggested_display: str | None, genre: str, role: str
) -> str:
    """Generate a one-sentence reason for the suggested parameter change."""
    direction = "above" if current_norm > suggested_norm else "below"
    target_str = suggested_display or f"{suggested_norm:.3f}"
    return (
        f"{param_name} is {direction} recipe target ({target_str}); "
        f"adjusting would better match {genre} {role} conventions."
    )


@mcp.tool()
def suggest_mix_adjustments(
    ctx: Context, track_name: str, genre: str, role: str = None
) -> str:
    """Suggest mix parameter changes by comparing current state against recipe targets.

    Compares a track's current device parameters against the role x genre recipe
    and returns per-parameter diffs with one-sentence reasoning. Read-only --
    no parameters are changed. Use apply_mix_recipe to apply changes.

    Args:
        track_name: Track name (case-insensitive substring match)
        genre: Genre for recipe lookup (use list_recipes() to see all available genres)
        role: Mixing role (kick, bass, lead, etc.). Inferred from track name if omitted.
    """
    # 1. Get mix state via RS command directly (NOT the MCP tool wrapper)
    conn = get_ableton_connection()
    mix_state = conn.send_command("get_mix_state", {})

    # 2. Find track by name
    track = _find_track(mix_state, track_name)
    if track is None:
        return format_error(
            f"Track '{track_name}' not found",
            suggestion="Check track name in Ableton session",
        )

    # 3. Resolve role
    resolved_role = role
    if resolved_role is None:
        resolved_role = _infer_role(track["name"])
    if resolved_role is None:
        return format_error(
            f"Cannot infer role from track name '{track['name']}'",
            suggestion="Provide role= explicitly (kick, bass, lead, pad, chords, vocal, atmospheric, return, master)",
        )

    # 4. Get recipe
    recipe = get_recipe(resolved_role, genre)
    if recipe is None:
        return format_error(
            f"No recipe for role='{resolved_role}' genre='{genre}'",
            suggestion=f"Available genres: {', '.join(list_recipes())}",
        )

    # 5. Build device param lookup from track state: {class_name: {param_name: normalized_value}}
    track_devices: dict[str, dict[str, float]] = {}
    for dev in track.get("devices", []):
        params = {p["name"]: p["value"] for p in dev.get("parameters", [])}
        track_devices[dev["class_name"]] = params

    # 6. Diff computation
    output_devices: dict[str, list] = {}
    total = 0
    for device_class, recipe_params in recipe.items():
        if device_class not in track_devices:
            continue  # Per locked decision #4: skip unloaded devices silently

        current_params = track_devices[device_class]
        display_name = CATALOG.get(device_class, {}).get("display_name", device_class)
        suggestions = []

        for param_name, recipe_natural in recipe_params.items():
            if param_name not in current_params:
                continue  # Param not in state -- skip

            current_norm = current_params[param_name]
            suggested_norm = natural_to_normalized(device_class, param_name, recipe_natural)
            delta = abs(current_norm - suggested_norm)

            if delta < DIFF_THRESHOLD:
                continue  # Below threshold -- skip

            # Add display values if conversion available
            cur_disp = _format_display(device_class, param_name, current_norm)
            sug_disp = _format_display(device_class, param_name, suggested_norm)

            suggestion: dict = {
                "parameter": param_name,
                "current_normalized": round(current_norm, 4),
                "suggested_normalized": round(suggested_norm, 4),
                "reason": _generate_reason(
                    param_name, current_norm, suggested_norm, sug_disp, genre, resolved_role
                ),
            }

            if cur_disp is not None:
                suggestion["current_display"] = cur_disp
            if sug_disp is not None:
                suggestion["suggested_display"] = sug_disp

            suggestions.append(suggestion)

        if suggestions:
            output_devices[display_name] = suggestions
            total += len(suggestions)

    # 7. Build response
    response: dict = {
        "track": track["name"],
        "role": resolved_role,
        "genre": genre,
        "total_suggestions": total,
        "devices": output_devices,
    }
    if total == 0:
        response["note"] = "Mix is close to recipe targets"

    return json.dumps(response, indent=2)
