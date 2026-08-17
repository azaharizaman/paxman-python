"""Maintained unit-name to canonical-symbol mapping.

Every maintained SI unit name (base, derived, non-SI, and the gram —
the prefix attachment point) maps to its canonical symbol. Names are
lowercase, single- or multi-word, per the BIPM SI Brochure (9th ed.,
2019) Tables 1, 3 and 8–9.

Prefixed names are not maintained here; they live in the generated
prefixed_unit_names.py module (Task 4).

Symbol values must stay unique: the Task 4 generator's symbol_to_name
reverse map depends on it (last-write-wins).

Maintained authority snapshot — regenerate via the Task 4 tool after edits.
"""

from __future__ import annotations

NAME_TO_SYMBOL: dict[str, str] = {
    # Table 1 — base units.
    "metre": "m",
    "kilogram": "kg",
    "second": "s",
    "ampere": "A",
    "kelvin": "K",
    "mole": "mol",
    "candela": "cd",
    # Table 3 — derived units with special names.
    "radian": "rad",
    "steradian": "sr",
    "hertz": "Hz",
    "newton": "N",
    "pascal": "Pa",
    "joule": "J",
    "watt": "W",
    "coulomb": "C",
    "volt": "V",
    "farad": "F",
    "ohm": "Ω",
    "siemens": "S",
    "weber": "Wb",
    "tesla": "T",
    "henry": "H",
    "degree celsius": "°C",
    "lumen": "lm",
    "lux": "lx",
    "becquerel": "Bq",
    "gray": "Gy",
    "sievert": "Sv",
    "katal": "kat",
    # The gram — the prefix attachment point for mass (§3.2 / D9).
    "gram": "g",
    # Tables 8–9 — non-SI units accepted for use with the SI.
    "minute": "min",
    "hour": "h",
    "day": "d",
    "degree": "°",
    "minute of arc": "′",
    "second of arc": "″",
    "hectare": "ha",
    "litre": "L",
    "tonne": "t",
    "dalton": "Da",
    "electronvolt": "eV",
    "unified atomic mass unit": "u",
    "ångström": "Å",
    "barn": "b",
    "bar": "bar",
    "millimetre of mercury": "mmHg",
}
