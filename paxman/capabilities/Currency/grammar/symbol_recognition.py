"""CLDR currency symbol recognition grammar.

Recognizes a standalone currency symbol token (qualified or bare) as one
span-bearing token. The alternation is built from SYMBOL_TOKENS
(qualified-first, longest-first — D4). Syntax only: resolving the symbol
to a code is the rules' job.
"""

from __future__ import annotations

import re

from paxman.capabilities.Currency.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.domain import Grammar, RecognitionMatch

_SYMBOL_ALTERNATION = "|".join(re.escape(token) for token in SYMBOL_TOKENS)
# Lookarounds, not \b: pure-symbol tokens ("$", "€") are non-word
# characters that \b would reject at string start, and the lookarounds
# still block matches inside a longer token. The sign block mirrors the
# Money symbol grammar.
_SYMBOL_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])(?:{_SYMBOL_ALTERNATION})(?![\w\-+\u2212])"
)


def _is_qualified(token: str) -> bool:
    """Whether a symbol token carries an ASCII letter (e.g. "US$")."""
    return any(char.isascii() and char.isalpha() for char in token)


class SymbolRecognition(Grammar[CurrencyNotation]):
    """Recognizes standalone CLDR currency symbol tokens.

    A token is "qualified" when it embeds an ASCII letter ("US$", "A$",
    "R$") and "bare" otherwise ("$", "€", "¥"). Symbols are case-exact —
    no case folding (symbols are arbitrary glyph strings).

    Examples: "US$" -> text "US$", shape "qualified_symbol"
              "€"    -> text "€",    shape "symbol"
    Non-examples: "US$5"/"$500" (amount-glued: the trailing digit is a
        word character, blocked by the lookaround), "x€" (inside a
        longer token).
    """

    name = "symbol_recognition"
    semantics = "symbol_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[CurrencyNotation]]:
        """Extract standalone symbol tokens from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape "symbol" or
            "qualified_symbol" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CurrencyNotation]] = []
        for match in _SYMBOL_PATTERN.finditer(text):
            token = match.group(0)
            matches.append(
                RecognitionMatch(
                    notation=CurrencyNotation(
                        text=token,
                        shape="qualified_symbol" if _is_qualified(token) else "symbol",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=token,
                )
            )
        return matches
