"""Date notation — intermediate representation for date values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DateNotation:
    """Date notation with day, month, and year components."""

    day: str
    month: str
    year: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.day, self.month, self.year]
