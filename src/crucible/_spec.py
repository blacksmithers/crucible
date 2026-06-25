"""Spec input normalization.

The engine works on a camelCase ``dict`` (mirroring the TS value-resolver and
the JSON seeds). ``validate()`` and ``validate_structural()`` accept either a
:class:`crucible.models.Specification` or a plain mapping; both normalize here.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

SpecInput = BaseModel | dict[str, Any]


def to_spec_dict(spec: SpecInput) -> dict[str, Any]:
    if isinstance(spec, BaseModel):
        return spec.model_dump(mode="json", by_alias=True, exclude_none=True)
    return dict(spec)
