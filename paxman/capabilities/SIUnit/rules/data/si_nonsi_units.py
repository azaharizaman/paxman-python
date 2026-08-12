"""Non-SI units accepted for use with the SI.

From BIPM SI Brochure (9th ed., 2019), Tables 8–9 — the complete union
of both tables' symbols (′ is U+2032 PRIME, ″ is U+2033 DOUBLE PRIME,
Å is U+00C5). LITRE_WRITTEN_FORMS records both written forms of the
litre symbol.

Maintained authority snapshot — regenerate via the Task 4 tool after edits.
"""

from __future__ import annotations

NONSI_UNIT_SYMBOLS: frozenset[str] = frozenset(
    {
        "min",
        "h",
        "d",
        "°",
        "′",
        "″",
        "ha",
        "L",
        "l",
        "t",
        "Da",
        "eV",
        "u",
        "Å",
        "b",
        "bar",
        "mmHg",
    }
)

LITRE_WRITTEN_FORMS: frozenset[str] = frozenset({"L", "l"})
