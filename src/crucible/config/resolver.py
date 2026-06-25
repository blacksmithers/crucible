"""Planning config resolver (port of ``config/resolver.ts``).

Resolves an effective config by deep-merging project overrides / per-spec
snapshots over the hardcoded defaults. The backing store is abstracted as
:class:`IConfigStore`; SpecSmither supplies a SQLite-backed implementation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol

from ..types.config import ValidatorConfig
from .defaults import HARDCODED_DEFAULTS

PLANNING_CONFIG_SCHEMA_VERSION = 1
PLANNING_CONFIG_DOMAIN = "planning"


def _deep_merge(target: dict[str, Any], source: Any) -> dict[str, Any]:
    if not isinstance(source, dict):
        return target
    result = dict(target)
    for key, value in source.items():
        if value is None:
            continue
        existing = result.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            result[key] = _deep_merge(existing, value)
        else:
            # Arrays and primitives replace wholesale.
            result[key] = value
    return result


class IConfigStore(Protocol):
    """Backing store for project/spec config overrides (async)."""

    async def get_project_overrides(
        self, project_id: str, domain: str
    ) -> dict[str, Any] | None: ...

    async def get_spec_snapshot(self, spec_id: str, domain: str) -> dict[str, Any] | None: ...


class PlanningConfigResolver:
    def __init__(self, store: IConfigStore) -> None:
        self._store = store

    @property
    def domain(self) -> str:
        return PLANNING_CONFIG_DOMAIN

    async def resolve_for_project(self, project_id: str) -> ValidatorConfig:
        overrides = await self._store.get_project_overrides(project_id, PLANNING_CONFIG_DOMAIN)
        return _deep_merge(deepcopy(HARDCODED_DEFAULTS), overrides or {})

    async def resolve_for_spec(self, spec_id: str) -> ValidatorConfig:
        snapshot = await self._store.get_spec_snapshot(spec_id, PLANNING_CONFIG_DOMAIN)
        return _deep_merge(deepcopy(HARDCODED_DEFAULTS), snapshot or {})

    async def build_snapshot_from_project(
        self, project_id: str
    ) -> dict[str, Any]:
        snapshot = await self.resolve_for_project(project_id)
        return {"snapshot": snapshot, "schemaVersion": PLANNING_CONFIG_SCHEMA_VERSION}
