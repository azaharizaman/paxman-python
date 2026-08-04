"""US federal date rule — validates and normalizes dates with two-digit year support."""

from __future__ import annotations

from datetime import datetime

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

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
    target_grammars = frozenset({"us_recognition", "european_recognition"})
    requires_features = frozenset()

    def _interpret_two_digit_year(self, year_str: str, contract: Contract) -> int:
        """Interpret two-digit year using contract's base year.

        Defensive: the base year is read from the contract's
        ``two_digit_base_year`` attribute when present, falling back to 2000
        otherwise. An explicit zero is a configured value and is honored
        rather than treated as unset. This helper never raises for contracts
        that lack the Date-specific parameter.

        Args:
            year_str: The year field from the notation.
            contract: Contract configuration.

        Returns:
            The full year (base year + two-digit offset, or the year as-is).
        """
        if len(year_str) == 2:
            base_year = getattr(contract, "two_digit_base_year", None)
            if base_year is None:
                base_year = 2000
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
        """Normalize to the default canonical ISO 8601 format."""
        month = int(notation.N1)
        day = int(notation.N2)
        year = self._interpret_two_digit_year(notation.N3, contract)

        return f"{year:04d}-{month:02d}-{day:02d}"
