"""ISSN recognition grammar — regex structural pattern matching."""

import re

from paxman.capabilities.ISSN.notation import ISSNNotation
from paxman.core.grammar.boundary import BoundaryGuard
from paxman.core.grammar.pipeline import PipelineGrammar
from paxman.core.grammar.stages import RegexStage, StandardPre

_ISSN_BODY = r"(?:ISSN(?:-L|-H)?[\s:-]*)?(?P<body>\d{4}-?\d{3}[0-9Xx])"
_ISSN_PATTERN: str = (
    BoundaryGuard.digit().lookbehind
    + _ISSN_BODY
    + BoundaryGuard.digit().lookahead
    + r"\b"
)


def _issn_notation(match: re.Match[str]) -> ISSNNotation:
    raw_body = match.group("body")
    digits = "".join(ch for ch in raw_body if ch in "0123456789Xx").upper()
    return ISSNNotation(digits=digits)


class ISSNRecognitionGrammar(PipelineGrammar[ISSNNotation]):
    """ISSN recognition: 8-char identifier with optional label."""

    name = "issn_recognition"
    semantics = "issn_recognition"
    single_value = True
    pre = StandardPre[ISSNNotation](empty_guard=True)
    regex = RegexStage[ISSNNotation](
        pattern=_ISSN_PATTERN, notation_fn=_issn_notation, flags=re.IGNORECASE
    )
