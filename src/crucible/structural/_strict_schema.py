"""Strict OpenSpec v1.1 schema for ``check_format`` (mirror of the Zod schemas).

Unlike :mod:`crucible.models` (lenient input structures), these models carry the
**constraints** from ``@specforge/spec-types`` (min array lengths, min string
lengths, enums, ranges, numeric types) so that validating a spec reproduces the
same set of schema violations the TS ``SpecificationSchema.safeParse`` produces.

Fields are camelCase (matching the JSON seeds) so Pydantic error ``loc`` paths
line up with the Zod issue paths. ``extra="ignore"`` mirrors Zod's default
unknown-key stripping. Field order mirrors the TS schemas so multi-error
ordering matches.

Faithful-port notes on Zod semantics (all reproduced here):

* ``z.string()`` / ``z.number()`` / ``z.number().int()`` do NOT coerce — a
  numeric string, a boolean, or ``null`` is rejected, not converted. Pydantic's
  default (lax) mode coerces all of these, which flipped ``passed`` false→true.
  So scalars are ``Strict``-annotated (:data:`_Str` / :data:`_Int` / :data:`_Num`).
* ``.optional()`` accepts a MISSING key but REJECTS an explicit ``null``;
  ``.nullish()`` accepts both. Rendering every optional as ``X | None`` erased
  that distinction (``null`` passed where the reference fails). Here a
  ``.optional()`` field is a non-``None`` type with ``Field(default=None)`` — the
  default covers "absent", and an explicit ``null`` fails type validation. Only
  the three genuine ``.nullish()`` fields (``coverageTarget``, blueprint-ref
  ``context``/``section``) keep ``| None``.
* Zod ``.min(n)`` on a string counts UTF-16 code units; :func:`_zstr` measures
  the same way (see :mod:`crucible._utf16`).

One documented micro-divergence remains: a float that is integer-valued
(JSON ``2.0``) satisfies ``z.number().int()`` in JS — ``Number.isInteger(2.0)``
is true — but Pydantic strict ``int`` rejects it. Real producers emit ``2`` for
integer fields, never ``2.0``, so this is inert in practice.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.types import Strict
from pydantic_core import PydanticCustomError

from .._utf16 import utf16_len
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

# --- Zod-faithful scalar types -------------------------------------------------
# Strict (no coercion): a numeric string / boolean / null is rejected, matching
# z.string() / z.number() / z.number().int(). `_Num` is a float that still accepts
# an int (as z.number() does), because Pydantic's float keeps that one lax rule.
_Str = Annotated[str, Strict()]
_Int = Annotated[int, Strict()]
_Num = Annotated[float, Strict()]


def _min_len_check(min_length: int) -> AfterValidator:
    def check(v: str) -> str:
        if utf16_len(v) < min_length:
            raise PydanticCustomError(
                "string_too_short",
                "String must contain at least {min_length} character(s)",
                {"min_length": min_length},
            )
        return v

    return AfterValidator(check)


# z.string().min(N), UTF-16 counted. Declared as Annotated literals (not via a
# helper call) so they read as type aliases to the checker. min-1 never diverges
# from code points, but stays on the same mechanism for consistency; min-20 is
# the only string length that can UTF-16-diverge (an N/A reason of astral chars).
NonEmptyStr = Annotated[str, Strict(), _min_len_check(1)]
_Reason = Annotated[str, Strict(), _min_len_check(20)]


# `.optional()` sentinel: a non-None-typed field with `default=None`. Absent →
# default (unread); explicit null → rejected by the type. A FRESH FieldInfo per
# field (Pydantic v2 mutates FieldInfo during model build, so never share one).
# Both helpers return Any, so the non-Optional annotation type-checks.
def _opt() -> Any:
    return Field(default=None)


def _opt_num(**bounds: Any) -> Any:
    """A null-rejecting optional number field carrying its range bounds."""
    return Field(default=None, **bounds)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="ignore")


class FieldDeclarationStrict(_Strict):
    value: Literal["N/A"]
    reason: _Reason


class AcceptanceCriterionStrict(_Strict):
    id: _Str
    given: _Str
    when: _Str
    then: _Str
    order: _Int = Field(ge=1)


class ImplementationStepStrict(_Strict):
    id: _Str
    text: _Str
    order: _Int = Field(ge=1)


class TestSpecificationStrict(_Strict):
    # SHAPE-only: element types are validated here, but the CONTENT minimums
    # (testTypes/qualityGates >= 1) are NOT — they are a ticket_expansion,
    # verification-ticket-only RUBRIC concern. Relaxed upstream before the 0.1.20
    # baseline; the port carried the pre-fix constraint until 0.3.0.
    testTypes: list[TestType]
    qualityGates: list[_Str]
    testCommands: list[_Str]
    # z.number().min(0).max(100).nullish() — null accepted.
    coverageTarget: _Num | None = Field(default=None, ge=0, le=100)


class CodeReferenceStrict(_Strict):
    filePath: _Str
    symbol: _Str = _opt()
    description: _Str = _opt()


class TypeReferenceStrict(_Strict):
    filePath: _Str
    typeName: _Str
    description: _Str = _opt()


class CodeSnippetStrict(_Strict):
    id: _Str
    language: _Str
    description: _Str = _opt()
    content: _Str
    order: _Int = _opt_num(ge=0)


class TypeSnippetStrict(_Strict):
    id: _Str
    language: _Str
    description: _Str = _opt()
    content: _Str
    order: _Int = _opt_num(ge=0)


class BlueprintReferenceStrict(_Strict):
    blueprintId: _Str
    # z.string().nullish() — null accepted (MB.9: link_blueprint_to_tickets sets
    # only blueprintId; AppSync returns context/section as null).
    context: _Str | None = None
    section: _Str | None = None


class DependencyLinkStrict(_Strict):
    ticketId: _Str
    type: DependencyType


class GoalStrict(_Strict):
    id: _Str
    title: NonEmptyStr
    description: NonEmptyStr
    type: GoalType
    successCriteria: list[NonEmptyStr] = Field(min_length=1)
    kpi: _Str = _opt()


class RequirementStrict(_Strict):
    id: _Str
    title: NonEmptyStr
    description: NonEmptyStr
    type: RequirementType
    source: _Str = _opt()
    acceptanceCriteria: list[AcceptanceCriterionStrict] = Field(min_length=1)
    dependsOn: list[_Str] = _opt()
    constraints: list[_Str] = _opt()


class NonFunctionalRequirementStrict(_Strict):
    id: _Str
    description: NonEmptyStr
    category: NfrCategory
    metric: NonEmptyStr
    target: NonEmptyStr
    measurementMethod: _Str = _opt()


class GuardrailStrict(_Strict):
    id: _Str
    description: NonEmptyStr
    category: GuardrailCategory
    rationale: NonEmptyStr
    consequence: NonEmptyStr
    scope: GuardrailScope = _opt()


class ScopeStrict(_Strict):
    inScope: list[NonEmptyStr] = Field(min_length=3)
    outOfScope: list[NonEmptyStr] = Field(min_length=1)
    assumptions: list[_Str] = _opt()
    externalDependencies: list[_Str] = _opt()


class TechStackItemStrict(_Strict):
    id: _Str
    name: NonEmptyStr
    version: _Str = _opt()
    layer: TechLayer
    rationale: _Str = _opt()
    alternativesConsidered: list[_Str] = _opt()


class ApiContractStrict(_Strict):
    id: _Str
    name: NonEmptyStr
    type: ApiContractType
    description: _Str = _opt()
    blueprintReferences: list[BlueprintReferenceStrict] = _opt()


class SharedPatternStrict(_Strict):
    id: _Str
    name: NonEmptyStr
    description: NonEmptyStr
    codeStandards: dict[str, Any] = _opt()
    commonImports: list[_Str] = _opt()
    returnTypes: dict[str, _Str] = _opt()
    additionalImports: list[_Str] = _opt()
    commonFiles: dict[str, _Str] = _opt()


class StructureItemStrict(_Strict):
    id: _Str
    scope: NonEmptyStr
    description: _Str = _opt()
    content: NonEmptyStr


class EpicTargetsStrict(_Strict):
    foundation: _Int = Field(ge=0)
    functional: _Int = Field(ge=0)
    nonFunctional: _Int = Field(ge=0)
    verification: _Int = Field(ge=0)


class BlueprintStrict(_Strict):
    id: _Str
    title: NonEmptyStr
    description: _Str = _opt()
    slug: _Str = _opt()
    category: BlueprintCategory
    format: BlueprintFormat = _opt()
    coverageType: BlueprintCoverageType = BlueprintCoverageType.TICKET
    content: _Str
    notes: _Str = _opt()
    version: _Str = _opt()
    order: _Int = _opt_num(ge=0)
    tags: list[_Str] = _opt()


class TicketStrict(_Strict):
    id: _Str
    epicId: _Str
    ticketNumber: _Int = _opt_num(gt=0)
    title: NonEmptyStr
    description: _Str = _opt()
    ticketType: TicketType
    complexity: Complexity
    estimatedMinutes: _Int = Field(ge=0)
    order: _Int = _opt_num(ge=0)
    tags: list[_Str] = _opt()
    acceptanceCriteria: list[AcceptanceCriterionStrict]
    implementationSteps: list[ImplementationStepStrict]
    filesToBeCreated: list[_Str]
    filesToBeModified: list[_Str]
    filesToBeDeleted: list[_Str]
    filesToBeReferenced: list[_Str]
    testSpecification: TestSpecificationStrict = _opt()
    guardrails: list[_Str]
    codeReferences: list[CodeReferenceStrict]
    typeReferences: list[TypeReferenceStrict]
    codeSnippets: list[CodeSnippetStrict] = _opt()
    typeSnippets: list[TypeSnippetStrict] = _opt()
    blueprintReferences: list[BlueprintReferenceStrict]
    dependencies: list[DependencyLinkStrict]
    fieldDeclarations: dict[str, FieldDeclarationStrict] = _opt()


class EpicStrict(_Strict):
    id: _Str
    specificationId: _Str
    title: NonEmptyStr
    description: _Str
    objective: _Str
    order: _Int = _opt_num(ge=0)
    estimatedMinutes: _Int = _opt_num(ge=0)
    architecture: _Str = _opt()
    scope: ScopeStrict = _opt()
    goals: list[GoalStrict] = _opt()
    acceptanceCriteria: list[AcceptanceCriterionStrict] = _opt()
    validationCommands: list[_Str] = _opt()
    apiContracts: list[ApiContractStrict] = _opt()
    sharedPatterns: list[SharedPatternStrict] = _opt()
    fileStructures: list[StructureItemStrict] = _opt()
    requirementsCovered: list[_Str] = _opt()
    nfrsCovered: list[_Str] = _opt()
    goalsCovered: list[_Str] = _opt()
    tickets: list[TicketStrict]
    fieldDeclarations: dict[str, FieldDeclarationStrict] = _opt()
    category: EpicCategory = _opt()


class SpecificationStrict(_Strict):
    schemaVersion: Literal["1.1"]
    id: _Str
    projectId: _Str
    title: NonEmptyStr
    description: _Str = _opt()
    status: _Str
    goals: list[GoalStrict] = Field(min_length=3)
    requirements: list[RequirementStrict] = Field(min_length=3)
    architecture: _Str
    scope: ScopeStrict
    techStack: list[TechStackItemStrict]
    folderStructures: list[StructureItemStrict] = Field(min_length=1)
    acceptanceCriteria: list[AcceptanceCriterionStrict]
    nonFunctionalRequirements: list[NonFunctionalRequirementStrict]
    sharedPatterns: list[SharedPatternStrict] = _opt()
    guardrails: list[GuardrailStrict]
    background: _Str = _opt()
    epics: list[EpicStrict]
    blueprints: list[BlueprintStrict]
    fieldDeclarations: dict[str, FieldDeclarationStrict] = _opt()
    epicTargets: EpicTargetsStrict = _opt()
    estimatedMinutes: _Int = _opt_num(ge=0)
