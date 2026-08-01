"""North American Numbering Plan (NANP) validation rules.

NANP structure: NPA-NXX-XXXX where NPA and NXX each begin with 2-9.
N11 codes (211/311/411/511/611/711/811/911) are not assignable as NPA
or NXX. 555-01XX exchanges are reserved for fictional numbers.
"""

from __future__ import annotations

import re
from typing import cast

from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.data.nanp_tables import (
    N11_CODES,
    SERVICE_NPAS,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="NANPA",
    specification_name="North American Numbering Plan (NANP)",
    kind="registry",
    reference_url="https://www.nanpa.com/",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)

# NANP countries for Milestone 1: United States only.
# Future milestones add "CA" and other NANP members.
_NANP_COUNTRIES: frozenset[str] = frozenset({"US"})

# Optional trunk 1, then NPA NXX XXXX. Group 1 = optional trunk,
# group 2 = NPA, group 3 = NXX, group 4 = line number.
_NANP_PATTERN = re.compile(r"^(1)?([2-9]\d{2})([2-9]\d{2})(\d{4})$")


def _is_fictional_range(nxx: str, line: str) -> bool:
    """Check if the number falls in the 555-0100..555-0199 fictional range.

    Per NANPA, numbers of the form NXX=555 with a line number 0100-0199
    are reserved for fictional use (e.g., in movies and TV). They are not
    assignable real numbers.

    Args:
        nxx: The 3-digit central office code.
        line: The 4-digit line number.

    Returns:
        True if the number is in the reserved fictional range.
    """
    return nxx == "555" and line.startswith("01")


def _nanp_digits(value: str) -> str | None:
    """Return the 10 NANP digits after stripping an optional trunk 1.

    Args:
        value: Digit-only national number (10 or 11 digits).

    Returns:
        The 10-digit NANP number (trunk stripped), or None if the value
        is not 10/11 digits or fails structural constraints.
    """
    match = _NANP_PATTERN.match(value)
    if match is None:
        return None
    npa, nxx, line = match.group(2), match.group(3), match.group(4)
    if npa in N11_CODES:
        return None
    if nxx in N11_CODES:
        return None
    if _is_fictional_range(nxx, line):
        return None
    return f"{npa}{nxx}{line}"


def _canonical(digits: str, contract: Contract) -> str:
    """Render the canonical form per contract.output_format.

    Args:
        digits: 10-digit NANP number (trunk already stripped).
        contract: Contract configuration.

    Returns:
        "+1" + digits (e164/rfc3966-with-plus), "tel:+1" + digits
        (rfc3966), or the NSN (national).
    """
    if contract.output_format == "rfc3966":
        return f"tel:+1{digits}"
    if contract.output_format == "national":
        return digits
    return f"+1{digits}"


class Section1_1NANPStructure(Rule[PhoneNotation]):
    """NANP — numbering plan structure.

    Validates NANP structure: 10-digit NPA-NXX-XXXX (optionally with
    leading trunk 1), NPA/NXX first digit 2-9, N11 codes not assignable,
    and 555-01XX reserved for fictional numbers.
    """

    name = "Section 1.1-nanp-structure"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "NANP numbering plan structure (NPA NXX-XXXX)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation is a structurally valid NANP number.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "national", default_country is a NANP country
            (Milestone 1: "US"), and the value passes the NANP structure
            regex and exclusions.
        """
        if notation.shape != "national":
            return False
        typed_contract = cast(PhoneContract, contract)
        if typed_contract.default_country not in _NANP_COUNTRIES:
            return False
        return _nanp_digits(notation.value) is not None

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+1" + 10-digit NANP number, or the formatted variant per
            contract.output_format.
        """
        digits = _nanp_digits(notation.value)
        assert digits is not None  # matches() ran first
        return _canonical(digits, contract)


class Section1_2ServiceNPA(Rule[PhoneNotation]):
    """NANP — service NPAs (toll-free and premium rate).

    Validates that the NPA is a NANPA-assigned service code (toll-free
    800/833/844/855/866/877/888 or premium 900).
    """

    name = "Section 1.2-service-npa"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "NANPA service NPA assignment table"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation carries a service NPA.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "national", default_country is a NANP country
            (Milestone 1: "US"), and the NPA is in the service table.
        """
        if notation.shape != "national":
            return False
        typed_contract = cast(PhoneContract, contract)
        if typed_contract.default_country not in _NANP_COUNTRIES:
            return False
        digits = _nanp_digits(notation.value)
        if digits is None:
            return False
        return digits[:3] in SERVICE_NPAS

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+1" + 10-digit NANP number, or the formatted variant per
            contract.output_format.
        """
        digits = _nanp_digits(notation.value)
        assert digits is not None  # matches() ran first
        return _canonical(digits, contract)
