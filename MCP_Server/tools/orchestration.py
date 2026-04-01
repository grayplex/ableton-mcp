"""Orchestration tools: production agenda, phase execution plans, checkpoints, next-action recommendations."""

import json

from mcp.server.fastmcp import Context

from MCP_Server.orchestration.agenda import get_agenda
from MCP_Server.orchestration.execution import get_execution_plan
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


@mcp.tool()
def get_phase_execution_plan(ctx: Context, phase_name: str, genre: str,
                              section_name: str = None, context: str = None) -> str:
    """Get a concrete ordered execution checklist for a production phase.

    Returns a PhaseChecklist with ExecutionStep entries — exact tool names and
    genre-appropriate suggested args (BPM, scale, instrument names, MIDI note patterns).
    Steps use sentinel strings (e.g. "<track_index>") for session-state values that must
    be resolved at runtime via get_all_tracks().

    Use this at the start of each production phase to get the exact sequence of tool
    calls needed. Execute steps in order, replacing sentinel values with live data.

    Args:
        phase_name: Phase type slug: setup, drums, bass, harmony, melody,
                    sound_design, arrangement, mix, or master.
        genre: Genre id or alias (e.g. "house", "techno", "lo_fi", "drum_and_bass").
        section_name: Optional arrangement section name (e.g. "Drop", "Verse").
                      When provided, note-writing steps use create_arrangement_midi_clip
                      with sentinel bar positions instead of session-view create_clip.
        context: Optional JSON override dict. Supported keys:
                 - instrument: override instrument name for this phase
                 - tempo: override BPM (setup phase only)
                 - scale: override scale name (setup phase only)
                 - root_note: override root note 0-11 (setup phase only)

    Returns:
        JSON string with PhaseChecklist or {"error": "..."} on unknown genre or phase.
    """
    context_dict = None
    if context:
        try:
            context_dict = json.loads(context)
        except (json.JSONDecodeError, TypeError):
            context_dict = None

    result = get_execution_plan(phase_name, genre, section_name, context_dict)
    return json.dumps(result)


@mcp.tool()
def get_production_checkpoint(ctx: Context, genre: str = None) -> str:
    """Get a compact snapshot of production progress from live Ableton state.

    Reads current Ableton session (tracks, devices, clips, locators) and infers
    which production phases are complete, which is active, and what to do next.
    Use this at the start of a new context window to re-orient, or any time you
    need to know where you are in the production.

    Args:
        genre: Genre id or alias (e.g. "house", "techno"). Required for phase
               inference. Without genre, returns session stats only.

    Returns:
        JSON ProductionCheckpoint with completed_phases, active_phase,
        session_stats, and a resume_hint sentence.
    """
    from MCP_Server.orchestration.checkpoint import get_checkpoint
    result = get_checkpoint(genre)
    return json.dumps(result)


@mcp.tool()
def get_next_actions(ctx: Context, genre: str, phase_name: str = None, n: int = 10) -> str:
    """Get the next N concrete tool calls to execute in the current production phase.

    Reads the live Ableton checkpoint to determine where you are, then returns
    specific ordered ExecutionStep entries with exact tool names and suggested args.
    Use this when starting a new context window or after completing a batch of steps.

    If phase_name is provided, bypasses the checkpoint and returns the full checklist
    for that specific phase — useful for planning ahead or restarting a phase.

    Args:
        genre: Genre id or alias (e.g. "house", "techno").
        phase_name: Optional phase to target (setup/drums/bass/harmony/melody/
                    sound_design/arrangement/mix/master). Bypasses checkpoint.
        n: Number of steps to return (default 10, max 25).

    Returns:
        JSON with checkpoint_summary, active_phase, genre, and steps list.
    """
    from MCP_Server.orchestration.next_actions import get_next_actions_result
    result = get_next_actions_result(genre, phase_name, n)
    return json.dumps(result)


@mcp.tool()
def get_phase_transition_guidance(ctx: Context, from_phase: str, genre: str = None,
                                   to_phase: str = None) -> str:
    """Check if a production phase is complete enough to advance to the next.

    Reads live Ableton state and checks phase-specific completion criteria:
    drums = drum track with clips exists; mix = Compressor2 on at least one track;
    master = GlueCompressor + Limiter2 on master track; etc.

    Returns a go/no-go verdict with specific blockers and fix hints so you know
    exactly what's missing before moving on.

    Args:
        from_phase: Phase to validate (setup/drums/bass/harmony/melody/
                    sound_design/arrangement/mix/master).
        genre: Genre id or alias. Used to determine next phase in sequence.
        to_phase: Optional override for the target next phase.

    Returns:
        JSON with ready_to_advance, completion_pct, blockers, fix_hints, next_phase.
    """
    from MCP_Server.orchestration.next_actions import get_transition_guidance
    result = get_transition_guidance(from_phase, genre, to_phase)
    return json.dumps(result)
