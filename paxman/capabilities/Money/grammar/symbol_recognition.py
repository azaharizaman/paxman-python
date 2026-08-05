"""CLDR currency symbol recognition grammar.

Recognizes a currency symbol token adjacent to an amount, in either
order, as one span-bearing token. The symbol alternation is built from
SYMBOL_TOKENS (qualified forms first, longest-first within each class,
so "US$" alternates before "$"). Syntax only: resolving the symbol to a
code is the rules' job.
"""

from __future__ import annotations

import re
from typing import cast

from paxman.capabilities.Money.grammar import AMOUNT_PATTERN, classify_amount_shape
from paxman.capabilities.Money.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.domain import Grammar, RecognitionMatch

_SYMBOL_ALTERNATION = "|".join(re.escape(token) for token in SYMBOL_TOKENS)
# Lookarounds, not \b: pure-symbol tokens ("$", "€") are non-word
# characters that \b would reject at string start, and the lookarounds
# still block matches inside a longer token.
_SYMBOL_PATTERN = re.compile(
    rf"(?<!\w)(?:(?P<prefix_symbol>{_SYMBOL_ALTERNATION})"
    rf" ?(?P<prefix_amount>{AMOUNT_PATTERN})"
    rf"|(?P<suffix_amount>{AMOUNT_PATTERN}) ?(?P<suffix_symbol>{_SYMBOL_ALTERNATION}))"
    rf"(?!\w)"
)


def _is_qualified(token: str) -> bool:
    """A symbol is qualified when it contains an ASCII letter (US$, RM)."""
    return any(ch.isascii() and ch.isalpha() for ch in token)


class SymbolRecognition(Grammar[MoneyNotation]):
    """Recognizes currency symbol + amount tokens.

    Matches a CLDR symbol adjacent to an amount in either order:
    "$500", "US$50.79", "RM100", "€5" (prefix) or "500 €",
    "1.000,00 €" (suffix). A symbol containing an ASCII letter (e.g.
    "US$", "CA$", "RM") is emitted with currency_shape
    "qualified_symbol"; a pure-symbol token ("$", "€") with "symbol".
    The qualified-before-bare token ordering makes "US$50.79" match as
    the qualified form, not as bare "$" followed by a stray amount.

    Examples: "US$50.79" -> currency_part "US$", shape "qualified_symbol"
              "$500" -> currency_part "$", shape "symbol"
    Non-examples: "$" (no amount), "USD 500" (codes are not symbols)
    """

    name = "symbol_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[MoneyNotation]]:
        """Extract symbol+amount tokens from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with "symbol"/"qualified_symbol"
            notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[MoneyNotation]] = []
        for match in _SYMBOL_PATTERN.finditer(text):
            symbol = cast(
                str, match.group("prefix_symbol") or match.group("suffix_symbol")
            )
            amount = cast(
                str, match.group("prefix_amount") or match.group("suffix_amount")
            )
            matches.append(
                RecognitionMatch(
                    notation=MoneyNotation(
                        currency_part=symbol,
                        amount_part=amount,
                        currency_shape=(
                            "qualified_symbol" if _is_qualified(symbol) else "symbol"
                        ),
                        amount_shape=classify_amount_shape(amount),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
