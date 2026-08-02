"""Date contract for Date capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from paxman.core.contract import resolve_output_format

VALID_OUTPUT_FORMATS: frozenset[str] = frozenset({"US"})


@dataclass(frozen=True)
class DateContract:
    """User-facing contract for Date capability."""

    capability_name: str = field(default="date", init=False)
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None
    two_digit_base_year: int | None = None

    def __post_init__(self) -> None:
        """Validate output_format against Date's offered formats.

        Date's default canonical output is ``"ISO"``. Accepted values are
        ``None`` (unset), ``"default"``, ``"ISO"`` (the default), and the
        offered alternative ``"US"``. Anything else raises
        :class:`ContractError`.

        Raises:
            ContractError: If ``output_format`` is not acceptable.
        """
        object.__setattr__(
            self,
            "output_format",
            resolve_output_format(
                self.output_format,
                capability_name="date",
                offered_formats=VALID_OUTPUT_FORMATS,
                default_format="ISO",
            ),
        )

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
