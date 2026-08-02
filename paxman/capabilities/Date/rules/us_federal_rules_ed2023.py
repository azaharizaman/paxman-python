"""US federal date rule — validates and normalizes dates with two-digit year support."""

from __future__ import annotations

from datetime import datetime

from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy
from paxman.core.errors import ContractError

PUBLICATION = Provenance(
    authority="US Federal Government",
    specification_name="Federal Rules",
    kind="policy",
    reference_url="https://www.usgs.gov/us-board-on-geographic-names",
    version="2023",
    lifecycle="active",
    publication_year=2023,
)


class Section1DateFormat(Rule[DateNotation]):
    """US federal date format — MM/DD/YYYY with two-digit year support.

    Notation mapping (US grammar):
        N1 = month, N2 = day, N3 = year
    """

    name = "Section 1-date-format"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 1 (date format)"

    def _interpret_two_digit_year(self, year_str: str, contract: Contract) -> int:
        """Interpret two-digit year using contract's base year.

        Args:
            year_str: The year field from the notation.
            contract: Contract configuration.

        Returns:
            The full year (base year + two-digit offset, or the year as-is).

        Raises:
            ContractError: If the contract is not a DateContract. The
                two-digit year helper needs the date-specific
                ``two_digit_base_year`` parameter, so the contract is
                narrowed with a runtime check (not a bare cast).
        """
        if len(year_str) == 2:
            if not isinstance(contract, DateContract):
                raise ContractError(
                    f"{self.name} requires a DateContract, "
                    f"got {type(contract).__name__}"
                )
            base_year = contract.two_digit_base_year or 2000
            return base_year + int(year_str)
        return int(year_str)

    def matches(self, notation: DateNotation, contract: Contract) -> bool:
        """Try to parse as US date with two-digit year support."""
        try:
            month = int(notation.N1)
            day = int(notation.N2)
            year = self._interpret_two_digit_year(notation.N3, contract)
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, notation: DateNotation, contract: Contract) -> str:
        """Normalize based on output_format contract parameter."""
        month = int(notation.N1)
        day = int(notation.N2)
        year = self._interpret_two_digit_year(notation.N3, contract)

        if contract.output_format == "US":
            return f"{month:02d}/{day:02d}/{year:04d}"
        return f"{year:04d}-{month:02d}-{day:02d}"
