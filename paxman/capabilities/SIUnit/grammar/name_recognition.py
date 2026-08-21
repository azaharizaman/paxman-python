"""Name recognition grammar for SI Unit (staged pipeline).

Recognizes unit names case-insensitively: the grammar folds the input
to lowercase and matches against the longest-first name token table
(D4). "Kilogram", "KILOGRAM", "kilogram" all emit a RecognitionMatch
over the span of the name text. Recognition only: no validation.

The single bespoke regex from the legacy grammar is reproduced exactly
as a ``RegexStage`` body (with ``re.IGNORECASE``) guarded by
``BoundaryGuard.degree_word_sign()``. The split-prefix shape
("kilo gram" -> ``split_word_prefix``) is computed inline in the
notation factory, byte-identically to the legacy ``recognize()``.
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.grammar.data.prefix_tokens import PREFIX_WORD_TOKENS
from paxman.capabilities.SIUnit.grammar.data.unit_name_tokens import NAME_TOKENS
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.grammar import BoundaryGuard, PipelineGrammar, RegexStage, StandardPre

# Prefix words for O(1) split detection (see recognize).
PREFIX_WORDS = frozenset(PREFIX_WORD_TOKENS)

# Same split-boundary structure as symbol_recognition: a lookbehind guards
# the left edge and a lookahead the right, so a token never merges with an
# adjacent word/separator/sign. Digits and underscore are blocked too (via
# \w), keeping quantity-adjacent names (e.g. "5kilogram") from being
# recognized — consistent with the symbol grammar's digit boundary.
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
# The degree_word_sign guard preserves the ° in the lookbehind exactly as the
# legacy grammar's _LOOKBEHIND/_LOOKAHEAD literals did — no hard-coded
# lookaround in this file (ADR-0008 D5). re.IGNORECASE reproduces the legacy
# case-insensitive name match.
_GUARD = BoundaryGuard.degree_word_sign()
_NAME_PATTERN = _GUARD.lookbehind + r"(?P<tok>" + _NAME_BODY + r")" + _GUARD.lookahead


def _name_notation(match: re.Match[str]) -> SIUnitNotation:
    """Map a matched name token to its split/attached notation.

    Mirrors the legacy recognize(): the matched text is folded to lowercase;
    a known prefix word followed by a space and a unit name (e.g. "kilo gram")
    is a rejectable split, while a multi-word unit name like "degree celsius"
    is a plain name (its first word is not a prefix).
    """
    token = match.group("tok").lower()
    parts = token.split()
    if len(parts) >= 2 and parts[0] in PREFIX_WORDS:
        shape = "split_word_prefix"
    else:
        shape = "name"
    return SIUnitNotation(text=token, shape=shape)


class NameRecognition(PipelineGrammar[SIUnitNotation]):
    """Grammar: name_recognition — case-folded unit names."""

    name = "name_recognition"
    semantics = "name_recognition"  # SEAM (ADR-0003): identity id

    pre = StandardPre[SIUnitNotation](empty_guard=True)
    regex = RegexStage[SIUnitNotation](
        pattern=_NAME_PATTERN,
        notation_fn=_name_notation,
        flags=re.IGNORECASE,
    )
