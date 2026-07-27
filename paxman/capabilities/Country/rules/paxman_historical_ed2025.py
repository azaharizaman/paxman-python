"""Paxman historical country name validation rule."""

from __future__ import annotations

from typing import cast

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.historical_data import HISTORICAL_TO_ALPHA2
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="Paxman",
    specification_name="Historical Country Names",
    kind="policy",
    reference_url="https://github.com/paxman-dev/paxman/blob/main/docs/historical-countries.md",
    version=None,
    lifecycle="active",
    publication_year=2025,
)


class SectionHistoricalNames(Rule[CountryNotation]):
    """Paxman Section: historical country names.

    Validates name shape against deprecated country names.
    Only active when contract.include_historical is True.
    """

    name = "Section-historical-names"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "Paxman historical country names"

    def matches(self, notation: CountryNotation, contract: Contract) -> bool:
        """Check if notation is a valid historical name.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if include_historical AND notation.shape == "name" AND name is in HISTORICAL_TO_ALPHA2.
        """
        country_contract = cast(CountryContract, contract)
        if not country_contract.include_historical:
            return False
        if notation.shape != "name":
            return False
        return notation.value.upper() in HISTORICAL_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: Contract) -> str:
        """Normalize to current alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Current alpha-2 code.
        """
        return HISTORICAL_TO_ALPHA2[notation.value.upper()]
