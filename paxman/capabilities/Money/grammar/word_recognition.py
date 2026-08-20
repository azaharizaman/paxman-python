"""CLDR currency display-name word recognition grammar (staged pipeline).

Recognizes a currency display-name word adjacent to an amount, in either
order, as one span-bearing token. The word alternation is built from
WORD_TOKENS (longest-first), word-boundary anchored and case-insensitive,
and fused with the amount by ``AmountComposer`` (S4). Syntax only:
resolving the word to a code is the rules' job.
"""

from __future__ import annotations

import re

from paxman.capabilities.Money.grammar import AMOUNT_PATTERN, classify_amount_shape
from paxman.capabilities.Money.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.grammar import (
    AmountComposer,
    BoundaryGuard,
    PipelineGrammar,
    StandardPre,
)


def _word_notation(lex: str, amount: str, amount_shape: str) -> MoneyNotation:
    """Map a matched word+amount token to its notation."""
    return MoneyNotation(
        currency_part=lex,
        amount_part=amount,
        currency_shape="word",
        amount_shape=amount_shape,
    )


class WordRecognition(PipelineGrammar[MoneyNotation]):
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
    single_value = True

    pre = StandardPre[MoneyNotation](empty_guard=True)
    composer = AmountComposer[MoneyNotation](
        pattern=AMOUNT_PATTERN,
        lexicon_tokens=WORD_TOKENS,
        notation_fn=_word_notation,
        classify=classify_amount_shape,
        boundary=BoundaryGuard.word_sign(),
        flags=re.IGNORECASE,
    )
