"""Specification entity (port of ``spec-types/schema/specification.ts``)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ._base import Entity
from .auxiliary import AcceptanceCriterion, FieldDeclaration
from .blueprint import Blueprint
from .epic import Epic
from .planning import (
    EpicTargets,
    Goal,
    Guardrail,
    NonFunctionalRequirement,
    Requirement,
    Scope,
    SharedPattern,
    StructureItem,
    TechStackItem,
)


class Specification(Entity):
    schema_version: Literal["1.1"] = "1.1"
    id: str
    project_id: str
    title: str
    description: str | None = None

    # Loose at the public schema level — products can narrow.
    status: str

    # Critical structured fields
    goals: list[Goal] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    architecture: str = ""
    scope: Scope = Field(default_factory=Scope)

    # Recommended structured fields
    tech_stack: list[TechStackItem] = Field(default_factory=list)
    folder_structures: list[StructureItem] = Field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(default_factory=list)
    shared_patterns: list[SharedPattern] | None = None
    guardrails: list[Guardrail] = Field(default_factory=list)

    # Enrichment (loose)
    background: str | None = None

    # Children
    epics: list[Epic] = Field(default_factory=list)
    blueprints: list[Blueprint] = Field(default_factory=list)

    field_declarations: dict[str, FieldDeclaration] | None = None
    epic_targets: EpicTargets | None = None
    estimated_minutes: int | None = None
