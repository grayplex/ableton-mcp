"""Orchestration package: production agenda, phase execution plans, checkpoints, and next-action recommendations.

Public API:
- schema.ProductionPhase, schema.ProductionAgenda
- schema.ExecutionStep, schema.PhaseChecklist
- schema.ProductionCheckpoint, schema.SessionStats
- agenda.get_agenda, agenda.AGENDA_CATALOG
"""

from .agenda import AGENDA_CATALOG, get_agenda

__all__ = ["AGENDA_CATALOG", "get_agenda"]
