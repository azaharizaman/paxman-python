"""ISO 8601 date grammar — recognizes YYYY-MM-DD format.

Notation mapping: N1=year, N2=month, N3=day
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar, RecognitionMatch

_ISO8601_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class ISO8601DateGrammar(Grammar[DateNotation]):
    """ISO 8601 date recognition: YYYY-MM-DD.

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
