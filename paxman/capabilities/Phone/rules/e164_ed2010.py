"""ITU-T E.164 validation rules — international number structure and country codes."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.data.e164_country_codes import (
    split_country_code,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ITU-T",
    specification_name="E.164",
    kind="specification",
    reference_url="https://www.itu.int/rec/T-REC-E.164",
    version="2010",
    lifecycle="active",
    publication_year=2010,
)

_MAX_E164_DIGITS = 15

# Minimum national significant number length. No national numbering plan
# uses a 1-digit NSN; the floor rejects degenerate values like "+12"
# (CC 1 + NSN "2"). Per-country NSN lengths are NOT validated here —
# that is deferred Milestone-3+ work (area-code/NXX tables).
_MIN_NSN_LENGTH = 2

_DIGITS_ONLY = re.compile(r"^\d+$")


def valid_e164_value(value: str) -> bool:
    """Check E.164 structural validity (shared by the E.164 and RFC 3966 rules).

    Args:
        value: Digit-only E.164 number (no leading +).

    Returns:
        True if the value is digits-only, 1-15 digits long, carries an
        assigned country-code prefix, and its NSN is at least
        _MIN_NSN_LENGTH digits. A bare country code (no NSN), degenerate
        1-digit NSNs, and 16+ digit values are rejected.
    """
    if not _DIGITS_ONLY.match(value):
        return False
    if not 1 <= len(value) <= _MAX_E164_DIGITS:
        return False
    country_code = split_country_code(value)
    if country_code is None:
        return False
    return len(value) - len(country_code) >= _MIN_NSN_LENGTH


def _canonical(value: str, contract: Contract) -> str:
    """Render the canonical form per contract.output_format.

    Args:
        value: Digit-only E.164 number (no leading +).
        contract: Contract configuration.

    Returns:
        Canonical string: "+CCNSN" (e164), "tel:+CCNSN" (rfc3966), or the
        national significant number (national).
    """
    if contract.output_format == "rfc3966":
        return f"tel:+{value}"
    if contract.output_format == "national":
        country_code = split_country_code(value)
        assert country_code is not None  # matches() ran first
        return value[len(country_code) :]
    return f"+{value}"


class Section6_1InternationalNumber(Rule[PhoneNotation]):
    """ITU-T E.164 Section 6.1 — Number structure.

    Validates the E.164 number structure: 1-15 digits, first digit 1-9,
    and a country code (1-3 digits, longest prefix) assigned by ITU-T.
    Per-country NSN lengths are not validated (structural check only).
    """

    name = "Section 6.1-international-number"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 6.1 (number structure)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation is a structurally valid E.164 number.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "e164", value is 1-15 digits, and the country
            code prefix is assigned.
        """
        if notation.shape != "e164":
            return False
        return valid_e164_value(notation.value)

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+" + value, or the formatted variant per contract.output_format.
        """
        return _canonical(notation.value, contract)


class Section6_2CountryCode(Rule[PhoneNotation]):
    """ITU-T E.164 Annex A — Country code assignment.

    Validates that the country code prefix of an E.164 number is in the
    ITU-T assigned country code table.
    """

    name = "Section 6.2-country-code"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "Annex A (table of assigned country codes)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation carries an assigned country code.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "e164" and the country code prefix is assigned.
        """
        if notation.shape != "e164":
            return False
        return valid_e164_value(notation.value)

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+" + value, or the formatted variant per contract.output_format.
        """
        return _canonical(notation.value, contract)
