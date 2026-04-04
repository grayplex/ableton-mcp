"""Mix recipe MCP tools: lookup, apply, sidechain routing, and section-aware mixing."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.devices.convert import convert_recipe_to_payload
from MCP_Server.mixing.catalog import get_master_recipe, get_recipe, list_recipes
from MCP_Server.mixing.freq_bands import detect_conflicts, extract_eq_bands
from MCP_Server.server import mcp
from MCP_Server.tools.analysis import _infer_role
from MCP_Server.tools.intelligence import _find_track
from MCP_Server.tools.scaffold import _beat_to_bar


@mcp.tool()
def get_mix_recipe(ctx: Context, role: str, genre: str) -> str:
    """Get mix recipe for a role in a genre. Returns device parameter values
    (EQ, compression, reverb/delay, panning, dynamics) in natural units.

    Parameters:
    - role: Mixing role (kick, bass, lead, pad, chords, vocal, atmospheric, return, master)
    - genre: Genre (use list_recipes() to see all available genres)
    """
    result = get_recipe(role, genre)
    if result is None:
        return format_error(
            f"No recipe found for role='{role}', genre='{genre}'",
            suggestion=f"Roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master. "
                       f"Genres: {', '.join(list_recipes())}",
        )
    return json.dumps(result, indent=2)


@mcp.tool()
def apply_mix_recipe(ctx: Context, track_index: int, role: str, genre: str) -> str:
    """Apply a mix recipe to a track: loads required devices and sets all parameters.

    Looks up the role x genre recipe, converts natural-unit values to normalized,
    sends a single apply_recipe command to load missing devices and set all params atomically.

    Parameters:
    - track_index: Index of the track to apply the recipe to
    - role: Mixing role (kick, bass, lead, pad, chords, vocal, atmospheric, return)
    - genre: Genre (use list_recipes() to see all available genres)
    """
    recipe = get_recipe(role, genre)
    if recipe is None:
        return format_error(
            f"No recipe found for role='{role}', genre='{genre}'",
            suggestion=f"Roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master. "
                       f"Genres: {', '.join(list_recipes())}",
        )

    devices_payload = convert_recipe_to_payload(recipe)
    timeout = max(30.0, len(devices_payload) * 15.0)

    conn = get_ableton_connection()
    result = conn.send_command("apply_recipe", {
        "track_index": track_index,
        "track_type": "track",
        "devices": devices_payload,
        "timeout": timeout,
    }, timeout=timeout)
    return json.dumps(result, indent=2)


@mcp.tool()
def apply_master_recipe(ctx: Context, genre: str) -> str:
    """Apply a master bus recipe to the master track: loads GlueCompressor,
    MultibandDynamics, and Limiter with genre-appropriate settings.

    Parameters:
    - genre: Genre (use list_recipes() to see all available genres)
    """
    recipe = get_master_recipe(genre)
    if recipe is None:
        return format_error(
            f"No master recipe found for genre='{genre}'",
            suggestion=f"Genres with master recipes: {', '.join(list_recipes())}",
        )

    devices_payload = convert_recipe_to_payload(recipe)
    timeout = max(30.0, len(devices_payload) * 15.0)

    conn = get_ableton_connection()
    result = conn.send_command("apply_recipe", {
        "track_index": 0,
        "track_type": "master",
        "devices": devices_payload,
        "timeout": timeout,
    }, timeout=timeout)
    return json.dumps(result, indent=2)


@mcp.tool()
def set_sidechain_source(
    ctx: Context,
    track_index: int,
    device_index: int,
    source_track_name: str,
    track_type: str = "track",
) -> str:
    """Set a compressor's sidechain input source by track name.

    Resolves the source track name to the correct routing at apply time.

    Parameters:
    - track_index: Index of the track containing the compressor
    - device_index: Index of the compressor device on the track
    - source_track_name: Name of the track to use as sidechain source
    - track_type: "track", "return", or "master" (default "track")
    """
    conn = get_ableton_connection()
    result = conn.send_command("set_sidechain_source", {
        "track_index": track_index,
        "device_index": device_index,
        "track_type": track_type,
        "source_track_name": source_track_name,
    })
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Section-aware mixing tools
# ---------------------------------------------------------------------------


@mcp.tool()
def apply_section_mix_recipe(
    ctx: Context,
    section_name: str,
    track_index: int,
    role: str,
    genre: str,
) -> str:
    """Apply a mix recipe to a track scoped to a specific arrangement section
    using automation breakpoints. Unlike apply_mix_recipe (global), this writes
    per-parameter automation so the recipe only affects the named section.

    Parameters:
    - section_name: Named arrangement section (matches locator name, case-insensitive)
    - track_index: Index of the track to apply the recipe to
    - role: Mixing role (kick, bass, lead, pad, chords, vocal, atmospheric, return)
    - genre: Genre (use list_recipes() to see all available genres)
    """
    recipe = get_recipe(role, genre)
    if recipe is None:
        return json.dumps({
            "error": f"No recipe found for role='{role}', genre='{genre}'",
            "section": section_name,
            "track_index": track_index,
        })

    devices_payload = convert_recipe_to_payload(recipe)

    conn = get_ableton_connection()

    # Get arrangement state to find section boundaries
    arrangement_state = conn.send_command("get_arrangement_state", {})
    cue_points = arrangement_state.get("cue_points", [])
    sig_num = arrangement_state.get("signature_numerator", 4)
    sig_den = arrangement_state.get("signature_denominator", 4)
    song_length = arrangement_state.get("song_length", 0.0)
    beats_per_bar = sig_num * (4.0 / sig_den)

    # Find section locator
    section_name_lower = section_name.lower()
    locator_index = None
    for i, cp in enumerate(cue_points):
        if cp.get("name", "").lower() == section_name_lower:
            locator_index = i
            break

    if locator_index is None:
        return json.dumps({
            "error": f"Section '{section_name}' not found in arrangement",
            "section": section_name,
            "track_index": track_index,
        })

    section_start_beat = cue_points[locator_index]["time"]
    if locator_index + 1 < len(cue_points):
        section_end_beat = cue_points[locator_index + 1]["time"]
    else:
        section_end_beat = song_length

    # Find clips in section to get clip_index for automation
    clips_result = conn.send_command("get_arrangement_clips", {"track_index": track_index})
    all_clips = clips_result.get("clips", [])
    section_clips = [
        c for c in all_clips
        if section_start_beat <= c["start_time"] < section_end_beat
    ]

    if not section_clips:
        return json.dumps({
            "error": f"No clips found in section '{section_name}' for track {track_index}",
            "section": section_name,
            "track_index": track_index,
        })

    # Write automation breakpoints for each device parameter
    devices_applied = 0
    automation_points = 0

    for device_spec in devices_payload:
        device_class = device_spec["class_name"]
        params = device_spec["params"]

        for param_name, normalized_value in params.items():
            # Write breakpoints: set value at section start, hold through end
            breakpoints = [
                {"time": section_start_beat, "value": normalized_value},
                {"time": section_end_beat, "value": normalized_value},
            ]
            conn.send_command("insert_envelope_breakpoints", {
                "track_index": track_index,
                "clip_index": 0,
                "device_index": 0,
                "parameter_name": param_name,
                "breakpoints": breakpoints,
            })
            automation_points += 2

        devices_applied += 1

    start_bar = _beat_to_bar(section_start_beat, beats_per_bar)
    end_bar = _beat_to_bar(section_end_beat, beats_per_bar)

    return json.dumps({
        "section": section_name,
        "track_index": track_index,
        "role": role,
        "genre": genre,
        "devices_applied": devices_applied,
        "automation_points": automation_points,
        "bar_range": f"{start_bar}-{end_bar}",
    })


@mcp.tool()
def detect_frequency_conflicts(
    ctx: Context,
    section_name: str,
    genre: str,
) -> str:
    """Detect frequency masking conflicts between tracks in a named section.

    Analyzes each track with clips in the section: infers role, looks up recipe
    EQ settings, and runs conflict detection to find frequency masking issues.

    Parameters:
    - section_name: Named arrangement section (matches locator name, case-insensitive)
    - genre: Genre for recipe EQ lookup (e.g. "house", "techno")
    """
    conn = get_ableton_connection()

    # Get arrangement state
    arrangement_state = conn.send_command("get_arrangement_state", {})
    cue_points = arrangement_state.get("cue_points", [])
    song_length = arrangement_state.get("song_length", 0.0)
    arrangement_tracks = arrangement_state.get("tracks", [])

    # Find section locator
    section_name_lower = section_name.lower()
    locator_index = None
    for i, cp in enumerate(cue_points):
        if cp.get("name", "").lower() == section_name_lower:
            locator_index = i
            break

    if locator_index is None:
        return json.dumps({
            "error": f"Section '{section_name}' not found in arrangement",
            "section": section_name,
            "genre": genre,
        })

    section_start_beat = cue_points[locator_index]["time"]
    if locator_index + 1 < len(cue_points):
        section_end_beat = cue_points[locator_index + 1]["time"]
    else:
        section_end_beat = song_length

    # Get mix state for device info
    mix_state = conn.send_command("get_mix_state", {})

    # Analyze each track with clips in the section
    track_data = []
    for track_info in arrangement_tracks:
        track_index = track_info["index"]
        track_name = track_info["name"]

        clips_result = conn.send_command("get_arrangement_clips", {"track_index": track_index})
        all_clips = clips_result.get("clips", [])
        section_clips = [
            c for c in all_clips
            if section_start_beat <= c["start_time"] < section_end_beat
        ]

        if not section_clips:
            continue

        role = _infer_role(track_name)
        if role is None:
            continue

        # Get EQ bands from recipe
        recipe = get_recipe(role, genre)
        if recipe is None:
            continue

        eq_bands = extract_eq_bands(recipe)
        if not eq_bands:
            continue

        track_data.append({
            "name": track_name,
            "role": role,
            "eq_bands": eq_bands,
        })

    # Run conflict detection
    conflicts = detect_conflicts(track_data)

    suggestions = [c["suggestion"] for c in conflicts]

    return json.dumps({
        "section": section_name,
        "genre": genre,
        "tracks_analyzed": len(track_data),
        "conflicts": conflicts,
        "suggestions": suggestions,
    })


@mcp.tool()
def setup_sidechain_chain(
    ctx: Context,
    source_track_name: str,
    target_track_name: str,
    target_device_index: int = None,
) -> str:
    """Set up sidechain routing from one track to another with auto-detection.

    Finds both tracks by name, auto-detects the first Compressor2 on the target
    track if target_device_index is not provided, and connects sidechain routing.

    Parameters:
    - source_track_name: Name of the sidechain source track (e.g. "Kick")
    - target_track_name: Name of the target track with compressor (e.g. "Bass")
    - target_device_index: Optional device index; auto-detects first Compressor2 if omitted
    """
    conn = get_ableton_connection()
    mix_state = conn.send_command("get_mix_state", {})

    # Find source track
    source_track = _find_track(mix_state, source_track_name)
    if source_track is None:
        return json.dumps({
            "error": f"Source track '{source_track_name}' not found",
            "source": source_track_name,
            "target": target_track_name,
        })

    # Find target track
    target_track = _find_track(mix_state, target_track_name)
    if target_track is None:
        return json.dumps({
            "error": f"Target track '{target_track_name}' not found",
            "source": source_track_name,
            "target": target_track_name,
        })

    # Auto-detect Compressor2 device index if not provided
    device_index = target_device_index
    if device_index is None:
        for d in target_track.get("devices", []):
            if d.get("class_name") == "Compressor2":
                device_index = d.get("index")
                break

    if device_index is None:
        return json.dumps({
            "error": f"No Compressor2 found on target track '{target_track_name}'",
            "source": source_track_name,
            "target": target_track_name,
        })

    # Determine target track index
    target_index = target_track.get("index", 0)

    # Set sidechain source
    conn.send_command("set_sidechain_source", {
        "track_index": target_index,
        "device_index": device_index,
        "track_type": "track",
        "source_track_name": source_track_name,
    })

    return json.dumps({
        "source": source_track_name,
        "target": target_track_name,
        "device_index": device_index,
        "status": "sidechain_connected",
    })
