"""ISO 4217 alpha-3 currency code recognition grammar.

Recognizes a standalone 3-letter ASCII code shape (case-insensitive) as
one span-bearing token. Case folding is the grammar's concern (Country
alpha-2/alpha-3 precedent): the token is emitted uppercase so the rule is
a pure table lookup. Syntax only: unknown codes are still matched —
deciding validity is the rules' job.
"""

from __future__ import annotations

import re

from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Sign characters ('-', U+2212, '+') are outside the identifier grammar; the
# boundary guards reject sign-adjacent tokens (mirrors Money's code grammar).
_CODE_PATTERN = re.compile(r"(?<![\w\-+\u2212])(?P<code>[A-Za-z]{3})(?![\w\-+\u2212])")


class CodeRecognition(Grammar[CurrencyNotation]):
    """Recognizes standalone ISO 4217 alpha-3 code shapes.

    Matches a 3-letter ASCII code in any casing: "USD", "usd", "Gbp".
    The grammar folds the token to uppercase at recognition; the rule
    validates against CURRENCY_CODES.

    Examples: "USD" -> text "USD", shape "code"
              "usd" -> text "USD", shape "code"
    Non-examples: "USD500"/"USD-500" (amount/sign-glued: blocked by the
        lookarounds), "xUSD" (inside a longer token).
    """

    name = "code_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[CurrencyNotation]]:
        """Extract standalone 3-letter code tokens from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape "code" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CurrencyNotation]] = []
        for match in _CODE_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CurrencyNotation(
                        text=match.group("code").upper(),
                        shape="code",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
