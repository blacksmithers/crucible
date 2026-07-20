"""Validation context (port of ``types/context.ts``).

The public ``validate(spec, context)`` accepts a ``dict`` shaped like
``ValidationContext`` (original TS keys ``phase``/``activeEntityId``/``config``/
``returns`` are canonical; snake_case keys are also accepted and normalized by
``validate``). ``PhaseContext`` is the internal, normalized per-phase context.

Note on ``existingFiles`` (MB.10.5 grep evidence): the TS carries it on its
``PhaseContext``, because there every phase receives that object. Crucible's
phases take positional arguments instead and only build a ``PhaseContext`` for
the guidance layer, so the value is threaded as an explicit ``existing_files``
parameter (``validate`` → dispatcher → phase → ``run_cross_validation`` →
``FileProvenanceContext``). It is deliberately NOT a ``PhaseContext`` field: it
would never be populated there and would silently read as ``None``.
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
    # MB.10.5 grep evidence: the set of real-repo file paths, injected by the
    # caller so the file-provenance check can resolve pre-existing (brownfield)
    # files. ABSENT → strict spec-internal existence (``E = createdPaths``);
    # PRESENT (even empty) → ``E = existingFiles ∪ createdPaths``.
    existingFiles: frozenset[str] | set[str] | list[str]


@dataclass(frozen=True)
class PhaseContext:
    phase: SinglePhase
    config: ValidatorConfig
    active_entity_id: str | list[str] | None = None
