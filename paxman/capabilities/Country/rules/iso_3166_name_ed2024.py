"""ISO 3166-1:2024 official name validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.data import NAME_TO_ALPHA2
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


class SectionNames(Rule[CountryNotation]):
    """ISO 3166-1 Section: official English short names.

    Validates name shape against the official list of 249 assigned names.
    """

    name = "Section-names"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 official English short names"

    def matches(self, notation: CountryNotation, contract: Contract) -> bool:
        """Check if notation is a valid country name.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "name" AND value is in NAME_TO_ALPHA2.
        """
        if notation.shape != "name":
            return False
        return notation.value.upper() in NAME_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: Contract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code.
        """
        return NAME_TO_ALPHA2[notation.value.upper()]
