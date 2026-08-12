"""Alpha-2 country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar, RecognitionMatch

_ALPHA2_PATTERN = re.compile(r"\b[A-Za-z]{2}\b")


class Alpha2Grammar(Grammar[CountryNotation]):
    """Recognizes exactly 2 ASCII letters as alpha-2 country code shape.

    Examples: "US", "GB", "us", "gB"
    Non-examples: "USA" (3 letters), "12" (digits), "U" (1 letter)
    """

    name = "alpha2_recognition"
    semantics = "alpha2_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        """Extract alpha-2 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape="alpha2" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CountryNotation]] = []
        for match in _ALPHA2_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CountryNotation(
                        shape="alpha2", value=match.group(0).upper()
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
