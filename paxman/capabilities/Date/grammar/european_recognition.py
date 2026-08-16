"""European date grammar — recognizes DD/MM/YYYY and DD/MM/YY formats.

Notation mapping: N1=day, N2=month, N3=year
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar, RecognitionMatch

_EUROPEAN_DATE_PATTERN_4DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")
_EUROPEAN_DATE_PATTERN_2DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)")


class EuropeanDateGrammar(Grammar[DateNotation]):
    """European date recognition: DD/MM/YYYY and DD/MM/YY.

    Both year-length variants carry digit lookarounds, so a date glued to
    surrounding digits (e.g. an ID like ``1201/02/2026``) is never partially
    matched.

    Notation mapping: N1=day, N2=month, N3=year
    """

    name = "european_recognition"
    semantics = "european_calendar_date"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        """Extract European date patterns from text.

        Emits spans for every pattern match; the engine orders by document
        position and resolves overlapping 2-digit/4-digit year spans via
        span dedup.
        """
        results: list[RecognitionMatch[DateNotation]] = []

        for match in _EUROPEAN_DATE_PATTERN_4DIGIT.finditer(text):
            day, month, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=day, N2=month, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )

        for match in _EUROPEAN_DATE_PATTERN_2DIGIT.finditer(text):
            day, month, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=day, N2=month, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )

        return results
