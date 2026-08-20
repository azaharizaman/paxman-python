"""ISBN-13 recognition grammar (staged pipeline).

Recognizes 13-digit ISBNs with optional label and separators. The trailing
separator guard is supplied by BoundaryGuard.isbn_trail() (ADR-0008 D5) so no
hard-coded lookaround literal remains in this file. The hyphen/space tolerance
is regex-native (the lookahead extracts the digit run via a backreference).
"""

from __future__ import annotations

import re

from paxman.capabilities.ISBN.notation import ISBNNotation
from paxman.core.grammar import BoundaryGuard, PipelineGrammar, RegexStage, StandardPre

_ISBN13_BODY = r"\b(?:ISBN(?:-13)?[\s:-]+)?(?=((?:\d[ -]?){12}\d)(?![\d]))\1"
_GUARD = BoundaryGuard.isbn_trail()
_ISBN13_PATTERN = _ISBN13_BODY + _GUARD.lookbehind + r"\b"


def _isbn13_notation(match: re.Match[str]) -> ISBNNotation:
    """Map an ISBN-13 match to its digit-string notation."""
    digits = "".join(ch for ch in match.group(1) if ch in "0123456789")
    return ISBNNotation(shape="isbn13", digits=digits)


class ISBN13RecognitionGrammar(PipelineGrammar[ISBNNotation]):
    """ISBN-13 recognition: 13-digit ISBN with optional label and separators."""

    name = "isbn13_recognition"
    semantics = "isbn13_recognition"
    single_value = True

    pre = StandardPre[ISBNNotation](empty_guard=True)
    regex = RegexStage[ISBNNotation](
        pattern=_ISBN13_PATTERN, notation_fn=_isbn13_notation, flags=re.IGNORECASE
    )
