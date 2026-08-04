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
    """ISO 8601 Section 4.3.1 — Calendar date.

    Notation mapping (ISO 8601 grammar):
        N1 = year, N2 = month, N3 = day
    """

    name = "Section 4.3.1-calendar-date"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4.3.1 (calendar date)"
    target_grammars = frozenset({"iso8601_recognition"})
    requires_features = frozenset()

    def matches(self, notation: DateNotation, contract: Contract) -> bool:
        """Try to parse as ISO 8601 date."""
        try:
            year = int(notation.N1)
            if year < 1000:
                return False
            month = int(notation.N2)
            day = int(notation.N3)
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, notation: DateNotation, contract: Contract) -> str:
        """Normalize to ISO 8601 format."""
        year = int(notation.N1)
        month = int(notation.N2)
        day = int(notation.N3)
        return f"{year:04d}-{month:02d}-{day:02d}"
