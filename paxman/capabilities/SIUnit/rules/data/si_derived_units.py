"""SI derived unit symbols with special names.

From BIPM SI Brochure (9th ed., 2019), Table 3 — the 22 special-name
symbols plus "g" (the gram), the prefix attachment point for mass per
§3.2 (the gram is not itself a Table 3 entry).

Maintained authority snapshot — regenerate via the Task 4 tool after edits.
"""

from __future__ import annotations

DERIVED_UNIT_SYMBOLS: frozenset[str] = frozenset(
    {
        "rad",
        "sr",
        "Hz",
        "N",
        "Pa",
        "J",
        "W",
        "C",
        "V",
        "F",
        "Ω",
        "S",
        "Wb",
        "T",
        "H",
        "°C",
        "lm",
        "lx",
        "Bq",
        "Gy",
        "Sv",
        "kat",
        "g",
    }
)
