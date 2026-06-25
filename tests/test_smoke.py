"""Scaffold smoke test — the package imports and exposes a version."""

from __future__ import annotations

import crucible


def test_package_imports() -> None:
    assert isinstance(crucible.__version__, str)
    assert crucible.__version__
