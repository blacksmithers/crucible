"""Shared Pydantic base for validator *output* contracts.

Output models use snake_case attributes with auto camelCase aliases. They are
serialized for the differential harness via::

    model.model_dump(mode="json", by_alias=True, exclude_unset=True)

``exclude_unset`` is the key to fidelity: it mirrors ``JSON.stringify`` in the
TS engine, which **omits ``undefined``** (fields the engine never set) but
**keeps ``null``** (fields the engine explicitly assigned ``None``).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    def to_json_dict(self) -> dict[str, Any]:
        """Canonical camelCase JSON dict (TS ``JSON.stringify`` semantics)."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)
