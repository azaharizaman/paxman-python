"""Date canonicalization capability."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.grammar.european_recognition import (
    EuropeanDateGrammar,
)
from paxman.capabilities.Date.grammar.iso8601_recognition import (
    ISO8601DateGrammar,
)
from paxman.capabilities.Date.grammar.us_recognition import USDateGrammar
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.en_50160_ed2010 import Section4DateFormat
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate
from paxman.capabilities.Date.rules.us_federal_rules_ed2023 import (
    Section1DateFormat,
)
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule

__all__ = ["DateCapability", "DateContract"]


class DateCapability(Capability[DateNotation]):
    """Date canonicalization capability."""

    name = "date"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar[DateNotation]]:
        return [
            ISO8601DateGrammar(),
            USDateGrammar(),
            EuropeanDateGrammar(),
        ]

    def get_rules(self) -> list[Rule[DateNotation]]:
        return [
            Section431CalendarDate(),
            Section1DateFormat(),
            Section4DateFormat(),
        ]

    @staticmethod
    def create_contract(
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
        two_digit_base_year: int | None = None,
    ) -> DateContract:
        """Create a DateContract with the given configuration."""
        return DateContract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
            output_format=output_format,
            two_digit_base_year=two_digit_base_year,
        )
