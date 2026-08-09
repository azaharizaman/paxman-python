"""English currency word recognition keys (grammar data).

Source: keys of NAME_TO_CODES in paxman/capabilities/Currency/rules/data/
cldr_currencies.py (Unicode CLDR v47 English display names).

Keys are lowercase (D4): the word grammar folds input to lowercase, so
the recognition keys match the rule-data lookup keys exactly.

Ordered longest-first so the grammar alternates multi-word names
before their shorter tails when present.
"""

from __future__ import annotations

WORD_TOKENS: tuple[str, ...] = (
    "boliviano",
    "lilangeni",
    "afghani",
    "bolivar",
    "cordoba",
    "guarani",
    "hryvnia",
    "lempira",
    "quetzal",
    "ringgit",
    "rufiyaa",
    "dirham",
    "dollar",
    "florin",
    "forint",
    "koruna",
    "kwacha",
    "pataca",
    "rupiah",
    "shekel",
    "somoni",
    "tugrik",
    "colon",
    "dinar",
    "franc",
    "krona",
    "krone",
    "manat",
    "naira",
    "nakfa",
    "pound",
    "riyal",
    "ruble",
    "rupee",
    "tenge",
    "zloty",
    "baht",
    "cedi",
    "dong",
    "dram",
    "euro",
    "kina",
    "kyat",
    "lari",
    "lira",
    "mark",
    "peso",
    "pula",
    "rand",
    "real",
    "rial",
    "riel",
    "taka",
    "tala",
    "vatu",
    "yuan",
    "kip",
    "leu",
    "sol",
    "som",
    "won",
    "yen",
)
