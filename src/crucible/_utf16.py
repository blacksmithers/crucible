"""UTF-16 code-unit length — the unit the reference engine measures strings in.

JavaScript ``String.prototype.length`` (and therefore every Zod ``.min()`` and
every rubric string-length check in ``@specforge/validator``) counts UTF-16 code
units, not Unicode code points. Python ``len(str)`` counts code points. The two
agree for the Basic Multilingual Plane but diverge on astral characters (emoji,
rare CJK, ...), where each code point is a UTF-16 surrogate pair — length 2, not
1. Measuring with this helper keeps min-length gates and scores byte-equivalent.
"""

from __future__ import annotations


def utf16_len(s: str) -> int:
    """Length of ``s`` in UTF-16 code units (JS ``s.length``)."""
    return sum(2 if ord(c) > 0xFFFF else 1 for c in s)
