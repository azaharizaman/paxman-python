"""Compound recognition grammar for SI Unit.

Recognizes product/quotient compound shapes over unit symbols: UNIT
(separator UNIT){1,3} where each UNIT is a symbol character run with an
optional exponent, and the separator is "/", "·" or "⋅" (D3). The
grammar is shape-only: it does not validate that the units are known
(the ISO 80000-1 rule does that). "m/s²", "N·m", "kg·m/s²", "g/cm³"
are recognized as single spans; "m s" (space) is not a compound.
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.grammar.data.compound_tokens import (
    COMPOUND_SEPARATORS,
    EXPONENT_CHARACTERS,
)
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Shape constants come from the Task 4 generated module (grammars may import
# from grammar/data/ — only rules are barred by the grammar↔rules purity
# scan). Keeps the separator/exponent characters in one place.
_EXPONENT = rf"[{EXPONENT_CHARACTERS}]*"
_UNIT = rf"(?:°?[A-Za-zµΩÅ][A-Za-zµΩÅ0-9]*{_EXPONENT})"
_SEP = f"[{COMPOUND_SEPARATORS}]"
# A factor is either a bare unit or a parenthesized group of 1–4 units
# joined by separators. ISO 80000-1 §6.6.2 prescribes parentheses as the
# disambiguation for a solidus followed by another separator, so a
# parenthesized denominator is a single compound factor (e.g. "(m·s²)").
_FACTOR = rf"(?:{_UNIT}|\({_UNIT}(?:{_SEP}{_UNIT}){{0,3}}\))"
_COMPOUND_RE = re.compile(
    rf"(?<![\w\-+\u2212])(?P<body>{_FACTOR}(?:{_SEP}{_FACTOR}){{1,3}})(?![\w\-+\u2212])"
)


class CompoundRecognition(Grammar[SIUnitNotation]):
    """Grammar: compound_recognition — product/quotient unit shapes."""

    name = "compound_recognition"
    semantics = "compound_recognition"  # SEAM (ADR-0003): identity id

    def recognize(self, text: str) -> list[RecognitionMatch[SIUnitNotation]]:
        """Emit one RecognitionMatch per compound shape found in text."""
        return [
            RecognitionMatch(
                raw_text=text[m.start() : m.end()],
                start=m.start(),
                end=m.end(),
                notation=SIUnitNotation(text=m.group("body"), shape="compound"),
            )
            for m in _COMPOUND_RE.finditer(text)
        ]
