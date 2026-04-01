"""Orchestration package: production agenda, phase execution plans, checkpoints, and next-action recommendations.

Public API:
- schema.ProductionPhase, schema.ProductionAgenda
- schema.ExecutionStep, schema.PhaseChecklist
- schema.ProductionCheckpoint, schema.SessionStats
- agenda.get_agenda, agenda.AGENDA_CATALOG
- execution.get_execution_plan
- checkpoint.get_checkpoint
"""

from .agenda import AGENDA_CATALOG, get_agenda
from .checkpoint import get_checkpoint
from .execution import get_execution_plan

__all__ = ["AGENDA_CATALOG", "get_agenda", "get_checkpoint", "get_execution_plan"]
