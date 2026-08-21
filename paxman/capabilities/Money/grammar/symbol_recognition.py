"""CLDR currency symbol recognition grammar (staged pipeline).

Recognizes a currency symbol token adjacent to an amount, in either
order, as one span-bearing token. The symbol alternation is built from
SYMBOL_TOKENS (qualified forms first, longest-first within each class,
so "US$" alternates before "$") and fused with the amount by
``AmountComposer`` (S4). Syntax only: resolving the symbol to a code is
the rules' job.
"""

from __future__ import annotations

from paxman.capabilities.Money.grammar import AMOUNT_PATTERN, classify_amount_shape
from paxman.capabilities.Money.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.grammar import (
    AmountComposer,
    BoundaryGuard,
    PipelineGrammar,
    StandardPre,
)


def _is_qualified(token: str) -> bool:
    """A symbol is qualified when it contains an ASCII letter (US$, RM)."""
    return any(ch.isascii() and ch.isalpha() for ch in token)


def _symbol_notation(lex: str, amount: str, amount_shape: str) -> MoneyNotation:
    """Map a matched symbol+amount token to its qualified/bare notation."""
    return MoneyNotation(
        currency_part=lex,
        amount_part=amount,
        currency_shape="qualified_symbol" if _is_qualified(lex) else "symbol",
        amount_shape=amount_shape,
    )


class SymbolRecognition(PipelineGrammar[MoneyNotation]):
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
    semantics = "symbol_recognition"
    single_value = True

    pre = StandardPre[MoneyNotation](empty_guard=True)
    composer = AmountComposer[MoneyNotation](
        pattern=AMOUNT_PATTERN,
        lexicon_tokens=SYMBOL_TOKENS,
        notation_fn=_symbol_notation,
        classify=classify_amount_shape,
        boundary=BoundaryGuard.word_sign(),
        flags=0,
    )
