"""Country name recognition grammar."""

from __future__ import annotations

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar


class NameGrammar(Grammar[CountryNotation]):
    """Recognizes any non-empty string as country name shape.

    Design note: This grammar matches ANY non-empty input, including values
    that might also match alpha2/alpha3/numeric grammars. This is intentional —
    multiple grammars matching the same input is fine because:
    - Each grammar produces a separate notation with the appropriate shape
    - Rules validate based on shape (e.g., SectionAlpha2Codes only accepts shape="alpha2")
    - Multiple candidates with the same canonical value produce SUCCESS, not AMBIGUOUS

    Examples: "United States", "马来西亚", "Burma", "US" (also matched by alpha2)
    Non-examples: "" (empty)
    """

    name = "name_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract name patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="name".
        """
        trimmed = text.strip()
        if not trimmed:
            return []
        return [CountryNotation(shape="name", value=trimmed)]
