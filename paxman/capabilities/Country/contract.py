"""Country contract — user-facing configuration for Country capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.capability_contract import CapabilityContract


@dataclass(frozen=True)
class CountryContract(CapabilityContract):
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

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "alpha2"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset(
        {"alpha3", "numeric", "name"}
    )

    capability_name: str = field(default="country", init=False)

    # Standard contract fields
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None

    # Capability-specific fields
    include_localized: bool = False
    include_historical: bool = False
    output_format: str | None = None

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

    def _extra_dict_fields(self) -> dict[str, object]:
        """Serialize capability-specific fields for replay hash.

        Returns:
            Dictionary of include_localized and include_historical flags.
        """
        return {
            "include_localized": self.include_localized,
            "include_historical": self.include_historical,
        }
