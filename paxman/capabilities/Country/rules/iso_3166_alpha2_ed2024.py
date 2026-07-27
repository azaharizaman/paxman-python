"""ISO 3166-1:2024 alpha-2 code validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.data import (
    ALPHA2_CODES,
    ALPHA3_TO_ALPHA2,
    NAME_TO_ALPHA2,
    NUMERIC_TO_ALPHA2,
)
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


class SectionAlpha2Codes(Rule[CountryNotation]):
    """ISO 3166-1 Section: alpha-2 codes.

    Validates alpha-2 shape against the official list of 249 assigned codes.
    """

    name = "Section-alpha2-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 alpha-2 codes"

    def matches(self, notation: CountryNotation, contract: Contract) -> bool:
        """Check if notation is a valid alpha-2 code.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "alpha2" AND value is in ALPHA2_CODES.
        """
        if notation.shape != "alpha2":
            return False
        return notation.value.upper() in ALPHA2_CODES

    def normalize(self, notation: CountryNotation, contract: Contract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code.
        """
        code = notation.value.upper()
        if contract.output_format == "alpha3":
            for alpha3, alpha2 in ALPHA3_TO_ALPHA2.items():
                if alpha2 == code:
                    return alpha3
        if contract.output_format == "numeric":
            for numeric, alpha2 in NUMERIC_TO_ALPHA2.items():
                if alpha2 == code:
                    return numeric
        if contract.output_format == "name":
            for name, alpha2 in NAME_TO_ALPHA2.items():
                if alpha2 == code:
                    return name
        return code
