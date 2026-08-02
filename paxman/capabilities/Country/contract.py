"""Country contract — user-facing configuration for Country capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from paxman.core.errors import ContractError

VALID_OUTPUT_FORMATS: frozenset[str] = frozenset(
    {"alpha2", "alpha3", "numeric", "name"}
)


@dataclass(frozen=True, slots=True)
class CountryContract:
    """User-facing configuration for Country capability.

    Attributes:
        capability_name: Fixed to "country" (not user-settable).
        output_format: Output format for canonical values. One of "alpha2",
            "alpha3", "numeric", "name". Defaults to "alpha2".
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
        include_localized: Enable CLDR multilingual names.
        include_historical: Enable deprecated country names.
    """

    capability_name: str = field(default="country", init=False)

    # Standard contract fields
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None

    # Capability-specific fields
    include_localized: bool = False
    include_historical: bool = False
    output_format: str = "alpha2"

    @property
    def active_grammars(self) -> list[str]:
        """All grammars active by default.

        Returns:
            List of grammar names to activate.
        """
        return [
            "alpha2_recognition",
            "alpha3_recognition",
            "numeric_recognition",
            "name_recognition",
        ]

    def __post_init__(self) -> None:
        """Validate output_format value."""
        if self.output_format not in VALID_OUTPUT_FORMATS:
            msg = (
                f"Invalid output_format: {self.output_format!r}. "
                f"Must be one of {sorted(VALID_OUTPUT_FORMATS)}"
            )
            raise ContractError(msg)

    def as_dict(self) -> dict[str, Any]:
        """Serialize for replay hash computation.

        Returns:
            Dictionary representation of all fields.
        """
        return {
            "capability_name": self.capability_name,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
            "output_format": self.output_format,
            "include_localized": self.include_localized,
            "include_historical": self.include_historical,
        }
