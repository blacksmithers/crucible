"""Auxiliary OpenSpec sub-entities (port of ``spec-types/schema/auxiliary.ts``)."""

from __future__ import annotations

from pydantic import Field

from ._base import Entity
from .enums import DependencyType, TestType


class FieldDeclaration(Entity):
    value: str = "N/A"
    reason: str


class AcceptanceCriterion(Entity):
    id: str
    given: str
    when: str
    then: str
    order: int


class ImplementationStep(Entity):
    id: str
    text: str
    order: int


class TestSpecification(Entity):
    test_types: list[TestType] = Field(default_factory=list)
    quality_gates: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    coverage_target: float | None = None


class CodeReference(Entity):
    file_path: str
    symbol: str | None = None
    description: str | None = None


class TypeReference(Entity):
    file_path: str
    type_name: str
    description: str | None = None


class CodeSnippet(Entity):
    id: str
    language: str
    description: str | None = None
    content: str


class TypeSnippet(Entity):
    id: str
    language: str
    description: str | None = None
    content: str


class BlueprintReference(Entity):
    blueprint_id: str
    context: str | None = None
    section: str | None = None


class DependencyLink(Entity):
    ticket_id: str
    type: DependencyType
