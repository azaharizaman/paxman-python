"""ISO 4217 alpha-3 currency code recognition grammar (staged pipeline).

Recognizes a standalone 3-letter ASCII code shape (case-insensitive) as
one span-bearing token. Case folding is the grammar's concern (Country
alpha-2/alpha-3 precedent): the token is emitted uppercase so the rule is
a pure table lookup. Syntax only: unknown codes are still matched —
deciding validity is the rules' job.
"""

from __future__ import annotations

import re

from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.grammar import BoundaryGuard, PipelineGrammar, RegexStage, StandardPre


def _code_notation(match: re.Match[str]) -> CurrencyNotation:
    """Fold the matched 3-letter code to uppercase at recognition."""
    return CurrencyNotation(text=match.group(0).upper(), shape="code")


_GUARD = BoundaryGuard.word_sign()
_CODE_PATTERN = _GUARD.lookbehind + r"[A-Za-z]{3}" + _GUARD.lookahead


class CodeRecognition(PipelineGrammar[CurrencyNotation]):
    """Recognizes standalone ISO 4217 alpha-3 code shapes.

    Matches a 3-letter ASCII code in any casing: "USD", "usd", "Gbp".
    The grammar folds the token to uppercase at recognition; the rule
    validates against CURRENCY_CODES. Sign characters ('-', U+2212, '+')
    are outside the identifier grammar; the word_sign boundary guards
    reject sign-adjacent tokens (mirrors Money's code grammar).

    Examples: "USD" -> text "USD", shape "code"
              "usd" -> text "USD", shape "code"
    Non-examples: "USD500"/"USD-500" (amount/sign-glued: blocked by the
        lookarounds), "xUSD" (inside a longer token).
    """

    name = "code_recognition"
    semantics = "code_recognition"
    single_value = True

    pre = StandardPre[CurrencyNotation](empty_guard=True)
    regex = RegexStage(
        pattern=_CODE_PATTERN,
        notation_fn=_code_notation,
    )
