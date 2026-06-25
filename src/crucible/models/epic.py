"""Epic entity (port of ``spec-types/schema/epic.ts``)."""

from __future__ import annotations

from pydantic import Field

from ._base import Entity
from .auxiliary import AcceptanceCriterion, FieldDeclaration
from .enums import EpicCategory
from .planning import ApiContract, Goal, Scope, SharedPattern, StructureItem
from .ticket import Ticket


class Epic(Entity):
    id: str
    specification_id: str
    title: str
    description: str
    objective: str
    order: int | None = None
    estimated_minutes: int | None = None

    architecture: str | None = None
    scope: Scope | None = None

    goals: list[Goal] | None = None
    acceptance_criteria: list[AcceptanceCriterion] | None = None
    validation_commands: list[str] | None = None
    api_contracts: list[ApiContract] | None = None
    shared_patterns: list[SharedPattern] | None = None
    file_structures: list[StructureItem] | None = None

    requirements_covered: list[str] | None = None
    nfrs_covered: list[str] | None = None
    goals_covered: list[str] | None = None

    tickets: list[Ticket] = Field(default_factory=list)

    field_declarations: dict[str, FieldDeclaration] | None = None
    category: EpicCategory | None = None
