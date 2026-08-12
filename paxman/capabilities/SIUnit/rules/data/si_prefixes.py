"""SI prefix symbols and names (BIPM SI Brochure, 9th ed., 2019, Table 5)."""

from __future__ import annotations

PREFIX_SYMBOLS: frozenset[str] = frozenset(
    {
        "da",
        "h",
        "k",
        "M",
        "G",
        "T",
        "P",
        "E",
        "Z",
        "Y",
        "R",
        "Q",
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
    }
)

PREFIX_NAMES: dict[str, str] = {
    "Q": "quetta",
    "R": "ronna",
    "Y": "yotta",
    "Z": "zetta",
    "E": "exa",
    "P": "peta",
    "T": "tera",
    "G": "giga",
    "M": "mega",
    "k": "kilo",
    "h": "hecto",
    "da": "deca",
    "d": "deci",
    "c": "centi",
    "m": "milli",
    "µ": "micro",
    "n": "nano",
    "p": "pico",
    "f": "femto",
    "a": "atto",
    "z": "zepto",
    "y": "yocto",
    "r": "ronto",
    "q": "quecto",
}
