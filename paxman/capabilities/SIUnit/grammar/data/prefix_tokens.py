"""SI prefix tokens for split-prefix recognition (grammar-only key table).

Mirrors the 24 SI prefixes from BIPM SI Brochure (9th ed., 2019) Table 5 /
ISO 80000-1. These are recognition keys only — no canonical mapping (that
lives in ``rules/data``). Order is longest-first so multi-character prefixes
(``da``) win over their single-character overlaps (``d``).

The grammars use these to recognize a prefix split across whitespace from its
unit (``kilo gram``, ``k g``) as a single span, so the trailing unit is never
emitted as a competing candidate.
"""

from __future__ import annotations

# Word forms of the 24 SI prefixes. "deca"/"deka" are both kept (international
# and US spellings); they do not collide (they diverge before any overlap).
PREFIX_WORD_TOKENS: tuple[str, ...] = (
    "yotta",
    "zetta",
    "exa",
    "peta",
    "tera",
    "giga",
    "mega",
    "kilo",
    "hecto",
    "deca",
    "deka",
    "deci",
    "centi",
    "milli",
    "micro",
    "nano",
    "pico",
    "femto",
    "atto",
    "zepto",
    "yocto",
    "ronna",
    "quetta",
    "ronto",
    "quecto",
)

# Symbol forms, longest-first (``da`` before ``d``).
PREFIX_SYMBOL_TOKENS: tuple[str, ...] = (
    "da",
    "Y",
    "Z",
    "E",
    "P",
    "T",
    "G",
    "M",
    "k",
    "h",
    "d",
    "c",
    "m",
    "µ",
    "n",
    "p",
    "f",
    "a",
    "z",
    "y",
    "r",
    "q",
    "R",
    "Q",
)
