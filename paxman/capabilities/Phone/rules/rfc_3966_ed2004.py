"""IETF RFC 3966 validation rule — the tel URI for telephone numbers."""

from __future__ import annotations

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.data.e164_country_codes import (
    split_country_code,
)
from paxman.capabilities.Phone.rules.e164_ed2010 import valid_e164_value
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


class Section3TelUri(Rule[PhoneNotation]):
    """RFC 3966 Section 3 — The tel URI for telephone numbers.

    Validates tel: URIs carrying global numbers (per RFC 3966 Section 3.1).
    The tel-URI grammar only recognizes global numbers (leading "+");
    local numbers (no "+", with or without phone-context) are Milestone-12+
    scope and never reach this rule.
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
            True if shape == "rfc3966" and the value passes the shared
            E.164 structural check (assigned country code, 2-15 digits,
            NSN length floor). Per-country NSN lengths are not validated.
        """
        if notation.shape != "rfc3966":
            return False
        return valid_e164_value(notation.value)

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+" + value (default), "tel:+value[;ext=extension]" (rfc3966),
            or the national significant number (national).

        Raises:
            ValueError: If the national format is requested and the value
                has no assigned country code prefix (matches() runs first,
                so this only fires on direct misuse).
        """
        if contract.output_format == "rfc3966":
            base = f"tel:+{notation.value}"
            return f"{base};ext={notation.extension}" if notation.extension else base
        if contract.output_format == "national":
            country_code = split_country_code(notation.value)
            if country_code is None:
                raise ValueError(
                    f"{self.name}: cannot normalize {notation.value!r}: "
                    "no assigned country code"
                )
            return notation.value[len(country_code) :]
        return f"+{notation.value}"
