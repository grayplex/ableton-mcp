"""Prompt interpretation tools: convert natural-language music prompts to production parameters.

interpret_prompt: Returns a ProductionBrief from any free-text music description.
interpret_prompt_to_plan: Returns both a ProductionBrief and a full production plan in one call.
"""

import copy
import json

from mcp.server.fastmcp import Context

from MCP_Server.connection import format_error
from MCP_Server.genres.catalog import get_blueprint
from MCP_Server.prompt.deriver import derive
from MCP_Server.prompt.history import record_brief, get_briefs, _SESSION_START
from MCP_Server.server import mcp
from MCP_Server.tools.plans import _build_plan_sections


@mcp.tool()
def interpret_prompt(ctx: Context, text: str) -> str:
    """Interpret a natural-language music prompt into structured production parameters.

    Converts a free-text description like "lo-fi hip hop beat" or "dark minimal techno"
    into a ProductionBrief with concrete production parameters derived deterministically
    from genre conventions, mood signals, and instrument references. Use this as the
    first step in any session to establish your production parameters before calling
    generate_production_plan or scaffold_arrangement.

    Parameters:
    - text: Free-text music description (e.g. "lo-fi hip hop beat", "euphoric trance anthem")

    Returns JSON with:
    - raw_prompt: The original text
    - primary_genre: Resolved genre blueprint id (or null for unrecognized prompts)
    - tempo_range: {"min_bpm": int, "max_bpm": int}
    - key_feel: {"scale": str, "mode": "major"|"minor"}
    - groove_feel: {"pattern_type": str, "swing_pct": int}
    - energy_level: 1–10
    - instrument_hints: list of {"role": str, "descriptor": str}
    - effect_hints: list of effect descriptor strings
    - velocity_style: "laid_back" | "medium" | "driving"
    - confidence: 0.0–1.0 parse confidence
    - reasoning: list of plain-English notes explaining each parameter choice
    """
    try:
        brief = derive(text)
        record_brief(text, brief, "interpret_prompt")
        return json.dumps(brief, indent=2)
    except Exception as e:
        return format_error(
            "interpret_prompt failed",
            detail=str(e),
            suggestion="Check that the prompt is a non-empty string",
        )


@mcp.tool()
def interpret_prompt_to_plan(
    ctx: Context,
    text: str,
    bars_per_section: int | None = None,
) -> str:
    """Interpret a natural-language music prompt and generate a full production plan in one call.

    Combines interpret_prompt and generate_production_plan: extracts genre, tempo, key,
    and groove from the prompt, then builds a complete section-by-section plan using
    the genre's arrangement blueprint. Eliminates the need to chain these two calls manually.

    Parameters:
    - text: Free-text music description (e.g. "lo-fi hip hop beat", "dark techno banger")
    - bars_per_section: Optional override to resize all sections to this bar count

    Returns JSON with:
    - brief: The full ProductionBrief (same as interpret_prompt)
    - plan: The production plan (same shape as generate_production_plan output),
            or null when no genre could be resolved from the prompt
    - warning: Optional string when genre confidence is low (< 0.5)
    """
    try:
        brief = derive(text)
        record_brief(text, brief, "interpret_prompt_to_plan")

        result: dict = {"brief": brief, "plan": None}

        genre_id = brief.get("primary_genre")
        if genre_id is None:
            result["warning"] = (
                "No genre could be resolved from the prompt "
                f"(confidence={brief['confidence']:.2f}). "
                "Provide a more specific prompt or call generate_production_plan directly."
            )
            return json.dumps(result, indent=2)

        # Fetch blueprint and build plan sections
        bp = get_blueprint(genre_id)
        if bp is None:
            result["warning"] = f"Genre '{genre_id}' resolved but blueprint unavailable."
            return json.dumps(result, indent=2)

        sections = copy.deepcopy(bp["arrangement"]["sections"])

        # Apply bars_per_section override if requested
        section_bar_overrides = None
        if bars_per_section is not None:
            section_bar_overrides = {s["name"]: bars_per_section for s in sections}

        plan_sections, warnings = _build_plan_sections(
            sections,
            section_bar_overrides=section_bar_overrides,
        )

        # Derive a reasonable key root from key_feel
        key_feel = brief.get("key_feel", {})
        mode = key_feel.get("mode", "minor")
        scale = key_feel.get("scale", "natural_minor")
        # Use "Am" for minor, "C" for major as neutral root defaults
        key_root = "Am" if mode == "minor" else "C"

        tempo_range = brief.get("tempo_range", {})
        bpm = (tempo_range.get("min_bpm", 80) + tempo_range.get("max_bpm", 130)) // 2

        plan: dict = {
            "genre": genre_id,
            "key": key_root,
            "bpm": bpm,
            "time_signature": "4/4",
            "scale": scale,
            "vibe": text,
            "sections": plan_sections,
        }

        if warnings:
            plan["warnings"] = warnings

        if brief["confidence"] < 0.5:
            result["warning"] = (
                f"Low prompt confidence ({brief['confidence']:.2f}) — "
                "plan is based on partial genre detection. "
                "Verify the genre and BPM in the brief before proceeding."
            )

        result["plan"] = plan
        return json.dumps(result, indent=2)

    except Exception as e:
        return format_error(
            "interpret_prompt_to_plan failed",
            detail=str(e),
            suggestion="Check that the prompt is a non-empty string",
        )


@mcp.tool()
def list_production_briefs(ctx: Context) -> str:
    """List all production briefs interpreted during this session.

    Returns a JSON summary of each prompt interpretation, ordered chronologically.
    Use after a context reset to recall what prompts have been processed.

    Returns JSON with:
    - count: Number of briefs interpreted this session
    - session_started: Unix timestamp when the server session began
    - briefs: Array of brief summaries (index, raw_prompt, primary_genre,
              bpm_range, key_feel, energy_level, confidence, source, timestamp)
    """
    entries = get_briefs()
    summaries = []
    for i, entry in enumerate(entries):
        brief = entry["brief"]
        tempo = brief.get("tempo_range", {})
        bpm_range = f"{tempo.get('min_bpm', '?')}-{tempo.get('max_bpm', '?')}"
        kf = brief.get("key_feel", {})
        key_feel = f"{kf.get('scale', '?')} {kf.get('mode', '?')}"
        summaries.append({
            "index": i,
            "raw_prompt": entry["raw_prompt"],
            "primary_genre": brief.get("primary_genre"),
            "bpm_range": bpm_range,
            "key_feel": key_feel,
            "energy_level": brief.get("energy_level"),
            "confidence": brief.get("confidence"),
            "source": entry["source"],
            "timestamp": entry["timestamp"],
        })
    return json.dumps({
        "count": len(entries),
        "session_started": _SESSION_START,
        "briefs": summaries,
    }, indent=2)
