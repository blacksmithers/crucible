"""Phase-specific gate checks (port of ``@specforge/validator`` ``src/checks``)."""

from __future__ import annotations

from .coverage import validate_nfr_coverage, validate_requirement_coverage
from .na_validation import validate_na_epic, validate_na_spec, validate_na_ticket

__all__ = [
    "validate_na_epic",
    "validate_na_spec",
    "validate_na_ticket",
    "validate_nfr_coverage",
    "validate_requirement_coverage",
]
