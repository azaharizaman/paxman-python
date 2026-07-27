"""Country capability — wires grammars and rules together."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.grammar.alpha2_recognition import Alpha2Grammar
from paxman.capabilities.Country.grammar.alpha3_recognition import Alpha3Grammar
from paxman.capabilities.Country.grammar.name_recognition import NameGrammar
from paxman.capabilities.Country.grammar.numeric_recognition import NumericGrammar
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.cldr_localized_ed2025 import SectionLocalizedNames
from paxman.capabilities.Country.rules.iso_3166_alpha2_ed2024 import SectionAlpha2Codes
from paxman.capabilities.Country.rules.iso_3166_alpha3_ed2024 import SectionAlpha3Codes
from paxman.capabilities.Country.rules.iso_3166_name_ed2024 import SectionNames
from paxman.capabilities.Country.rules.iso_3166_numeric_ed2024 import SectionNumericCodes
from paxman.capabilities.Country.rules.paxman_historical_ed2025 import SectionHistoricalNames
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


class CountryCapability(Capability[CountryNotation]):
    """Country canonicalization capability.

    Canonicalizes country representations (alpha2, alpha3, numeric, name)
    to ISO 3166-1 alpha-2 codes with full provenance.
    """

    name = "country"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar[CountryNotation]]:
        """Return all grammar instances.

        Returns:
            List of 4 grammars: alpha2, alpha3, numeric, name.
        """
        return [
            Alpha2Grammar(),
            Alpha3Grammar(),
            NumericGrammar(),
            NameGrammar(),
        ]

    def get_rules(self) -> list[Rule[CountryNotation]]:
        """Return all validation rule instances.

        Returns:
            List of 6 rules: iso_alpha2, iso_alpha3, iso_numeric, iso_name, cldr_localized, paxman_historical.
        """
        return [
            SectionAlpha2Codes(),
            SectionAlpha3Codes(),
            SectionNumericCodes(),
            SectionNames(),
            SectionLocalizedNames(),
            SectionHistoricalNames(),
        ]

    @staticmethod
    def create_contract(
        *,
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
        include_localized: bool = False,
        include_historical: bool = False,
        extra_synonyms: dict[str, str] | None = None,
    ) -> CountryContract:
        """Factory method for creating contracts with proper defaults.

        Args:
            excluded_rules: Rule names to exclude.
            pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
            year: Year for temporal filtering.
            output_format: Canonical output format ("alpha2", "alpha3", "numeric", "name").
            include_localized: Enable CLDR multilingual names.
            include_historical: Enable deprecated country names.
            extra_synonyms: Caller-supplied aliases.

        Returns:
            Configured CountryContract instance.
        """
        return CountryContract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
            output_format=output_format,
            include_localized=include_localized,
            include_historical=include_historical,
            extra_synonyms=extra_synonyms or {},
        )
