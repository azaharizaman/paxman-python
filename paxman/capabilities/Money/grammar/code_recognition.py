"""ISO 4217 alpha-3 currency code recognition grammar (staged pipeline).

Recognizes an ISO 4217 alpha-3 code shape adjacent to an amount, in
either order, as one span-bearing token. The fused either-order regex is
built by ``AmountComposer`` (S4): a 3-letter uppercase ASCII code
adjacent to an amount, prefix ("USD500", "USD 500") or suffix ("500 USD",
"100MYR"). Syntax only: unknown codes are still matched — deciding
validity is the rules' job.
"""

from __future__ import annotations

from paxman.capabilities.Money.grammar import AMOUNT_PATTERN, classify_amount_shape
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.grammar import (
    AmountComposer,
    BoundaryGuard,
    PipelineGrammar,
    StandardPre,
)


def _code_notation(lex: str, amount: str, amount_shape: str) -> MoneyNotation:
    """Map a matched code+amount token to its notation."""
    return MoneyNotation(
        currency_part=lex,
        amount_part=amount,
        currency_shape="code",
        amount_shape=amount_shape,
    )


class CodeRecognition(PipelineGrammar[MoneyNotation]):
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
    semantics = "code_recognition"
    single_value = True

    pre = StandardPre[MoneyNotation](empty_guard=True)
    composer = AmountComposer[MoneyNotation](
        pattern=AMOUNT_PATTERN,
        lexicon_tokens=None,
        notation_fn=_code_notation,
        classify=classify_amount_shape,
        boundary=BoundaryGuard.word_sign(),
        flags=0,
    )
