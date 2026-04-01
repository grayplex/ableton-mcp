"""Orchestration package: production agenda, phase execution plans, checkpoints, and next-action recommendations.

Public API:
- schema.ProductionPhase, schema.ProductionAgenda
- schema.ExecutionStep, schema.PhaseChecklist
- schema.ProductionCheckpoint, schema.SessionStats
- agenda.get_agenda, agenda.AGENDA_CATALOG
- execution.get_execution_plan
"""

from .agenda import AGENDA_CATALOG, get_agenda
from .execution import get_execution_plan

__all__ = ["AGENDA_CATALOG", "get_agenda", "get_execution_plan"]
