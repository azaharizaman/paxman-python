"""European date grammar — recognizes DD/MM/YYYY and DD/MM/YY formats.

Notation mapping: N1=day, N2=month, N3=year
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_EUROPEAN_DATE_PATTERN_4DIGIT = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_EUROPEAN_DATE_PATTERN_2DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)")


class EuropeanDateGrammar(Grammar[DateNotation]):
    """European date recognition: DD/MM/YYYY and DD/MM/YY.

    Notation mapping: N1=day, N2=month, N3=year
    """

    name = "european_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract European date patterns from text.

        Preserves recognition order from input. Avoids duplicates: if a
        2-digit year match falls within a 4-digit year match's span, only
        the 4-digit match is kept.
        """
        # Collect all matches with position info for ordering
        all_matches: list[tuple[int, DateNotation]] = []

        for match in _EUROPEAN_DATE_PATTERN_4DIGIT.finditer(text):
            day, month, year = match.group(1), match.group(2), match.group(3)
            all_matches.append((match.start(), DateNotation(N1=day, N2=month, N3=year)))

        four_digit_ranges = [
            (m.start(), m.end()) for m in _EUROPEAN_DATE_PATTERN_4DIGIT.finditer(text)
        ]

        for match in _EUROPEAN_DATE_PATTERN_2DIGIT.finditer(text):
            start, end = match.start(), match.end()
            if any(start >= fs and end <= fe for fs, fe in four_digit_ranges):
                continue
            day, month, year = match.group(1), match.group(2), match.group(3)
            all_matches.append((match.start(), DateNotation(N1=day, N2=month, N3=year)))

        # Sort by position to preserve input order
        all_matches.sort(key=lambda x: x[0])
        return [notation for _, notation in all_matches]
