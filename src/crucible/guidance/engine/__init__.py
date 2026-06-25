"""Guidance engine internals (applicability + threshold resolution)."""

from __future__ import annotations

from .applicability import is_applicable, is_config_applicable
from .resolver import resolve_source, resolve_threshold

__all__ = [
    "is_applicable",
    "is_config_applicable",
    "resolve_source",
    "resolve_threshold",
]
