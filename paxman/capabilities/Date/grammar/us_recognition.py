"""US date grammar — recognizes MM/DD/YYYY and MM/DD/YY formats.

Notation mapping: N1=month, N2=day, N3=year
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_US_DATE_PATTERN_4DIGIT = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_US_DATE_PATTERN_2DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)")


class USDateGrammar(Grammar[DateNotation]):
    """US date recognition: MM/DD/YYYY and MM/DD/YY.

    Notation mapping: N1=month, N2=day, N3=year
    """

    name = "us_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract US date patterns from text.

        Avoids duplicates: if a 2-digit year match falls within a 4-digit
        year match's span, only the 4-digit match is kept.
        """
        results: list[DateNotation] = []
        four_digit_ranges: list[tuple[int, int]] = []

        for match in _US_DATE_PATTERN_4DIGIT.finditer(text):
            month, day, year = match.group(1), match.group(2), match.group(3)
            four_digit_ranges.append((match.start(), match.end()))
            results.append(DateNotation(N1=month, N2=day, N3=year))

        for match in _US_DATE_PATTERN_2DIGIT.finditer(text):
            start, end = match.start(), match.end()
            if any(start >= fs and end <= fe for fs, fe in four_digit_ranges):
                continue
            month, day, year = match.group(1), match.group(2), match.group(3)
            results.append(DateNotation(N1=month, N2=day, N3=year))

        return results
