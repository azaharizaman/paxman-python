"""Amount parsing and canonical formatting helpers for the Money capability.

Pure digit-string logic: parsing.py sits at the package root (outside
grammar/ and rules/) and imports nothing from paxman.*.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal


@dataclass(frozen=True, slots=True)
class ParsedAmount:
    """A parsed amount: normalized integer and fractional digit strings."""

    integer: str
    fraction: str

    def decimal_digits(self) -> int:
        """Return the number of fractional digits."""
        return len(self.fraction)

    def to_decimal_string(self) -> str:
        """Render as "integer[.fraction]" for value construction."""
        if not self.fraction:
            return self.integer
        return f"{self.integer}.{self.fraction}"


def parse_amount(raw: str) -> ParsedAmount | None:
    """Parse an amount token into normalized integer and fraction strings.

    "Last separator wins": the final "," or "." is the decimal point; any
    separators before it are base-1000 grouping. A single separator is
    therefore always a decimal point ("1,00" -> integer "1", fraction "";
    "1.234" -> integer "1", fraction "234"). Grouping folds to a plain
    integer ("1,00.50" -> integer "1000", fraction "50"). A token with no
    separator keeps the plain digit run with leading zeros stripped.
    Parentheses (accounting form) are ignored: only digit characters and
    the separators participate.

    Assumption note: the user's "1.500,50 -> 1000.50" is internally
    inconsistent (grouping math gives 1500.50) and is treated as a typo
    for "1.000,50"; both "1,00.50" and "1.000,50" parse to integer
    "1000", fraction "50".

    Args:
        raw: The amount token as written (e.g. "1,00.50", "(500)").

    Returns:
        The parsed amount, or None when the token contains no digit
        character (e.g. "" or "abc").
    """
    if not any(ch.isdigit() for ch in raw):
        return None
    last_separator = max(raw.rfind(","), raw.rfind("."))
    if last_separator == -1:
        digits = "".join(ch for ch in raw if ch.isdigit())
        return ParsedAmount(integer=digits.lstrip("0") or "0", fraction="")
    integer_raw = raw[:last_separator]
    fraction_raw = raw[last_separator + 1 :]
    groups = [g for g in re.split(r"[.,]", integer_raw) if g]
    total = 0
    for group in groups:
        group_digits = "".join(ch for ch in group if ch.isdigit()) or "0"
        total = total * 1000 + int(group_digits)
    fraction_digits = "".join(ch for ch in fraction_raw if ch.isdigit())
    if not fraction_digits or set(fraction_digits) == {"0"}:
        fraction = ""
    else:
        fraction = fraction_digits
    return ParsedAmount(integer=str(total), fraction=fraction)


def format_amount(
    parsed: ParsedAmount,
    minor_units: int,
    precision: Literal["strict", "truncate", "round"],
) -> str:
    """Format a parsed amount to exactly ``minor_units`` decimal digits.

    "strict" trusts the caller: the rules guarantee the parsed amount has
    at most ``minor_units`` decimal digits, so the fraction is only
    zero-padded. "truncate" drops excess digits (toward zero at the
    minor-unit scale) and zero-pads shorter fractions. "round" quantizes
    the numeric value half-to-even (ROUND_HALF_EVEN). Zero minor units
    never render a decimal point ("500", not "500.").

    Args:
        parsed: Parsed amount to format.
        minor_units: Number of decimal digits in the output.
        precision: Over-precision policy ("strict" | "truncate" | "round").

    Returns:
        The amount digit string with exactly ``minor_units`` decimal
        digits (e.g. "500.00", or "500" when minor_units == 0).
    """
    if precision == "round":
        value = Decimal(parsed.integer or "0") + Decimal(parsed.fraction or "0") / (
            Decimal(10) ** len(parsed.fraction)
        )
        quantum = Decimal(1).scaleb(-minor_units)
        return format(value.quantize(quantum, rounding=ROUND_HALF_EVEN), "f")
    if precision == "truncate":
        fraction = parsed.fraction[:minor_units].ljust(minor_units, "0")
    else:  # strict — rules guarantee decimal_digits() <= minor_units
        fraction = parsed.fraction.ljust(minor_units, "0")
    if minor_units == 0:
        return parsed.integer or "0"
    return f"{parsed.integer or '0'}.{fraction}"
