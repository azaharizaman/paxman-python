"""Country contract — user-facing configuration for Country capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CountryContract:
    """User-facing configuration for Country capability.

    Attributes:
        capability_name: Fixed to "country" (not user-settable).
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
        output_format: Canonical output format ("alpha2", "alpha3", "numeric", "name").
        include_localized: Enable CLDR multilingual names.
        include_historical: Enable deprecated country names.
        extra_synonyms: Caller-supplied aliases (validated at construction).
    """

    capability_name: str = field(default="country", init=False)

    # Standard contract fields
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None

    # Capability-specific fields
    include_localized: bool = False
    include_historical: bool = False
    extra_synonyms: dict[str, str] = field(default_factory=lambda: {})

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
            "extra_synonyms": self.extra_synonyms,
        }
