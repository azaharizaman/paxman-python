"""US date grammar — recognizes MM/DD/YYYY format."""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_US_DATE_PATTERN = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


class USDateGrammar(Grammar[DateNotation]):
    """US date recognition: MM/DD/YYYY."""

    name = "us_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract US date patterns from text."""
        matches = _US_DATE_PATTERN.findall(text)
        return [
            DateNotation(day=day, month=month, year=year)
            for month, day, year in matches
        ]
