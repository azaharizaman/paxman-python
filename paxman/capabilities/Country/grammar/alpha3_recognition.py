"""Alpha-3 country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar, RecognitionMatch

_ALPHA3_PATTERN = re.compile(r"\b[A-Za-z]{3}\b")


class Alpha3Grammar(Grammar[CountryNotation]):
    """Recognizes exactly 3 ASCII letters as alpha-3 country code shape.

    Examples: "USA", "GBR", "usa", "gbr"
    Non-examples: "US" (2 letters), "123" (digits), "United" (6 letters)
    """

    name = "alpha3_recognition"
    semantics = "alpha3_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        """Extract alpha-3 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape="alpha3" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CountryNotation]] = []
        for match in _ALPHA3_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CountryNotation(
                        shape="alpha3", value=match.group(0).upper()
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
