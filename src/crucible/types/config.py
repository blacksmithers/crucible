"""Validator configuration types (port of ``types/config.ts``).

The runtime config is a plain nested ``dict`` mirroring the TS object literal
(see ``crucible/config/defaults.py``). The resolver reads it by string path,
so deeply-nested loose sections (``structuralRequirements``) stay ``Any`` here
rather than being over-modelled. The well-defined leaf types that surface in
*output* (notably ``ScoringWeights``) are typed precisely.
"""

from __future__ import annotations

from typing import Any, Literal

from typing_extensions import TypedDict

# Ticket complexity buckets (config-level mirror of models.Complexity).
ConfigComplexity = Literal["small", "medium", "large", "xlarge"]


class ScoringWeights(TypedDict):
    spec: float
    epics: float
    tickets: float


class ThresholdEntry(TypedDict):
    default: float
    min: float
    max: float


PerComplexityCounts = dict[ConfigComplexity, float]

# The full validator config object. Kept as a loose mapping: the engine and
# resolver access it by string key, exactly as the TS object literal is read.
ValidatorConfig = dict[str, Any]
