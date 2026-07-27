"""ISO 8601 date grammar — recognizes YYYY-MM-DD format.

Notation mapping: N1=year, N2=month, N3=day
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_ISO8601_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class ISO8601DateGrammar(Grammar[DateNotation]):
    """ISO 8601 date recognition: YYYY-MM-DD.

    Notation mapping: N1=year, N2=month, N3=day
    """

    name = "iso8601_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract ISO 8601 date patterns from text."""
        matches = _ISO8601_PATTERN.findall(text)
        return [DateNotation(N1=year, N2=month, N3=day) for year, month, day in matches]
