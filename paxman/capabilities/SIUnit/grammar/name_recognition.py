"""Name recognition grammar for SI Unit.

Recognizes unit names case-insensitively: the grammar folds the input
to lowercase and matches against the longest-first name token table
(D4). "Kilogram", "KILOGRAM", "kilogram" all emit a RecognitionMatch
over the span of the name text. Recognition only: no validation.
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.grammar.data.unit_name_tokens import NAME_TOKENS
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Same split-boundary structure as symbol_recognition: a combined
# `(?<!X)(?!X)` assertion before the token would reject it — the lookahead
# runs first and sees the token's own first letter (always [a-z] here).
_LOOKBEHIND = r"(?<![a-z])"
_LOOKAHEAD = r"(?![a-z])"
_ALTERNATION = "|".join(re.escape(t) for t in NAME_TOKENS)
_NAME_RE = re.compile(
    _LOOKBEHIND + r"(?P<name>" + _ALTERNATION + r")" + _LOOKAHEAD, re.IGNORECASE
)


class NameRecognition(Grammar[SIUnitNotation]):
    """Grammar: name_recognition — case-folded unit names."""

    name = "name_recognition"
    semantics = "name_recognition"  # SEAM (ADR-0003): identity id

    def recognize(self, text: str) -> list[RecognitionMatch[SIUnitNotation]]:
        """Emit one RecognitionMatch per unit name found in text."""
        return [
            RecognitionMatch(
                raw_text=text[m.start() : m.end()],
                start=m.start(),
                end=m.end(),
                notation=SIUnitNotation(text=m.group("name").lower(), shape="name"),
            )
            for m in _NAME_RE.finditer(text)
        ]
