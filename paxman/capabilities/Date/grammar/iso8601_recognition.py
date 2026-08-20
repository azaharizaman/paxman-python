"""ISO 8601 date recognition grammar (staged pipeline).

Recognizes YYYY-MM-DD format. The digit lookarounds are supplied by
BoundaryGuard.digit() (ADR-0008 D5) so no hard-coded lookaround literal
remains in this file. Notation mapping: N1=year, N2=month, N3=day.
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.grammar import BoundaryGuard, PipelineGrammar, RegexStage, StandardPre

_GUARD = BoundaryGuard.digit()
_ISO8601_PATTERN = _GUARD.lookbehind + r"(\d{4})-(\d{2})-(\d{2})" + _GUARD.lookahead


def _iso_notation(match: re.Match[str]) -> DateNotation:
    """Map an ISO 8601 match to its year/month/day notation."""
    return DateNotation(N1=match.group(1), N2=match.group(2), N3=match.group(3))


class ISO8601DateGrammar(PipelineGrammar[DateNotation]):
    """ISO 8601 date recognition: YYYY-MM-DD.

    Digit lookarounds keep the pattern disjoint from surrounding digits, so a
    longer digit run (e.g. an ID like ``12026-01-15``) is never partially
    matched as a date, mirroring the other shipped date grammars.

    Notation mapping: N1=year, N2=month, N3=day
    """

    name = "iso8601_recognition"
    semantics = "iso8601_calendar_date"
    single_value = True

    pre = StandardPre[DateNotation](empty_guard=True)
    regex = RegexStage[DateNotation](
        pattern=_ISO8601_PATTERN, notation_fn=_iso_notation
    )
