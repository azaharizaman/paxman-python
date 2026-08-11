"""ISO 8601 date grammar — recognizes YYYY-MM-DD format.

Notation mapping: N1=year, N2=month, N3=day
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar, RecognitionMatch

_ISO8601_PATTERN = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")


class ISO8601DateGrammar(Grammar[DateNotation]):
    """ISO 8601 date recognition: YYYY-MM-DD.

    Digit lookarounds keep the pattern disjoint from surrounding digits, so a
    longer digit run (e.g. an ID like ``12026-01-15``) is never partially
    matched as a date, mirroring the other shipped date grammars.

    Notation mapping: N1=year, N2=month, N3=day
    """

    name = "iso8601_recognition"
    semantics = "iso8601_calendar_date"

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        """Extract ISO 8601 date patterns from text."""
        return [
            RecognitionMatch(
                notation=DateNotation(N1=year, N2=month, N3=day),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _ISO8601_PATTERN.finditer(text)
            for year, month, day in [match.groups()]
        ]
