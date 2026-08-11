"""CLDR currency display-name word recognition grammar.

Recognizes a currency display-name word adjacent to an amount, in
either order, as one span-bearing token. The word alternation is built
from WORD_TOKENS (longest-first), word-boundary anchored and
case-insensitive. Syntax only: resolving the word to a code is the
rules' job.
"""

from __future__ import annotations

import re
from typing import cast

from paxman.capabilities.Money.grammar import AMOUNT_PATTERN, classify_amount_shape
from paxman.capabilities.Money.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.domain import Grammar, RecognitionMatch

_WORD_ALTERNATION = "|".join(re.escape(token) for token in WORD_TOKENS)
# Sign characters ('-', U+2212, '+') are outside the amount grammar; the
# boundary guards reject sign-adjacent tokens so the sign is never dropped.
_WORD_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])(?:(?P<prefix_word>{_WORD_ALTERNATION})"
    rf" ?(?P<prefix_amount>{AMOUNT_PATTERN})"
    rf"|(?P<suffix_amount>{AMOUNT_PATTERN}) ?(?P<suffix_word>{_WORD_ALTERNATION}))"
    rf"(?![\w\-+\u2212])",
    re.IGNORECASE,
)


class WordRecognition(Grammar[MoneyNotation]):
    """Recognizes currency display-name word + amount tokens.

    Matches a CLDR display-name word adjacent to an amount in either
    order: "18 Dollar" (amount-first) or "500 Ringgit", "500 Euro".
    Matching is case-insensitive; the currency_part is the word as
    written in the input (e.g. "Dollar" from "18 Dollar", "euro" from
    "500 euro"). Word boundaries keep the match inside one token:
    "500 Dollars" does not match.

    Examples: "18 Dollar" -> currency_part "Dollar", shape "word"
              "500 euro" -> currency_part "euro", shape "word"
    Non-examples: "500 USD" (codes are not words), "500 Dollars"
    """

    name = "word_recognition"
    semantics = "word_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[MoneyNotation]]:
        """Extract word+amount tokens from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape "word" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[MoneyNotation]] = []
        for match in _WORD_PATTERN.finditer(text):
            word = cast(str, match.group("prefix_word") or match.group("suffix_word"))
            amount = cast(
                str, match.group("prefix_amount") or match.group("suffix_amount")
            )
            matches.append(
                RecognitionMatch(
                    notation=MoneyNotation(
                        currency_part=word,
                        amount_part=amount,
                        currency_shape="word",
                        amount_shape=classify_amount_shape(amount),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
