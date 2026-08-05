"""Shared amount token helpers for Money recognition grammars.

Holds the single amount-token regex and the syntactic amount-shape
classifier shared by the three recognition grammars. This module is part
of the recognition layer and imports nothing from paxman.* (the purity
gate forbids grammar modules from importing rules or parsing): shape
classification is purely syntactic — the grammars never resolve an
amount, only describe its shape for the rules.
"""

from __future__ import annotations

# A digit run with optional "," / "." / narrow no-break-space (U+202F)
# separators, optionally wrapped in parentheses (accounting form). The
# amount never contains an ASCII space: the single ASCII space in a
# matched token is always the currency/amount separator.
_AMOUNT_CORE = r"[0-9][0-9.,\u202f]*"
AMOUNT_PATTERN = rf"(?:\({_AMOUNT_CORE}\)|{_AMOUNT_CORE})"


def classify_amount_shape(amount: str) -> str:
    """Classify an amount token's syntactic shape (syntax only).

    Shape is decided from the token alone, never by parsing its value:
    "accounting" when the whole token is wrapped in parentheses,
    "space_decimal" when it contains a (narrow no-break) space,
    otherwise "dot_decimal" or "comma_decimal" by the LAST separator,
    else "integer".

    Args:
        amount: The amount token as written (e.g. "1.000,50", "(500)").

    Returns:
        One of "integer", "dot_decimal", "comma_decimal",
        "space_decimal", "accounting".
    """
    if amount.startswith("(") and amount.endswith(")"):
        return "accounting"
    if any(ch.isspace() for ch in amount):
        return "space_decimal"
    if amount.rfind(".") > amount.rfind(","):
        return "dot_decimal"
    if amount.rfind(",") > amount.rfind("."):
        return "comma_decimal"
    return "integer"
