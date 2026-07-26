"""ISO 8601 date grammar — recognizes YYYY-MM-DD format."""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_ISO8601_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class ISO8601DateGrammar(Grammar[DateNotation]):
    """ISO 8601 date recognition: YYYY-MM-DD."""

    name = "iso8601_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract ISO 8601 date patterns from text."""
        matches = _ISO8601_PATTERN.findall(text)
        return [
            DateNotation(day=day, month=month, year=year)
            for year, month, day in matches
        ]
