"""Planning sub-entities (port of ``spec-types/schema/planning/*.ts``)."""

from __future__ import annotations

from pydantic import Field

from ._base import Entity
from .auxiliary import AcceptanceCriterion, BlueprintReference
from .enums import (
    ApiContractType,
    GoalType,
    GuardrailCategory,
    GuardrailScope,
    NfrCategory,
    RequirementType,
    TechLayer,
)


class Goal(Entity):
    id: str
    title: str
    description: str
    type: GoalType
    success_criteria: list[str] = Field(default_factory=list)
    kpi: str | None = None


class Requirement(Entity):
    id: str
    title: str
    description: str
    type: RequirementType
    source: str | None = None
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    depends_on: list[str] | None = None
    constraints: list[str] | None = None


class NonFunctionalRequirement(Entity):
    id: str
    description: str
    category: NfrCategory
    metric: str
    target: str
    measurement_method: str | None = None


class Guardrail(Entity):
    id: str
    description: str
    category: GuardrailCategory
    rationale: str
    consequence: str
    scope: GuardrailScope | None = None


class Scope(Entity):
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    assumptions: list[str] | None = None
    external_dependencies: list[str] | None = None


class TechStackItem(Entity):
    id: str
    name: str
    version: str | None = None
    layer: TechLayer
    rationale: str | None = None
    alternatives_considered: list[str] | None = None


class ApiContract(Entity):
    id: str
    name: str
    type: ApiContractType
    description: str | None = None
    blueprint_references: list[BlueprintReference] | None = None


class SharedPattern(Entity):
    id: str
    name: str
    description: str
    code_standards: dict[str, str] | None = None
    common_imports: list[str] | None = None
    return_types: dict[str, str] | None = None
    additional_imports: list[str] | None = None
    common_files: dict[str, str] | None = None


class StructureItem(Entity):
    id: str
    scope: str
    description: str | None = None
    content: str


class EpicTargets(Entity):
    foundation: int
    functional: int
    non_functional: int
    verification: int
