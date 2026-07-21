"""UTF-16 code-unit length — the unit crucible measures string length in.

crucible measures string length in UTF-16 code units, exactly as JavaScript
``String.length`` does — so every min-length gate and every rubric
string-length check counts UTF-16 code units, not Unicode code points. Python
``len(str)`` counts code points. The two agree for the Basic Multilingual Plane
but diverge on astral characters (emoji, rare CJK, ...), where each code point
is a UTF-16 surrogate pair — length 2, not 1. Measuring with this helper keeps
min-length gates and scores consistent.
"""

from __future__ import annotations


def utf16_len(s: str) -> int:
    """Length of ``s`` in UTF-16 code units (JS ``s.length``)."""
    return sum(2 if ord(c) > 0xFFFF else 1 for c in s)
