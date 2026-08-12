"""Symbol recognition grammar for SI Unit.

Recognizes unit symbols exactly as written (case-exact): base symbols
("m", "kg"), derived special-name symbols ("Pa", "°C"), non-SI symbols
("min", "L"), prefix symbols ("k", "M") and prefixed units ("km", "MHz").
Each recognition emits a span-bearing RecognitionMatch over the symbol
text. Recognition only: no validation, no canonicalization (D1/D2/D6).
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.grammar.data.unit_symbol_tokens import SYMBOL_TOKENS
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Word chars, signs, and the compound separators block a token: they
# never merge into a symbol and never split a compound (D2). The degree
# sign is in the block set too, so "25°C" cannot fall back to a bare "C"
# (coulomb) after the "°C" token is rejected. The left boundary is a
# lookbehind and the right a lookahead — a lookahead placed before the
# token would see the token's own first character (a word char) and
# reject the match before the token is even consumed.
_LOOKBEHIND = r"(?<![°\w\-+\u2212/·⋅])"
_LOOKAHEAD = r"(?![\w\-+\u2212/·⋅])"
_ALTERNATION = "|".join(re.escape(t) for t in SYMBOL_TOKENS)
_TOKEN_RE = re.compile(_LOOKBEHIND + r"(?P<token>" + _ALTERNATION + r")" + _LOOKAHEAD)


class SymbolRecognition(Grammar[SIUnitNotation]):
    """Grammar: symbol_recognition — case-exact unit symbol tokens."""

    name = "symbol_recognition"
    semantics = "symbol_recognition"  # SEAM (ADR-0003): identity id

    def recognize(self, text: str) -> list[RecognitionMatch[SIUnitNotation]]:
        """Emit one RecognitionMatch per symbol token found in text."""
        return [
            RecognitionMatch(
                raw_text=text[m.start() : m.end()],
                start=m.start(),
                end=m.end(),
                notation=SIUnitNotation(text=m.group("token"), shape="symbol"),
            )
            for m in _TOKEN_RE.finditer(text)
        ]
