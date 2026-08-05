"""US date grammar — recognizes MM/DD/YYYY and MM/DD/YY formats.

Notation mapping: N1=month, N2=day, N3=year
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar, RecognitionMatch

_US_DATE_PATTERN_4DIGIT = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_US_DATE_PATTERN_2DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)")


class USDateGrammar(Grammar[DateNotation]):
    """US date recognition: MM/DD/YYYY and MM/DD/YY.

    Notation mapping: N1=month, N2=day, N3=year
    """

    name = "us_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        """Extract US date patterns from text.

        Emits spans for every pattern match; the engine resolves
        overlapping 2-digit/4-digit year spans via span dedup.
        """
        results: list[RecognitionMatch[DateNotation]] = []

        for match in _US_DATE_PATTERN_4DIGIT.finditer(text):
            month, day, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=month, N2=day, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )

        for match in _US_DATE_PATTERN_2DIGIT.finditer(text):
            month, day, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=month, N2=day, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )

        return results
