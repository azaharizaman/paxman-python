"""ISO 3166-1:2024 numeric (M49) code validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.data import NUMERIC_TO_ALPHA2
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 3166-1:2024",
    kind="registry",
    reference_url="https://www.iso.org/guest/en/ISO3166-1/RegistrationTable/Active%20country%20list.html",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)


class SectionNumericCodes(Rule[CountryNotation]):
    """ISO 3166-1 Section: numeric (M49) codes.

    Validates numeric shape against the official list of 249 assigned codes.
    """

    name = "Section-numeric-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 numeric (M49) codes"

    def _normalize_key(self, value: str) -> str:
        """Zero-pad numeric value to 3 digits (M49 standard format)."""
        try:
            return f"{int(value):03d}"
        except ValueError:
            return value

    def matches(self, notation: CountryNotation, contract: Contract) -> bool:
        """Check if notation is a valid numeric code.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "numeric" AND value is in NUMERIC_TO_ALPHA2.
        """
        if notation.shape != "numeric":
            return False
        return self._normalize_key(notation.value) in NUMERIC_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: Contract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code.
        """
        return NUMERIC_TO_ALPHA2[self._normalize_key(notation.value)]
