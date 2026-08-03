"""ISO 3166-1:2024 validation rules.

All four sections (alpha-2, alpha-3, numeric, name) share the same
publication and lookup tables. Rules are co-located in a single file
to reflect this shared provenance.

All sections support contract.output_format for canonical output in
alpha-2 (default), alpha-3, numeric (M49), or name format.
"""

from __future__ import annotations

from typing import cast

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.data.iso_3166_ed2024 import (
    ALPHA2_CODES,
    ALPHA2_TO_ALPHA3,
    ALPHA2_TO_NAME,
    ALPHA2_TO_NUMERIC,
    ALPHA3_TO_ALPHA2,
    NAME_TO_ALPHA2,
    NUMERIC_TO_ALPHA2,
    SYNONYM_TO_ALPHA2,
)
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
    target_grammars = frozenset({"alpha2_recognition"})
    requires_features = frozenset()

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
        """Normalize to canonical country code in requested output format.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Country code in the requested output format.
        """
        country_contract = cast(CountryContract, contract)
        alpha2 = notation.value.upper()
        fmt = country_contract.output_format

        if fmt == "alpha2":
            return alpha2
        if fmt == "alpha3":
            return ALPHA2_TO_ALPHA3[alpha2]
        if fmt == "numeric":
            return ALPHA2_TO_NUMERIC[alpha2]
        # fmt == "name"
        return ALPHA2_TO_NAME[alpha2]


class SectionAlpha3Codes(Rule[CountryNotation]):
    """ISO 3166-1 Section: alpha-3 codes.

    Validates alpha-3 shape against the official list of 249 assigned codes.
    """

    name = "Section-alpha3-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 alpha-3 codes"
    target_grammars = frozenset({"alpha3_recognition"})
    requires_features = frozenset()

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
        """Normalize to canonical country code in requested output format.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Country code in the requested output format.
        """
        country_contract = cast(CountryContract, contract)
        alpha3 = notation.value.upper()
        alpha2 = ALPHA3_TO_ALPHA2[alpha3]
        fmt = country_contract.output_format

        if fmt == "alpha2":
            return alpha2
        if fmt == "alpha3":
            return ALPHA2_TO_ALPHA3[alpha2]
        if fmt == "numeric":
            return ALPHA2_TO_NUMERIC[alpha2]
        # fmt == "name"
        return ALPHA2_TO_NAME[alpha2]


class SectionNumericCodes(Rule[CountryNotation]):
    """ISO 3166-1 Section: numeric (M49) codes.

    Validates numeric shape against the official list of 249 assigned codes.
    """

    name = "Section-numeric-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 numeric (M49) codes"
    target_grammars = frozenset({"numeric_recognition"})
    requires_features = frozenset()

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
        """Normalize to canonical country code in requested output format.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Country code in the requested output format.
        """
        country_contract = cast(CountryContract, contract)
        alpha2 = NUMERIC_TO_ALPHA2[self._normalize_key(notation.value)]
        fmt = country_contract.output_format

        if fmt == "alpha2":
            return alpha2
        if fmt == "alpha3":
            return ALPHA2_TO_ALPHA3[alpha2]
        if fmt == "numeric":
            return ALPHA2_TO_NUMERIC[alpha2]
        # fmt == "name"
        return ALPHA2_TO_NAME[alpha2]


class SectionNames(Rule[CountryNotation]):
    """ISO 3166-1 Section: official English short names.

    Validates name shape against the official list of 249 assigned names
    and their common synonyms (e.g., USA → US, UK → GB).
    """

    name = "Section-names"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 official English short names"
    target_grammars = frozenset({"name_recognition"})
    requires_features = frozenset()

    def matches(self, notation: CountryNotation, contract: Contract) -> bool:
        """Check if notation is a valid country name or synonym.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "name" AND value is in NAME_TO_ALPHA2
            or SYNONYM_TO_ALPHA2.
        """
        if notation.shape != "name":
            return False
        upper = notation.value.upper()
        return upper in NAME_TO_ALPHA2 or upper in SYNONYM_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: Contract) -> str:
        """Normalize to canonical country code in requested output format.

        Checks NAME_TO_ALPHA2 first, then falls back to SYNONYM_TO_ALPHA2,
        then converts to requested output format.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Country code in the requested output format.
        """
        country_contract = cast(CountryContract, contract)
        upper = notation.value.upper()
        if upper in NAME_TO_ALPHA2:
            alpha2 = NAME_TO_ALPHA2[upper]
        else:
            alpha2 = SYNONYM_TO_ALPHA2[upper]
        fmt = country_contract.output_format

        if fmt == "alpha2":
            return alpha2
        if fmt == "alpha3":
            return ALPHA2_TO_ALPHA3[alpha2]
        if fmt == "numeric":
            return ALPHA2_TO_NUMERIC[alpha2]
        # fmt == "name"
        return ALPHA2_TO_NAME[alpha2]
