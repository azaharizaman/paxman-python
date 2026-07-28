"""Alpha-3 country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

_ALPHA3_PATTERN = re.compile(r"\b[A-Za-z]{3}\b")


class Alpha3Grammar(Grammar[CountryNotation]):
    """Recognizes exactly 3 ASCII letters as alpha-3 country code shape.

    Examples: "USA", "GBR", "usa", "gbr"
    Non-examples: "US" (2 letters), "123" (digits), "United" (6 letters)
    """

    name = "alpha3_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract alpha-3 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="alpha3".
        """
        if not text.strip():
            return []
        matches = _ALPHA3_PATTERN.findall(text)
        return [CountryNotation(shape="alpha3", value=m.upper()) for m in matches]
