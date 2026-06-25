"""Phase classification helpers (port of ``api/phase-classification.ts``)."""

from __future__ import annotations

from ..scoring.cascade import phase_includes_epics, phase_includes_tickets
from ..types.phase import ValidationPhase

_HUMAN_JUDGMENT_PHASES = {"epic_decomposition", "ticket_decomposition"}

__all__ = ["is_human_judgment_phase", "phase_includes_epics", "phase_includes_tickets"]


def is_human_judgment_phase(phase: ValidationPhase) -> bool:
    return phase != "all" and phase in _HUMAN_JUDGMENT_PHASES
