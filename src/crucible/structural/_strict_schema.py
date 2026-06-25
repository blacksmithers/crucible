"""Strict OpenSpec v1.1 schema for ``check_format`` (mirror of the Zod schemas).

Unlike :mod:`crucible.models` (lenient input structures), these models carry the
**constraints** from ``@specforge/spec-types`` (min array lengths, min string
lengths, enums, ranges) so that validating a spec reproduces the same set of
schema violations the TS ``SpecificationSchema.safeParse`` produces.

Fields are camelCase (matching the JSON seeds) so Pydantic error ``loc`` paths
line up with the Zod issue paths. ``extra="ignore"`` mirrors Zod's default
unknown-key stripping. Field order mirrors the TS schemas so multi-error
ordering matches.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import (
    ApiContractType,
    BlueprintCategory,
    BlueprintCoverageType,
    BlueprintFormat,
    Complexity,
    DependencyType,
    EpicCategory,
    GoalType,
    GuardrailCategory,
    GuardrailScope,
    NfrCategory,
    RequirementType,
    TechLayer,
    TestType,
    TicketType,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="ignore")


class FieldDeclarationStrict(_Strict):
    value: Literal["N/A"]
    reason: str = Field(min_length=20)


class AcceptanceCriterionStrict(_Strict):
    id: str
    given: str
    when: str
    then: str
    order: int = Field(ge=1)


class ImplementationStepStrict(_Strict):
    id: str
    text: str
    order: int = Field(ge=1)


class TestSpecificationStrict(_Strict):
    testTypes: list[TestType] = Field(min_length=1)
    qualityGates: list[NonEmptyStr] = Field(min_length=1)
    testCommands: list[str]
    coverageTarget: float | None = Field(default=None, ge=0, le=100)


class CodeReferenceStrict(_Strict):
    filePath: str
    symbol: str | None = None
    description: str | None = None


class TypeReferenceStrict(_Strict):
    filePath: str
    typeName: str
    description: str | None = None


class CodeSnippetStrict(_Strict):
    id: str
    language: str
    description: str | None = None
    content: str


class TypeSnippetStrict(_Strict):
    id: str
    language: str
    description: str | None = None
    content: str


class BlueprintReferenceStrict(_Strict):
    blueprintId: str
    context: str | None = None
    section: str | None = None


class DependencyLinkStrict(_Strict):
    ticketId: str
    type: DependencyType


class GoalStrict(_Strict):
    id: str
    title: NonEmptyStr
    description: NonEmptyStr
    type: GoalType
    successCriteria: list[NonEmptyStr] = Field(min_length=1)
    kpi: str | None = None


class RequirementStrict(_Strict):
    id: str
    title: NonEmptyStr
    description: NonEmptyStr
    type: RequirementType
    source: str | None = None
    acceptanceCriteria: list[AcceptanceCriterionStrict] = Field(min_length=1)
    dependsOn: list[str] | None = None
    constraints: list[str] | None = None


class NonFunctionalRequirementStrict(_Strict):
    id: str
    description: NonEmptyStr
    category: NfrCategory
    metric: NonEmptyStr
    target: NonEmptyStr
    measurementMethod: str | None = None


class GuardrailStrict(_Strict):
    id: str
    description: NonEmptyStr
    category: GuardrailCategory
    rationale: NonEmptyStr
    consequence: NonEmptyStr
    scope: GuardrailScope | None = None


class ScopeStrict(_Strict):
    inScope: list[NonEmptyStr] = Field(min_length=3)
    outOfScope: list[NonEmptyStr] = Field(min_length=1)
    assumptions: list[str] | None = None
    externalDependencies: list[str] | None = None


class TechStackItemStrict(_Strict):
    id: str
    name: NonEmptyStr
    version: str | None = None
    layer: TechLayer
    rationale: str | None = None
    alternativesConsidered: list[str] | None = None


class ApiContractStrict(_Strict):
    id: str
    name: NonEmptyStr
    type: ApiContractType
    description: str | None = None
    blueprintReferences: list[BlueprintReferenceStrict] | None = None


class SharedPatternStrict(_Strict):
    id: str
    name: NonEmptyStr
    description: NonEmptyStr
    codeStandards: dict[str, Any] | None = None
    commonImports: list[str] | None = None
    returnTypes: dict[str, str] | None = None
    additionalImports: list[str] | None = None
    commonFiles: dict[str, str] | None = None


class StructureItemStrict(_Strict):
    id: str
    scope: NonEmptyStr
    description: str | None = None
    content: NonEmptyStr


class EpicTargetsStrict(_Strict):
    foundation: int = Field(ge=0)
    functional: int = Field(ge=0)
    nonFunctional: int = Field(ge=0)
    verification: int = Field(ge=0)


class BlueprintStrict(_Strict):
    id: str
    title: NonEmptyStr
    description: str | None = None
    slug: str | None = None
    category: BlueprintCategory
    format: BlueprintFormat | None = None
    coverageType: BlueprintCoverageType = BlueprintCoverageType.TICKET
    content: str
    notes: str | None = None
    version: str | None = None
    order: int | None = None
    tags: list[str] | None = None


class TicketStrict(_Strict):
    id: str
    epicId: str
    ticketNumber: int | None = Field(default=None, gt=0)
    title: NonEmptyStr
    description: str | None = None
    ticketType: TicketType
    complexity: Complexity
    estimatedMinutes: int = Field(ge=0)
    order: int | None = None
    acceptanceCriteria: list[AcceptanceCriterionStrict]
    implementationSteps: list[ImplementationStepStrict]
    filesToBeCreated: list[str]
    filesToBeModified: list[str]
    filesToBeDeleted: list[str]
    filesToBeReferenced: list[str]
    testSpecification: TestSpecificationStrict | None = None
    guardrails: list[str]
    codeReferences: list[CodeReferenceStrict]
    typeReferences: list[TypeReferenceStrict]
    codeSnippets: list[CodeSnippetStrict] | None = None
    typeSnippets: list[TypeSnippetStrict] | None = None
    blueprintReferences: list[BlueprintReferenceStrict]
    dependencies: list[DependencyLinkStrict]
    fieldDeclarations: dict[str, FieldDeclarationStrict] | None = None


class EpicStrict(_Strict):
    id: str
    specificationId: str
    title: NonEmptyStr
    description: str
    objective: str
    order: int | None = None
    estimatedMinutes: int | None = None
    architecture: str | None = None
    scope: ScopeStrict | None = None
    goals: list[GoalStrict] | None = None
    acceptanceCriteria: list[AcceptanceCriterionStrict] | None = None
    validationCommands: list[str] | None = None
    apiContracts: list[ApiContractStrict] | None = None
    sharedPatterns: list[SharedPatternStrict] | None = None
    fileStructures: list[StructureItemStrict] | None = None
    requirementsCovered: list[str] | None = None
    nfrsCovered: list[str] | None = None
    goalsCovered: list[str] | None = None
    tickets: list[TicketStrict]
    fieldDeclarations: dict[str, FieldDeclarationStrict] | None = None
    category: EpicCategory | None = None


class SpecificationStrict(_Strict):
    schemaVersion: Literal["1.1"]
    id: str
    projectId: str
    title: NonEmptyStr
    description: str | None = None
    status: str
    goals: list[GoalStrict] = Field(min_length=3)
    requirements: list[RequirementStrict] = Field(min_length=3)
    architecture: str
    scope: ScopeStrict
    techStack: list[TechStackItemStrict]
    folderStructures: list[StructureItemStrict] = Field(min_length=1)
    acceptanceCriteria: list[AcceptanceCriterionStrict]
    nonFunctionalRequirements: list[NonFunctionalRequirementStrict]
    sharedPatterns: list[SharedPatternStrict] | None = None
    guardrails: list[GuardrailStrict]
    background: str | None = None
    epics: list[EpicStrict]
    blueprints: list[BlueprintStrict]
    fieldDeclarations: dict[str, FieldDeclarationStrict] | None = None
    epicTargets: EpicTargetsStrict | None = None
    estimatedMinutes: int | None = None
