"""Country name recognition grammar.

Uses per-locale lookup tables to recognize country names and variants
and resolve them to their canonical ISO 3166-1 English short names (or
historical canonical names for historical entities).

Lookup order: English → Historical → Chinese — first match wins.
"""

from __future__ import annotations

import re
import unicodedata

from paxman.capabilities.Country.grammar.data.chinese_names import (
    CHINESE_NAME_TO_CANONICAL,
)
from paxman.capabilities.Country.grammar.data.english_names import (
    ENGLISH_NAME_TO_CANONICAL,
)
from paxman.capabilities.Country.grammar.data.historical_names import (
    HISTORICAL_NAME_TO_CANONICAL,
)
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

# Compiled normalizer: keep only letters, digits, and whitespace
# (strip punctuation and other symbols).
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Normalize input for lookup table matching.

    NFKD-decomposes (splits accented chars like ô → o + combining mark),
    strips combining marks and punctuation, collapses whitespace, and
    uppercases. Unicode letters (including CJK) and digits are preserved.

    Args:
        text: Raw input text.

    Returns:
        Normalized key for table lookup.
    """
    # NFKD decompose: "ô" → "o" + combining circumflex
    decomposed = unicodedata.normalize("NFKD", text)
    # Keep only alphanumeric and whitespace (strips combining marks + punctuation)
    cleaned = "".join(c for c in decomposed if c.isalnum() or c.isspace())
    # Collapse whitespace
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    # Uppercase
    return cleaned.upper().strip()


class NameGrammar(Grammar[CountryNotation]):
    """Recognizes country names from lookup tables.

    Matches input against English, historical, and Chinese name tables.
    Returns the canonical ISO English short name (or historical canonical
    name for historical entities) as the notation value.

    Unlike the other country grammars (alpha2, alpha3, numeric), this
    grammar resolves names to their canonical form at recognition time.
    This is intentional — names have multiple valid forms (e.g., "USA",
    "America", "United States of America") that all resolve to the same
    canonical value ("United States"), and resolution at the grammar layer
    simplifies downstream validation.

    Examples: "United States" → value="United States"
              "USA" → value="United States"
              "US" → value="United States"
              "中国" → value="China"
              "Burma" → value="BURMA"
    Non-examples: "840" → [] (no name match)
                  "" → [] (empty)
                  "XYZ" → [] (unknown name)
    """

    name = "name_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract country names from text via lookup tables.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="name" and the canonical
            name as value, or empty list if input is empty/unknown.
        """
        trimmed = text.strip()
        if not trimmed:
            return []

        normalized = _normalize(trimmed)

        # Lookup order: English → Historical → Chinese
        if normalized in ENGLISH_NAME_TO_CANONICAL:
            return [
                CountryNotation(
                    shape="name", value=ENGLISH_NAME_TO_CANONICAL[normalized]
                )
            ]

        if normalized in HISTORICAL_NAME_TO_CANONICAL:
            return [
                CountryNotation(
                    shape="name", value=HISTORICAL_NAME_TO_CANONICAL[normalized]
                )
            ]

        if normalized in CHINESE_NAME_TO_CANONICAL:
            return [
                CountryNotation(
                    shape="name", value=CHINESE_NAME_TO_CANONICAL[normalized]
                )
            ]

        return []
