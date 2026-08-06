"""ISO 4217 alpha-3 currency code recognition grammar.

Recognizes an ISO 4217 alpha-3 code shape adjacent to an amount, in
either order, as one span-bearing token. Syntax only: unknown codes are
still matched — deciding validity is the rules' job.
"""

from __future__ import annotations

import re
from typing import cast

from paxman.capabilities.Money.grammar import AMOUNT_PATTERN, classify_amount_shape
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Sign characters ('-', U+2212, '+') are outside the amount grammar; the
# boundary guards reject sign-adjacent tokens so the sign is never dropped.
_CODE_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])"
    rf"(?:(?P<prefix_code>[A-Z]{{3}}) ?(?P<prefix_amount>{AMOUNT_PATTERN})"
    rf"|(?P<suffix_amount>{AMOUNT_PATTERN}) ?(?P<suffix_code>[A-Z]{{3}}))"
    rf"(?![\w\-+\u2212])"
)


class CodeRecognition(Grammar[MoneyNotation]):
    """Recognizes ISO 4217 alpha-3 code + amount tokens.

    Matches a 3-letter uppercase ASCII code adjacent to an amount in
    either order: "USD500", "USD 500" (prefix) or "500 USD", "100MYR"
    (suffix). Word boundaries keep the whole token inside one span.

    Examples: "USD500" -> currency_part "USD", amount_part "500"
              "500 USD" -> same notation, suffix order
    Non-examples: "USD" (no amount), "usd 500" (lowercase),
                  "xUSD500" (inside a longer token)
    """

    name = "code_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[MoneyNotation]]:
        """Extract code+amount tokens from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape "code" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[MoneyNotation]] = []
        for match in _CODE_PATTERN.finditer(text):
            currency = cast(
                str, match.group("prefix_code") or match.group("suffix_code")
            )
            amount = cast(
                str, match.group("prefix_amount") or match.group("suffix_amount")
            )
            matches.append(
                RecognitionMatch(
                    notation=MoneyNotation(
                        currency_part=currency,
                        amount_part=amount,
                        currency_shape="code",
                        amount_shape=classify_amount_shape(amount),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
