"""Numeric (M49) country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

_NUMERIC_PATTERN = re.compile(r"\b\d{1,3}\b")


class NumericGrammar(Grammar[CountryNotation]):
    """Recognizes 1-3 digits as numeric country code shape.

    Examples: "840", "4", "004"
    Non-examples: "US" (letters), "1234" (4 digits), "12a" (alphanumeric)
    """

    name = "numeric_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract numeric patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="numeric".
        """
        if not text.strip():
            return []
        matches = _NUMERIC_PATTERN.findall(text)
        return [CountryNotation(shape="numeric", value=m) for m in matches]
