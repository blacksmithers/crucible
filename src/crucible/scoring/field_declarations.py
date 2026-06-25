"""N/A field declarations (port of ``scoring/field-declarations.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types.config import ValidatorConfig
from ..types.rubric import RubricEntry


def _field_key(field_path: str) -> str:
    dot = field_path.find(".")
    return field_path[dot + 1 :] if dot != -1 else field_path


def is_field_declared_na(entity: dict[str, Any], field_path: str) -> bool:
    decls = entity.get("fieldDeclarations")
    if not isinstance(decls, dict):
        return False
    decl = decls.get(_field_key(field_path))
    return isinstance(decl, dict) and decl.get("value") == "N/A"


@dataclass(frozen=True)
class NAValidationResult:
    valid: bool
    reason: (
        Literal["not-declared", "not-eligible", "reason-too-short", "reason-missing"] | None
    ) = None
    message: str | None = None


def validate_na_declaration(
    entity: dict[str, Any],
    field_path: str,
    rubric_entry: RubricEntry,
    config: ValidatorConfig,
) -> NAValidationResult:
    decls = entity.get("fieldDeclarations")
    decl = decls.get(_field_key(field_path)) if isinstance(decls, dict) else None

    if not isinstance(decl, dict) or decl.get("value") != "N/A":
        return NAValidationResult(valid=False, reason="not-declared")

    if not rubric_entry.na_eligible:
        return NAValidationResult(
            valid=False,
            reason="not-eligible",
            message=f'Field "{field_path}" cannot be declared N/A',
        )

    reason = decl.get("reason")
    if not reason:
        return NAValidationResult(
            valid=False,
            reason="reason-missing",
            message=f'N/A declaration for "{field_path}" requires a reason',
        )

    min_length = config["naReason"]["minLength"]
    if len(reason) < min_length:
        return NAValidationResult(
            valid=False,
            reason="reason-too-short",
            message=(
                f'N/A declaration for "{field_path}" requires reason of at least '
                f"{min_length} chars"
            ),
        )

    return NAValidationResult(valid=True)
