"""Schema version resolution (port of ``structural/version-resolver.ts``)."""

from __future__ import annotations

from ._strict_schema import SpecificationStrict

_SCHEMAS = {"1.1": SpecificationStrict}


def resolve_schema(schema_version: str) -> type[SpecificationStrict]:
    schema = _SCHEMAS.get(schema_version)
    if schema is None:
        supported = ", ".join(_SCHEMAS)
        raise ValueError(
            f"Unsupported schemaVersion: '{schema_version}'. Supported: {supported}"
        )
    return schema
