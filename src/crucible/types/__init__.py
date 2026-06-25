"""Validator type contracts (port of ``@specforge/validator`` ``src/types``)."""

from __future__ import annotations

from .cascade import CascadeFailure, CascadeFloors
from .config import (
    ConfigComplexity,
    PerComplexityCounts,
    ScoringWeights,
    ThresholdEntry,
    ValidatorConfig,
)
from .context import PhaseContext, ValidationContext
from .enums import (
    ActionVerb,
    CompositePatternId,
    EntityType,
    FindingStatus,
    Severity,
    Tier,
)
from .finding import CompositeFinding, Finding, ThresholdContext
from .guidance import (
    GuidanceCrossValidationEntry,
    GuidanceEntry,
    GuidanceMessage,
    GuidanceResult,
)
from .operations import OPERATION_NAMES, OperationName, is_operation_name
from .phase import (
    RETURN_LAYERS,
    SINGLE_PHASES,
    VALIDATION_PHASES,
    ReturnLayer,
    SinglePhase,
    ValidationPhase,
)
from .result import (
    CrossValidationEmission,
    CrossValidationFinding,
    CrossValidationResult,
    GlobalScoreBreakdown,
    InvalidField,
    PerFieldScore,
    ScoringResult,
    ScoringResultActive,
    ScoringResultSkipped,
    SkippedCheck,
    StructuralFinding,
    StructuralResult,
    ValidationResult,
    ValidationResultAll,
    ValidationResultAllMeta,
    ValidationResultMeta,
)
from .rubric import ConditionalApplicability, RubricEntry, StructuralCheck
from .scope import EntityScope, ResponseDetail

__all__ = [
    "OPERATION_NAMES",
    "RETURN_LAYERS",
    "SINGLE_PHASES",
    "VALIDATION_PHASES",
    "ActionVerb",
    "CascadeFailure",
    "CascadeFloors",
    "CompositeFinding",
    "CompositePatternId",
    "ConditionalApplicability",
    "ConfigComplexity",
    "CrossValidationEmission",
    "CrossValidationFinding",
    "CrossValidationResult",
    "EntityScope",
    "EntityType",
    "Finding",
    "FindingStatus",
    "GlobalScoreBreakdown",
    "GuidanceCrossValidationEntry",
    "GuidanceEntry",
    "GuidanceMessage",
    "GuidanceResult",
    "InvalidField",
    "OperationName",
    "PerComplexityCounts",
    "PerFieldScore",
    "PhaseContext",
    "ResponseDetail",
    "ReturnLayer",
    "RubricEntry",
    "ScoringResult",
    "ScoringResultActive",
    "ScoringResultSkipped",
    "ScoringWeights",
    "Severity",
    "SinglePhase",
    "SkippedCheck",
    "StructuralCheck",
    "StructuralFinding",
    "StructuralResult",
    "ThresholdContext",
    "ThresholdEntry",
    "Tier",
    "ValidationContext",
    "ValidationPhase",
    "ValidationResult",
    "ValidationResultAll",
    "ValidationResultAllMeta",
    "ValidationResultMeta",
    "ValidatorConfig",
    "is_operation_name",
]
