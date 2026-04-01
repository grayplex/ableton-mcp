"""Orchestration tools: production agenda, phase execution plans, checkpoints, next-action recommendations."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.orchestration.agenda import get_agenda
from MCP_Server.server import mcp


@mcp.tool()
def get_production_agenda(ctx: Context, genre: str, brief: str = None) -> str:
    """Get an ordered production phase agenda for a genre.

    Returns a ProductionAgenda with phases in genre-appropriate order
    (e.g., techno leads with drums→bass before sound design; ambient has
    no drums phase, starts with pads). Each phase includes its goal,
    the genre roles it involves, and an estimated step count.

    Use this at the start of a production to understand the full workflow,
    or before each phase to confirm what comes next.

    Args:
        genre: Genre id or alias (e.g., "house", "techno", "lo_fi", "drum_and_bass")
        brief: Optional JSON string of a ProductionBrief (from interpret_prompt).
               If provided, brief.primary_genre overrides genre arg and
               brief.energy_level >= 7 elevates drums to the first phase.

    Returns:
        JSON string with ProductionAgenda or {"error": "..."} on unknown genre.
    """
    brief_dict = None
    if brief:
        try:
            brief_dict = json.loads(brief)
        except (json.JSONDecodeError, TypeError):
            brief_dict = None

    result = get_agenda(genre, brief_dict)
    return json.dumps(result)
