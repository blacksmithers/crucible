"""Shared Pydantic base for validator *output* contracts.

Output models use snake_case attributes with auto camelCase aliases. They are
serialized to the canonical camelCase JSON via::

    model.model_dump(mode="json", by_alias=True, exclude_unset=True)

``exclude_unset`` is the key to the JSON serialization contract: it **omits**
fields the engine never set but **keeps ``null``** for fields the engine
explicitly assigned ``None``.
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
        """Canonical camelCase JSON dict (JSON serialization semantics)."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)
