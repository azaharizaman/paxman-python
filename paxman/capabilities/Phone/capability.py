"""Phone capability — wires grammars and rules together."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.grammar.e164_recognition import E164Grammar
from paxman.capabilities.Phone.grammar.international_00_recognition import (
    International00Grammar,
)
from paxman.capabilities.Phone.grammar.national_recognition import NationalGrammar
from paxman.capabilities.Phone.grammar.tel_uri_recognition import TelUriGrammar
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.e164_ed2010 import (
    Section6_1InternationalNumber,
    Section6_2CountryCode,
)
from paxman.capabilities.Phone.rules.nanp_ed2024 import (
    Section1_1NANPStructure,
    Section1_2ServiceNPA,
)
from paxman.capabilities.Phone.rules.rfc_3966_ed2004 import Section3TelUri
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule

__all__ = ["PhoneCapability", "PhoneContract", "PhoneNotation"]


class PhoneCapability(Capability[PhoneNotation]):
    """Phone canonicalization capability.

    Canonicalizes phone numbers (E.164 international, NANP national,
    RFC 3966 tel-URI) to E.164 format with full provenance.
    """

    name = "phone"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar[PhoneNotation]]:
        """Return all grammar instances.

        Returns:
            List of 4 grammars: e164, tel-URI, international-00, national.
        """
        return [
            E164Grammar(),
            TelUriGrammar(),
            International00Grammar(),
            NationalGrammar(),
        ]

    def get_rules(self) -> list[Rule[PhoneNotation]]:
        """Return all validation rule instances.

        Returns:
            List of 5 rules: E.164 structure, E.164 country code,
            RFC 3966 tel-URI, NANP structure, NANP service NPA.
        """
        return [
            Section6_1InternationalNumber(),
            Section6_2CountryCode(),
            Section3TelUri(),
            Section1_1NANPStructure(),
            Section1_2ServiceNPA(),
        ]

    @staticmethod
    def create_contract(
        *,
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
        default_country: str | None = None,
    ) -> PhoneContract:
        """Factory method for creating contracts with proper defaults.

        Args:
            excluded_rules: Rule names to exclude.
            pinned_rules: Pin to specific rules (takes precedence over
                excluded_rules).
            year: Year for temporal filtering.
            output_format: Output format for canonical values. Optional;
                None/"default"/"e164" resolve to "e164", or one of the
                offered alternatives "rfc3966"/"national". For E.164, tel-URI,
                and NANP inputs "national" works without default_country
                (the country code is embedded in the value); for national-shaped
                input it needs default_country to resolve the value.
            default_country: ISO 3166-1 alpha-2 country code used to resolve
                national-shaped numbers (e.g., "US"). Required for "national"
                output from national-shaped input; optional otherwise.

        Returns:
            Configured PhoneContract instance.
        """
        return PhoneContract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
            output_format=output_format,
            default_country=default_country,
        )
