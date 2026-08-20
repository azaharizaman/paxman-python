"""US date recognition grammar (staged pipeline).

Recognizes MM/DD/YYYY and MM/DD/YY formats. The 4-digit and 2-digit year
variants are merged into one year-length alternation; the digit lookarounds
(via BoundaryGuard.digit()) keep the pattern disjoint from surrounding
digits. Notation mapping: N1=month, N2=day, N3=year.
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.grammar import BoundaryGuard, PipelineGrammar, RegexStage, StandardPre

_GUARD = BoundaryGuard.digit()
_US_PATTERN = (
    _GUARD.lookbehind + r"(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})" + _GUARD.lookahead
)


def _us_notation(match: re.Match[str]) -> DateNotation:
    """Map a US date match to its month/day/year notation."""
    return DateNotation(N1=match.group(1), N2=match.group(2), N3=match.group(3))


class USDateGrammar(PipelineGrammar[DateNotation]):
    """US date recognition: MM/DD/YYYY and MM/DD/YY.

    Both year-length variants carry digit lookarounds, so a date glued to
    surrounding digits (e.g. an ID like ``1201/02/2026``) is never partially
    matched.

    Notation mapping: N1=month, N2=day, N3=year
    """

    name = "us_recognition"
    semantics = "us_calendar_date"
    single_value = True

    pre = StandardPre[DateNotation](empty_guard=True)
    regex = RegexStage[DateNotation](pattern=_US_PATTERN, notation_fn=_us_notation)
