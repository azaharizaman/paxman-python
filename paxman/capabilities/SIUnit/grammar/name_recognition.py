"""Name recognition grammar for SI Unit.

Recognizes unit names case-insensitively: the grammar folds the input
to lowercase and matches against the longest-first name token table
(D4). "Kilogram", "KILOGRAM", "kilogram" all emit a RecognitionMatch
over the span of the name text. Recognition only: no validation.
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.grammar.data.prefix_tokens import PREFIX_WORD_TOKENS
from paxman.capabilities.SIUnit.grammar.data.unit_name_tokens import NAME_TOKENS
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Prefix words for O(1) split detection (see recognize).
PREFIX_WORDS = frozenset(PREFIX_WORD_TOKENS)

# Same split-boundary structure as symbol_recognition: a lookbehind guards
# the left edge and a lookahead the right, so a token never merges with an
# adjacent word/separator/sign. Digits and underscore are blocked too (via
# \w), keeping quantity-adjacent names (e.g. "5kilogram") from being
# recognized — consistent with the symbol grammar's digit boundary.
_LOOKBEHIND = r"(?<![°\w\-+\u2212/·⋅])"
_LOOKAHEAD = r"(?![\w\-+\u2212/·⋅])"
_NAME_ALT = "|".join(re.escape(t) for t in NAME_TOKENS)
_PREFIX_WORD_ALT = "|".join(re.escape(t) for t in PREFIX_WORD_TOKENS)
# A word prefix split across whitespace from its unit ("kilo gram") is
# captured as ONE span so the inner unit ("gram") is consumed and never
# emitted as a competing candidate. finditer commits to the leftmost match,
# so "kilo gram" is grabbed whole and "gram" inside it is not separately
# recognized. A single outer named group wraps non-capturing alternatives:
# Python's re silently drops a leading lookbehind when named groups appear
# inside an alternation, so the split/name distinction is made by testing
# the matched text for a space rather than by named groups.
_NAME_BODY = (
    r"(?:(?:" + _PREFIX_WORD_ALT + r")\s+(?:" + _NAME_ALT + r"))"
    r"|"
    r"(?:" + _NAME_ALT + r")"
)
_NAME_RE = re.compile(
    _LOOKBEHIND + r"(?P<tok>" + _NAME_BODY + r")" + _LOOKAHEAD, re.IGNORECASE
)


class NameRecognition(Grammar[SIUnitNotation]):
    """Grammar: name_recognition — case-folded unit names."""

    name = "name_recognition"
    semantics = "name_recognition"  # SEAM (ADR-0003): identity id

    def recognize(self, text: str) -> list[RecognitionMatch[SIUnitNotation]]:
        """Emit one RecognitionMatch per unit name (or split prefix) found."""
        matches: list[RecognitionMatch[SIUnitNotation]] = []
        for m in _NAME_RE.finditer(text):
            token = m.group("tok").lower()
            parts = token.split()
            # A split prefix is a known prefix word followed by a space and a
            # unit name (e.g. "kilo gram"); a multi-word unit name like
            # "degree celsius" is NOT a split (its first word is not a prefix).
            if len(parts) >= 2 and parts[0] in PREFIX_WORDS:
                shape = "split_word_prefix"
            else:
                shape = "name"
            matches.append(
                RecognitionMatch(
                    raw_text=text[m.start() : m.end()],
                    start=m.start(),
                    end=m.end(),
                    notation=SIUnitNotation(text=token, shape=shape),
                )
            )
        return matches
