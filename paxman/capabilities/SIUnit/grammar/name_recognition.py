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

# Same split-boundary structure as symbol_recognition: a lookbehind guards
# the left edge and a lookahead the right, so a token never merges with an
# adjacent word/separator/sign. Digits and underscore are blocked too (via
# \w), keeping quantity-adjacent names (e.g. "5kilogram") from being
# recognized — consistent with the symbol grammar's digit boundary.
_LOOKBEHIND = r"(?<![°\w\-+\u2212/·⋅])"
_LOOKAHEAD = r"(?![\w\-+\u2212/·⋅])"
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
