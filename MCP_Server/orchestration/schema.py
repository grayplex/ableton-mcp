"""Orchestration schema: TypedDicts for production agenda, execution plans, and checkpoints.

All types are TypedDicts — JSON-serializable without .asdict().
Defined here for all of v1.9 (phases 48-51) to avoid circular imports.
"""

from typing import Literal, Optional, TypedDict


# ---------------------------------------------------------------------------
# Phase 48 — Production Agenda
# ---------------------------------------------------------------------------

class ProductionPhase(TypedDict):
    """One named phase in a production workflow."""
    name: str                # human-readable phase name (e.g., "Drum Programming")
    phase_id: str            # slug matching phase_type (e.g., "drums")
    phase_type: str          # Literal: setup|drums|bass|harmony|melody|sound_design|arrangement|mix|master
    goal: str                # one-sentence description of what this phase produces
    roles: list              # list[str] — genre instrumentation roles relevant to this phase
    estimated_steps: int     # typical tool call count
    depends_on: list         # list[str] — phase_ids that must precede this one


class ProductionAgenda(TypedDict):
    """Ordered list of production phases for a genre."""
    genre: str
    phases: list             # list[ProductionPhase]
    total_estimated_steps: int


# ---------------------------------------------------------------------------
# Phase 49 — Phase Execution Plans
# ---------------------------------------------------------------------------

class ExecutionStep(TypedDict):
    """One concrete, immediately-executable tool call in a phase checklist."""
    step_number: int
    description: str         # plain English: what this step does
    tool_name: str           # exact registered MCP tool name
    suggested_args: dict     # {param: value}; session-state values use "<sentinel>" strings
    depends_on_step: Optional[int]
    phase: str               # phase_id this step belongs to


class PhaseChecklist(TypedDict):
    """Ordered list of execution steps for one production phase."""
    phase_name: str
    genre: str
    section: Optional[str]   # arrangement section scope (None = session-wide)
    steps: list              # list[ExecutionStep]
    total_steps: int
    estimated_tool_calls: int


# ---------------------------------------------------------------------------
# Phase 50 — Production Checkpoint
# ---------------------------------------------------------------------------

class SessionStats(TypedDict):
    """Compact session statistics for checkpoint."""
    track_count: int
    tracks_with_instruments: int
    tracks_with_clips: int
    has_mix_applied: bool     # True if any track has EQ Eight + Compressor loaded
    has_master_applied: bool  # True if master has GlueCompressor + Limiter


class ProductionCheckpoint(TypedDict):
    """Compact snapshot of production progress inferred from live Ableton state."""
    genre: Optional[str]
    completed_phases: list       # list[str] — phase_ids inferred complete
    active_phase: Optional[str]  # phase_id currently in progress
    active_phase_progress: float # 0.0–1.0
    pending_steps: list          # list[str] — human-readable pending items
    session_stats: dict          # SessionStats
    next_phase: Optional[str]    # phase_id after active_phase
    resume_hint: str             # single sentence: what to do next
