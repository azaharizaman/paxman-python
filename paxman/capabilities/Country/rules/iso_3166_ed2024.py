"""ISO 3166-1:2024 validation rules.

All four sections (alpha-2, alpha-3, numeric, name) share the same
publication and lookup tables. Rules are co-located in a single file
to reflect this shared provenance.
"""

from __future__ import annotations

from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.data.iso_3166_ed2024 import (
    ALPHA2_CODES,
    ALPHA3_TO_ALPHA2,
    NAME_TO_ALPHA2,
    NUMERIC_TO_ALPHA2,
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
