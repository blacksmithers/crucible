"""Ticket entity (port of ``spec-types/schema/ticket.ts``)."""

from __future__ import annotations

from pydantic import Field

from ._base import Entity
from .auxiliary import (
    AcceptanceCriterion,
    BlueprintReference,
    CodeReference,
    CodeSnippet,
    DependencyLink,
    FieldDeclaration,
    ImplementationStep,
    TestSpecification,
    TypeReference,
    TypeSnippet,
)
from .enums import Complexity, TicketType


class Ticket(Entity):
    id: str
    epic_id: str
    ticket_number: int | None = None
    title: str
    description: str | None = None

    ticket_type: TicketType
    complexity: Complexity
    estimated_minutes: int = 0
    order: int | None = None

    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    implementation_steps: list[ImplementationStep] = Field(default_factory=list)
    files_to_be_created: list[str] = Field(default_factory=list)
    files_to_be_modified: list[str] = Field(default_factory=list)
    files_to_be_deleted: list[str] = Field(default_factory=list)
    files_to_be_referenced: list[str] = Field(default_factory=list)

    test_specification: TestSpecification | None = None

    guardrails: list[str] = Field(default_factory=list)
    code_references: list[CodeReference] = Field(default_factory=list)
    type_references: list[TypeReference] = Field(default_factory=list)
    code_snippets: list[CodeSnippet] | None = None
    type_snippets: list[TypeSnippet] | None = None
    blueprint_references: list[BlueprintReference] = Field(default_factory=list)

    dependencies: list[DependencyLink] = Field(default_factory=list)

    field_declarations: dict[str, FieldDeclaration] | None = None
