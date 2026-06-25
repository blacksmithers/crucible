"""Rubric entry + structural check contracts (port of ``types/rubric.ts``).

These are static, internal config data (the 53 rubric entries are authored in
``crucible/guidance/rubric/``) and never serialized to output, so they are
frozen dataclasses rather than Pydantic models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .enums import ActionVerb, Tier
from .operations import OperationName
from .phase import ValidationPhase


@dataclass(frozen=True)
class StructuralCheck:
    type: str  # 'minLength' | 'minCount' | 'present' | 'enumMember' | 'pattern' | <named quality check>
    param: Any = None
    source: str | None = None  # 'config:<dot.path>' — resolves from ValidatorConfig
    applies_to: Literal["field", "items"] | None = None  # for minLength


@dataclass(frozen=True)
class ConditionalApplicability:
    field: str
    equals: Any


@dataclass(frozen=True)
class RubricEntry:
    id: str
    field_path: str
    curriculum_phase: ValidationPhase
    curriculum_step: int
    tier: Tier
    structural_checks: list[StructuralCheck]
    na_eligible: bool
    primary_verbs: list[ActionVerb]
    curriculum_prompt: str
    available_operations: list[OperationName]
    prerequisite: str | None = None
    conditional_applicability: ConditionalApplicability | None = None
    applicability_check: Literal["enforceTypes"] | None = None
    na_without_reason_prompt: str | None = None
    composes_with: list[str] | None = field(default=None)
