"""ISO 3166-1:2024 alpha-3 code validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.data import ALPHA3_TO_ALPHA2
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


class SectionAlpha3Codes(Rule[CountryNotation]):
    """ISO 3166-1 Section: alpha-3 codes.

    Validates alpha-3 shape against the official list of 249 assigned codes.
    """

    name = "Section-alpha3-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 alpha-3 codes"

    def matches(self, notation: CountryNotation, contract: Contract) -> bool:
        """Check if notation is a valid alpha-3 code.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "alpha3" AND value is in ALPHA3_TO_ALPHA2.
        """
        if notation.shape != "alpha3":
            return False
        return notation.value.upper() in ALPHA3_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: Contract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code.
        """
        code = notation.value.upper()
        return ALPHA3_TO_ALPHA2[code]
