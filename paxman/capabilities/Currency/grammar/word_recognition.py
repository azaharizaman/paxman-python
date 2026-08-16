"""CLDR currency display-name word recognition grammar.

Recognizes a standalone currency display-name word (case-insensitive) as
one span-bearing token. The alternation is built from WORD_TOKENS
(longest-first). Case folding is the grammar's concern (Country/ISBN
precedent): the token is emitted lowercase so the rule is a pure
lowercase-key table lookup. Syntax only.
"""

from __future__ import annotations

import re

from paxman.capabilities.Currency.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.domain import Grammar, RecognitionMatch

_WORD_ALTERNATION = "|".join(re.escape(token) for token in WORD_TOKENS)
_WORD_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])(?:{_WORD_ALTERNATION})(?![\w\-+\u2212])",
    re.IGNORECASE,
)


class WordRecognition(Grammar[CurrencyNotation]):
    """Recognizes standalone CLDR currency display-name word tokens.

    Matching is case-insensitive; the emitted text is the token folded to
    lowercase so the rule's NAME_TO_CODES lookup is an exact lowercase-key
    hit. "Euro"/"euro"/"EURO" all emit text "euro". Word boundaries keep
    the match inside one token: "Dollars" does not match "Dollar".

    Examples: "Euro" -> text "euro", shape "word"
              "US Dollar" -> the "Dollar" span matches (text "dollar");
                  "US" (2 letters) matches nothing.
    Non-examples: "Dollars" (plural, blocked by the lookahead), "euro500"
        (amount-glued, blocked), "the" (not a display-name token).
    """

    name = "word_recognition"
    semantics = "word_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CurrencyNotation]]:
        """Extract standalone display-name word tokens from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape "word" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CurrencyNotation]] = []
        for match in _WORD_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CurrencyNotation(
                        text=match.group(0).lower(),
                        shape="word",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
