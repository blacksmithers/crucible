"""Cross-validation emission (finding + per-finding guidance prose)."""

from __future__ import annotations

from dataclasses import dataclass

from ..types.result import CrossValidationFinding


@dataclass(frozen=True)
class CVEmission:
    finding: CrossValidationFinding
    guidance: str
