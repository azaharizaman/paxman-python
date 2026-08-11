"""Numeric (M49) country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar, RecognitionMatch

_NUMERIC_PATTERN = re.compile(r"\b\d{1,3}\b")


class NumericGrammar(Grammar[CountryNotation]):
    """Recognizes 1-3 digits as numeric country code shape.

    Examples: "840", "4", "004"
    Non-examples: "US" (letters), "1234" (4 digits), "12a" (alphanumeric)
    """

    name = "numeric_recognition"
    semantics = "numeric_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        """Extract numeric patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of span-bearing matches with shape="numeric" notations.
        """
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CountryNotation]] = []
        for match in _NUMERIC_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CountryNotation(shape="numeric", value=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
