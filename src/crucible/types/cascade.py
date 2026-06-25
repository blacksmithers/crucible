"""Cascade floor/failure contracts (port of ``types/cascade.ts``)."""

from __future__ import annotations

from typing import Literal

from ._base import CamelModel


class CascadeFloors(CamelModel):
    spec_only: float
    spec_plus_epics: float
    total: float


class CascadeFailure(CamelModel):
    level: Literal["specOnly", "specPlusEpics", "total"]
    expected: float
    actual: float
    message: str
