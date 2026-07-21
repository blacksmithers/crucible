"""UTF-16 string-length parity (defect: len() code points vs JS UTF-16 units).

The reference engine measures every string length in UTF-16 code units (JS
``String.length``); the port used Python ``len()`` (code points). They agree on
the BMP and diverge on astral characters (emoji), where each code point is a
surrogate pair. That flipped rubric min-length gates — and therefore scores —
for any field carrying an emoji near its threshold.
"""

from __future__ import annotations

import pytest

from crucible._utf16 import utf16_len
from crucible.config import load_defaults
from crucible.guidance.engine.resolver import resolve_threshold
from crucible.guidance.rubric import ticket_entries
from crucible.scoring.per_field import compute_per_field

_EMOJI = "\U0001f600"  # U+1F600, one code point, two UTF-16 units


def test_utf16_len_bmp_equals_codepoints() -> None:
    assert utf16_len("") == 0
    assert utf16_len("hello") == 5
    assert utf16_len("café") == 4  # é is BMP


def test_utf16_len_counts_astral_as_two() -> None:
    assert utf16_len(_EMOJI) == 2
    assert utf16_len(_EMOJI * 10) == 20
    assert utf16_len("a" + _EMOJI + "b") == 4


def _first_field_minlength_entry() -> tuple:
    """A ticket rubric entry with a whole-field string minLength check, plus its
    threshold — the scoring path that measures a string's length."""
    config = load_defaults()
    for entry in ticket_entries:
        if entry.conditional_applicability is not None:
            continue
        for check in entry.structural_checks:
            if check.type == "minLength" and check.applies_to in ("field", None):
                threshold = int(resolve_threshold(check, config, {}))
                if threshold >= 2:
                    return entry, threshold, config
    pytest.skip("no unconditional field-minLength ticket entry found")


def test_scoring_measures_field_length_in_utf16() -> None:
    entry, threshold, config = _first_field_minlength_entry()
    field = entry.field_path.split(".", 1)[1]  # "ticket.description" -> "description"

    # emoji count chosen so code points < threshold <= UTF-16 units:
    n = (threshold + 1) // 2
    assert n < threshold <= 2 * n

    emoji_val = _EMOJI * n  # UTF-16 length 2n >= threshold  -> should PASS
    ascii_val = "a" * n  # length n < threshold             -> should FAIL

    def earned(value: object) -> float:
        entity = {field: value}
        return compute_per_field(entity, [entry], config)[entry.id].earned

    # UTF-16 counting: emoji string clears the gate, the equally-code-point-long
    # ASCII string does not. Code-point counting would fail both.
    assert earned(emoji_val) > 0, "emoji string should clear the UTF-16 min-length"
    assert earned(ascii_val) == 0, "ASCII string of n code points should fail"
