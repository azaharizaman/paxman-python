"""Country name recognition grammar.

Recognizes country name representations from per-locale key sets without
assigning canonical meaning. The input is normalized for membership only;
the trimmed input token is returned as the notation value. Provenance-backed
validation rules own every token-to-country decision.
"""

from __future__ import annotations

from paxman.capabilities.Country.grammar.data.chinese_names import (
    CHINESE_NAME_KEYS,
)
from paxman.capabilities.Country.grammar.data.english_names import (
    ENGLISH_NAME_KEYS,
)
from paxman.capabilities.Country.grammar.data.historical_names import (
    HISTORICAL_NAME_KEYS,
)
from paxman.capabilities.Country.grammar.data.localized_names import (
    LOCALIZED_NAME_KEYS,
)
from paxman.capabilities.Country.name_normalization import normalize_name
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

# Union of every recognized name representation across locales.
_KNOWN_NAME_KEYS = (
    ENGLISH_NAME_KEYS | HISTORICAL_NAME_KEYS | CHINESE_NAME_KEYS | LOCALIZED_NAME_KEYS
)


class NameGrammar(Grammar[CountryNotation]):
    """Recognizes country name representations from recognition key sets.

    Decides whether an input is a known country name representation and
    returns it unchanged as the notation value. It does not resolve names
    to canonical countries — validation rules assign meaning with
    provenance.

    Examples: "United States" → value="United States"
              "USA" → value="USA"
              "中国" → value="中国"
              "Alemania" → value="Alemania"
              "Burma" → value="Burma"
    Non-examples: "840" → [] (no name match)
                  "" → [] (empty)
                  "XYZ" → [] (unknown name)
    """

    name = "name_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract a country name representation from text.

        Args:
            text: Raw input text.

        Returns:
            A list with a single CountryNotation of shape="name" carrying
            the trimmed input token when the token is a known name
            representation, or an empty list for empty/unknown input.
        """
        trimmed = text.strip()
        if not trimmed:
            return []

        normalized = normalize_name(trimmed)

        if normalized in _KNOWN_NAME_KEYS:
            return [CountryNotation(shape="name", value=trimmed)]

        return []
