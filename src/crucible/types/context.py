"""Validation context.

The public ``validate(spec, context)`` accepts a ``dict`` shaped like
``ValidationContext`` (the camelCase keys ``phase``/``activeEntityId``/
``config``/``returns`` are canonical; snake_case keys are also accepted and
normalized by ``validate``). ``PhaseContext`` is the internal, normalized
per-phase context.

Note on ``existingFiles`` (grep evidence): rather than carrying it on every
``PhaseContext``, crucible's phases take positional arguments and only build a
``PhaseContext`` for the guidance layer, so the value is threaded as an explicit
``existing_files`` parameter (``validate`` → dispatcher → phase →
``run_cross_validation`` → ``FileProvenanceContext``). It is deliberately NOT a
``PhaseContext`` field: it would never be populated there and would silently
read as ``None``.
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
    # Guidance language ("en" default; "pt-br"). Aliases such as "pt_BR"/"pt"
    # are normalized by ``validate``. Only the guidance layer's prose is
    # translated — findings, field paths, and operation names stay canonical.
    language: str
    # Grep evidence: the set of real-repo file paths, injected by the
    # caller so the file-provenance check can resolve pre-existing (brownfield)
    # files. ABSENT → strict spec-internal existence (``E = createdPaths``);
    # PRESENT (even empty) → ``E = existingFiles ∪ createdPaths``.
    existingFiles: frozenset[str] | set[str] | list[str]


@dataclass(frozen=True)
class PhaseContext:
    phase: SinglePhase
    config: ValidatorConfig
    active_entity_id: str | list[str] | None = None
    # Normalized guidance language (see ``crucible.i18n``).
    language: str = "en"
