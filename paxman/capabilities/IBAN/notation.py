"""IBAN notation — grammar-normalized compact form."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IBANNotation:
    """IBAN notation — compact + structured decomposition.

    ``country_code`` 2-letter ISO 3166-1 alpha-2, uppercased.
    ``check_digits`` 2-digit string at positions 3-4.
    ``bban`` 1-30 alphanum, uppercased, spaces stripped.
    ``compact`` electronic string country_code+check_digits+bban (15-34).
    The grammar never computes mod-97; rules own it.
    """

    country_code: str  # e.g. "DE" — length 2, A-Z
    check_digits: str  # e.g. "89" — length 2, 0-9
    bban: str  # e.g. "370400440532013000" — 1-30 alphanum
    compact: str  # e.g. "DE89370400440532013000" — 15-34
