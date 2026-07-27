"""Date contract for Date capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DateContract:
    """User-facing contract for Date capability."""

    capability_name: str = field(default="date", init=False)
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None
    two_digit_base_year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        return [
            "iso8601_recognition",
            "us_recognition",
            "european_recognition",
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
            "output_format": self.output_format,
            "two_digit_base_year": self.two_digit_base_year,
        }
