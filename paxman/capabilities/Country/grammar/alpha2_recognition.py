"""Alpha-2 country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

_ALPHA2_PATTERN = re.compile(r"\b[A-Za-z]{2}\b")


class Alpha2Grammar(Grammar[CountryNotation]):
    """Recognizes exactly 2 ASCII letters as alpha-2 country code shape.

    Examples: "US", "GB", "us", "gB"
    Non-examples: "USA" (3 letters), "12" (digits), "U" (1 letter)
    """

    name = "alpha2_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract alpha-2 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="alpha2".
        """
        if not text.strip():
            return []
        matches = _ALPHA2_PATTERN.findall(text)
        return [CountryNotation(shape="alpha2", value=m.upper()) for m in matches]
