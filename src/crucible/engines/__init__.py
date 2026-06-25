"""Computation engines (port of ``@specforge/validator`` ``src/engines``)."""

from __future__ import annotations

from .wave_calculator import (
    WaveAssignment,
    WaveCalculationResult,
    compute_waves,
    tickets_by_wave,
)

__all__ = [
    "WaveAssignment",
    "WaveCalculationResult",
    "compute_waves",
    "tickets_by_wave",
]
