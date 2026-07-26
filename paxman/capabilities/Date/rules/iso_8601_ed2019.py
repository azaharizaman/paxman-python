"""ISO 8601 date rule — validates and normalizes dates to ISO format."""

from __future__ import annotations

from datetime import datetime

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 8601",
    kind="specification",
    reference_url="https://www.iso.org/standard/70907.html",
    version="2019",
    lifecycle="active",
    publication_year=2019,
)


class Section431CalendarDate(Rule[DateNotation]):
    """ISO 8601 Section 4.3.1 — Calendar date."""

    name = "Section 4.3.1-calendar-date"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4.3.1 (calendar date)"

    def matches(self, notation: DateNotation, contract: Contract) -> bool:
        """Try to parse as ISO 8601 date."""
        try:
            day = int(notation.day)
            month = int(notation.month)
            year = int(notation.year)
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, notation: DateNotation, contract: Contract) -> str:
        """Normalize to ISO 8601 format."""
        day = int(notation.day)
        month = int(notation.month)
        year = int(notation.year)
        return f"{year:04d}-{month:02d}-{day:02d}"
