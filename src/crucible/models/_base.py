"""Shared Pydantic base for OpenSpec entity models.

Entity models are *lenient* input structures: snake_case attributes with
auto-generated camelCase aliases, `populate_by_name` so both forms construct,
and `extra="allow"` so unknown/runtime fields in seeds pass through untouched.

They deliberately carry **no** min-count / min-length constraints — the
validator engine is what reports deficiencies, so a sparse spec must still
load in order to be scored.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Entity(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )
