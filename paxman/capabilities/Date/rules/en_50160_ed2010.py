"""EN 50160 date rule — validates and normalizes European DD/MM/YYYY dates."""

from __future__ import annotations

from datetime import datetime

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="CENELEC",
    specification_name="EN 50160",
    kind="specification",
    reference_url="https://standards.cencenelec.eu/dyn/www/f?p=205:110:0::::FSP_PROJECT,FSP_ORG_ID:55423,32357",
    version="2010",
    lifecycle="active",
    publication_year=2010,
)


class Section4DateFormat(Rule[DateNotation]):
    """EN 50160 Section 4 — European date format DD/MM/YYYY.

    Notation mapping (European grammar):
        N1 = day, N2 = month, N3 = year
    """

    name = "Section 4-date-format"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4 (date format)"

    def _interpret_two_digit_year(self, year_str: str, contract: Contract) -> int:
        """Interpret two-digit year using contract's base year."""
        if len(year_str) == 2:
            base_year = contract.two_digit_base_year or 2000
            return base_year + int(year_str)
        return int(year_str)

    def matches(self, notation: DateNotation, contract: Contract) -> bool:
        """Try to parse as European date DD/MM/YYYY."""
        try:
            day = int(notation.N1)
            month = int(notation.N2)
            year = self._interpret_two_digit_year(notation.N3, contract)
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, notation: DateNotation, contract: Contract) -> str:
        """Normalize based on output_format contract parameter."""
        day = int(notation.N1)
        month = int(notation.N2)
        year = self._interpret_two_digit_year(notation.N3, contract)

        if contract.output_format == "US":
            return f"{month:02d}/{day:02d}/{year:04d}"
        return f"{year:04d}-{month:02d}-{day:02d}"
