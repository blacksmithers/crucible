"""Validation context (port of ``types/context.ts``).

The public ``validate(spec, context)`` accepts a ``dict`` shaped like
``ValidationContext`` (original TS keys ``phase``/``activeEntityId``/``config``/
``returns`` are canonical; snake_case keys are also accepted and normalized by
``validate``). ``PhaseContext`` is the internal, normalized per-phase context.
"""

from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import TypedDict

from .config import ValidatorConfig
from .phase import ReturnLayer, SinglePhase, ValidationPhase


class ValidationContext(TypedDict, total=False):
    phase: ValidationPhase
    activeEntityId: str | list[str]
    config: ValidatorConfig
    returns: list[ReturnLayer]


@dataclass(frozen=True)
class PhaseContext:
    phase: SinglePhase
    config: ValidatorConfig
    active_entity_id: str | list[str] | None = None
