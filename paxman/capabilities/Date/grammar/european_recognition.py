"""European date grammar — recognizes DD.MM.YYYY format."""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_EUROPEAN_DATE_PATTERN = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")


class EuropeanDateGrammar(Grammar[DateNotation]):
    """European date recognition: DD.MM.YYYY."""

    name = "european_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract European date patterns from text."""
        matches = _EUROPEAN_DATE_PATTERN.findall(text)
        return [
            DateNotation(day=day, month=month, year=year)
            for day, month, year in matches
        ]
