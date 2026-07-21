"""Guidance internationalization.

The engine's canonical guidance language is English. A caller opts into a
translation via ``context['language']`` (e.g. ``"pt-br"``); the language is
threaded through the phase context into every formatter and check that emits
guidance prose. Translations are packaged JSON catalogs under ``data/`` that
OVERLAY the English defaults: a missing key falls back to English rather than
failing, so a partial catalog degrades gracefully and the default ``"en"``
output is byte-identical to the pre-i18n engine.

Catalog shape (``data/<language>.json``)::

    {
      "text":          { "<catalog key>": "<translated template>", ... },
      "rubricPrompts": { "<rubric entry id>": "<translated curriculumPrompt>", ... },
      "naPrompts":     { "<rubric entry id>": "<translated naWithoutReasonPrompt>", ... }
    }

Templates use ``{placeholder}`` markers substituted by :func:`render` via
literal replacement — braces that are part of the prose (e.g. operation-call
snippets) pass through untouched, and a translation may reorder or drop
placeholders but never invent new ones.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import cache
from importlib import resources
from typing import Any, cast

from .catalog_en import TEXT_EN

__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "TEXT_EN",
    "na_prompt",
    "normalize_language",
    "render",
    "rubric_prompt",
    "text",
]

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "pt-br")

_ALIASES = {
    "en": "en",
    "en-us": "en",
    "pt": "pt-br",
    "pt-br": "pt-br",
}


def normalize_language(raw: str) -> str | None:
    """Canonicalize a language tag (``pt_BR``/``PT-BR``/``pt`` → ``pt-br``).

    Returns ``None`` for an unsupported tag.
    """
    return _ALIASES.get(raw.strip().lower().replace("_", "-"))


@cache
def _catalog(language: str) -> dict[str, dict[str, str]]:
    if language == DEFAULT_LANGUAGE:
        return {}
    raw = (
        resources.files("crucible.i18n.data")
        .joinpath(f"{language}.json")
        .read_text(encoding="utf-8")
    )
    return cast("dict[str, dict[str, str]]", json.loads(raw))


def text(language: str, key: str) -> str:
    """Resolve a catalog string by key, falling back to the canonical English.

    Raises ``KeyError`` for a key absent from the English catalog (a typo, not
    a missing translation).
    """
    override = _catalog(language).get("text", {}).get(key)
    return override if override is not None else TEXT_EN[key]


def rubric_prompt(language: str, entry_id: str) -> str | None:
    """Translated ``curriculumPrompt`` for a rubric entry, or ``None`` to use
    the English text from ``rubric.json``."""
    return _catalog(language).get("rubricPrompts", {}).get(entry_id)


def na_prompt(language: str, entry_id: str) -> str | None:
    """Translated ``naWithoutReasonPrompt`` for a rubric entry, or ``None`` to
    use the English text from ``rubric.json``."""
    return _catalog(language).get("naPrompts", {}).get(entry_id)


def render(template: str, subs: Mapping[str, Any]) -> str:
    """Substitute ``{placeholder}`` markers by literal replacement.

    Unlike ``str.format`` this leaves prose braces intact, so templates can
    contain operation-call snippets without escaping.
    """
    out = template
    for key, value in subs.items():
        out = out.replace("{" + key + "}", str(value))
    return out
