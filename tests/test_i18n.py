"""i18n — the ``language`` context option and the pt-br catalog.

Three properties are pinned:

1. **EN is the identity** — ``language: "en"`` (or omitting the option) yields
   byte-identical guidance to the pre-i18n engine (the rest of the suite pins
   the absolute strings; here we pin en == default).
2. **Catalog completeness** — the pt-br catalog covers every EN catalog key,
   every rubric ``curriculumPrompt``, and exactly the rubric entries that have
   an EN ``naWithoutReasonPrompt``; a translation may reorder or drop
   ``{placeholder}`` markers but never invent one.
3. **pt-br output** — representative guidance from every source (rubric
   prompts, composite templates, fixed prompts, cross-validation emissions)
   comes out in Portuguese.
"""

from __future__ import annotations

import json
import re
from importlib import resources
from typing import Any

import pytest

from crucible import load_defaults, validate
from crucible.api.input_validation import ValidatorInputError
from crucible.guidance.format.operations_vocabulary import (
    OPERATION_DESCRIPTIONS,
    describe_operation,
)
from crucible.i18n import (
    SUPPORTED_LANGUAGES,
    TEXT_EN,
    normalize_language,
    render,
    text,
)

_PLACEHOLDER = re.compile(r"\{([a-zA-Z][a-zA-Z0-9]*)\}")


def _load_pt_catalog() -> dict[str, dict[str, str]]:
    raw = (
        resources.files("crucible.i18n.data").joinpath("pt-br.json").read_text(encoding="utf-8")
    )
    return json.loads(raw)  # type: ignore[no-any-return]


def _load_rubric() -> list[dict[str, Any]]:
    raw = (
        resources.files("crucible.guidance.rubric.data")
        .joinpath("rubric.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(raw)  # type: ignore[no-any-return]


def _spec(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schemaVersion": "1.1",
        "id": "s1",
        "projectId": "p1",
        "title": "Spec Title",
        "status": "draft",
        "goals": [],
        "requirements": [],
        "architecture": "",
        "scope": {"inScope": [], "outOfScope": []},
        "techStack": [],
        "folderStructures": [],
        "acceptanceCriteria": [],
        "epics": [
            {
                "id": "e1",
                "title": "Epic One",
                "description": "d",
                "objective": "o",
                "tickets": [
                    {
                        "id": "t1",
                        "title": "Ticket One",
                        "dependencies": [{"ticketId": "ghost"}],
                    }
                ],
            }
        ],
    }
    base.update(overrides)
    return base


def _guidance_json(spec: dict[str, Any], phase: str, language: str | None) -> Any:
    ctx: dict[str, Any] = {
        "phase": phase,
        "config": load_defaults(),
        "returns": ["guidance"],
    }
    if phase in ("epic_expansion", "ticket_decomposition"):
        ctx["activeEntityId"] = "e1"
    elif phase == "ticket_expansion":
        ctx["activeEntityId"] = "t1"
    if language is not None:
        ctx["language"] = language
    result = validate(spec, ctx)
    assert result.guidance is not None
    return {
        eid: [e.message for e in entries]
        for eid, entries in result.guidance.per_entity.items()
    }


# --- normalization -----------------------------------------------------------


@pytest.mark.parametrize("raw", ["pt-br", "pt_BR", "PT-BR", "pt"])
def test_normalize_language_pt_aliases(raw: str) -> None:
    assert normalize_language(raw) == "pt-br"


@pytest.mark.parametrize("raw", ["en", "EN", "en-US", "en_us"])
def test_normalize_language_en_aliases(raw: str) -> None:
    assert normalize_language(raw) == "en"


def test_normalize_language_unsupported() -> None:
    assert normalize_language("fr") is None


def test_invalid_language_raises() -> None:
    with pytest.raises(ValidatorInputError, match="Invalid language 'fr'"):
        validate(
            _spec(), {"phase": "planning_spec", "config": load_defaults(), "language": "fr"}
        )


# --- catalog completeness ----------------------------------------------------


def test_pt_text_covers_every_en_key() -> None:
    pt = _load_pt_catalog()
    assert set(pt["text"].keys()) == set(TEXT_EN.keys())


def test_pt_rubric_prompts_cover_every_entry() -> None:
    pt = _load_pt_catalog()
    rubric_ids = {e["id"] for e in _load_rubric()}
    assert set(pt["rubricPrompts"].keys()) == rubric_ids


def test_pt_na_prompts_cover_exactly_the_na_entries() -> None:
    pt = _load_pt_catalog()
    na_ids = {e["id"] for e in _load_rubric() if e.get("naWithoutReasonPrompt")}
    assert set(pt["naPrompts"].keys()) == na_ids


def test_pt_placeholders_never_invented() -> None:
    """A translation may reorder or drop placeholders, never introduce one."""
    pt = _load_pt_catalog()
    for key, template in pt["text"].items():
        allowed = set(_PLACEHOLDER.findall(TEXT_EN[key]))
        assert set(_PLACEHOLDER.findall(template)) <= allowed, key
    en_prompts = {e["id"]: e["curriculumPrompt"] for e in _load_rubric()}
    for entry_id, template in pt["rubricPrompts"].items():
        allowed = set(_PLACEHOLDER.findall(en_prompts[entry_id]))
        assert set(_PLACEHOLDER.findall(template)) <= allowed, entry_id


def test_pt_rubric_threshold_placeholders_preserved() -> None:
    """Threshold markers ({minCount}, {minLength}, ...) must survive translation
    so the substitution engine can resolve them."""
    pt = _load_pt_catalog()
    en_prompts = {e["id"]: e["curriculumPrompt"] for e in _load_rubric()}
    threshold_markers = {"minCount", "minLength", "itemMinLength"}
    for entry_id, template in pt["rubricPrompts"].items():
        expected = set(_PLACEHOLDER.findall(en_prompts[entry_id])) & threshold_markers
        assert expected <= set(_PLACEHOLDER.findall(template)), entry_id


# --- EN is the identity ------------------------------------------------------


@pytest.mark.parametrize(
    "phase",
    [
        "planning_spec",
        "epic_decomposition",
        "epic_expansion",
        "ticket_decomposition",
        "ticket_expansion",
        "cross_validation",
    ],
)
def test_en_language_is_default(phase: str) -> None:
    spec = _spec()
    assert _guidance_json(spec, phase, None) == _guidance_json(spec, phase, "en")


# --- pt-br output ------------------------------------------------------------


def test_pt_composite_and_rubric_guidance() -> None:
    messages = _guidance_json(_spec(), "planning_spec", "pt-br")["s1"]
    joined = "\n".join(messages)
    assert "Especificação \"Spec Title\" — fase planning_spec incompleta." in joined
    assert "DECLARE estes campos fundacionais juntos." in joined


def test_pt_individual_finding_frame() -> None:
    # A spec with only one missing critical field yields an individual message
    # (composites need >= 2 findings on the same entity).
    spec = _spec()
    epic = spec["epics"][0]
    ticket = epic["tickets"][0]
    ticket["dependencies"] = []
    messages = _guidance_json(spec, "ticket_expansion", "pt-br").get("t1", [])
    joined = "\n".join(messages)
    assert 'Ticket "Ticket One"' in joined
    assert "ausente" in joined or "incompleto" in joined


def test_pt_fixed_decomposition_prompts() -> None:
    spec = _spec()
    epic_msg = _guidance_json(spec, "epic_decomposition", "pt-br")["s1"][0]
    assert epic_msg.startswith("Fase de decomposição.")
    ctx: dict[str, Any] = {
        "phase": "ticket_decomposition",
        "config": load_defaults(),
        "returns": ["guidance"],
        "activeEntityId": "e1",
        "language": "pt-br",
    }
    result = validate(spec, ctx)
    assert result.guidance is not None
    ticket_msg = result.guidance.per_entity["e1"][0].message
    assert "tickets deste épico" in ticket_msg


def test_pt_cross_validation_guidance() -> None:
    messages = _guidance_json(_spec(), "cross_validation", "pt-br")["t1"]
    joined = "\n".join(messages)
    assert 'O ticket "t1" referencia "ghost" em dependencies' in joined


def test_pt_language_alias_reaches_guidance() -> None:
    spec = _spec()
    assert _guidance_json(spec, "planning_spec", "pt_BR") == _guidance_json(
        spec, "planning_spec", "pt-br"
    )


# --- helpers -----------------------------------------------------------------


def test_render_leaves_prose_braces_intact() -> None:
    out = render("call f({\n  x: {value}\n})", {"value": 7})
    assert out == "call f({\n  x: 7\n})"


def test_text_unknown_key_raises() -> None:
    with pytest.raises(KeyError):
        text("en", "guidance.doesNotExist")


def test_describe_operation_translated() -> None:
    assert describe_operation("gps") == "Full X-ray of the specification"
    assert describe_operation("gps", "pt-br") == "Raio-X completo da especificação"
    assert OPERATION_DESCRIPTIONS["gps"] == "Full X-ray of the specification"


def test_supported_languages() -> None:
    assert SUPPORTED_LANGUAGES == ("en", "pt-br")
