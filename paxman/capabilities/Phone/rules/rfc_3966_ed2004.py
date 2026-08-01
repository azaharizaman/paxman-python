"""IETF RFC 3966 validation rule — the tel URI for telephone numbers."""

from __future__ import annotations

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.data.e164_country_codes import (
    split_country_code,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 3966",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc3966",
    version="2004",
    lifecycle="active",
    publication_year=2004,
)

_MAX_E164_DIGITS = 15


class Section3TelUri(Rule[PhoneNotation]):
    """RFC 3966 Section 3 — The tel URI for telephone numbers.

    Validates tel: URIs carrying global numbers (per RFC 3966 Section 3.1).
    Local numbers with phone-context are Milestone-12+ scope and rejected
    here (they carry no E.164 country code).
    """

    name = "Section 3-tel-uri"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 3 (tel URI) / Section 3.1 (global numbers)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation is a valid tel-URI global number.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "rfc3966", value is 1-15 digits with an
            assigned country code prefix.
        """
        if notation.shape != "rfc3966":
            return False
        if not notation.value.isdigit():
            return False
        if not 1 <= len(notation.value) <= _MAX_E164_DIGITS:
            return False
        return split_country_code(notation.value) is not None

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+" + value (default), "tel:+value[;ext=extension]" (rfc3966),
            or the national significant number (national).
        """
        if contract.output_format == "rfc3966":
            base = f"tel:+{notation.value}"
            return f"{base};ext={notation.extension}" if notation.extension else base
        if contract.output_format == "national":
            country_code = split_country_code(notation.value)
            assert country_code is not None  # matches() ran first
            return notation.value[len(country_code) :]
        return f"+{notation.value}"
