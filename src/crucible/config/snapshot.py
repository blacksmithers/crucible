"""Per-spec config snapshot validation.

A frozen per-spec snapshot is a FULL resolved config, so it validates against
the complete schema, refinements and all — a partial is rejected.
"""

from __future__ import annotations

from .schema import ValidatorConfigSchema as ValidatorConfigSnapshotSchema

__all__ = ["ValidatorConfigSnapshotSchema"]
