"""CLDR currency display-name word recognition grammar (staged pipeline).

Recognizes a standalone currency display-name word (case-insensitive) as
one span-bearing token. The alternation is built from WORD_TOKENS
(longest-first) and guarded by word_sign boundaries; the token is emitted
lowercase so the rule is a pure lowercase-key table lookup. Syntax only.
"""

from __future__ import annotations

import re

from paxman.capabilities.Currency.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.grammar import (
    BoundaryGuard,
    LexiconStage,
    PipelineGrammar,
    StandardPre,
)


def _word_notation(token: str) -> CurrencyNotation:
    """Fold the matched display-name word to lowercase at recognition."""
    return CurrencyNotation(text=token.lower(), shape="word")


class WordRecognition(PipelineGrammar[CurrencyNotation]):
    """Recognizes standalone CLDR currency display-name word tokens.

    Matching is case-insensitive (``re.IGNORECASE`` on the guarded
    alternation); the emitted text is the token folded to lowercase so the
    rule's NAME_TO_CODES lookup is an exact lowercase-key hit. "Euro"/
    "euro"/"EURO" all emit text "euro". Word boundaries keep the match
    inside one token: "Dollars" does not match "Dollar".

    Examples: "Euro" -> text "euro", shape "word"
              "US Dollar" -> the "Dollar" span matches (text "dollar");
                  "US" (2 letters) matches nothing.
    Non-examples: "Dollars" (plural, blocked by the lookahead), "euro500"
        (amount-glued, blocked), "the" (not a display-name token).
    """

    name = "word_recognition"
    semantics = "word_recognition"
    single_value = True

    pre = StandardPre[CurrencyNotation](empty_guard=True)
    lexicon = LexiconStage(
        tokens=WORD_TOKENS,
        boundary=BoundaryGuard.word_sign(),
        longest_first=True,
        notation_fn=_word_notation,
        flags=re.IGNORECASE,
    )
