"""crucible — deterministic validation engine for OpenSpec v1.1 specifications.

Faithful Python port of the SpecForge ``@specforge/validator`` engine.

The public API is assembled incrementally as the port lands (config →
structural → scoring → rubric → cross-validation → guidance → api). Until the
``api`` layer is wired, importing ``crucible`` exposes only ``__version__``.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0.dev0"
