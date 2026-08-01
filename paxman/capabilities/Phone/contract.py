"""Phone contract — user-facing configuration for Phone capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PhoneContract:
    """User-facing configuration for Phone capability.

    Attributes:
        capability_name: Fixed to "phone" (not user-settable).
        default_country: ISO 3166-1 alpha-2 country code used to resolve
            national numbers (e.g., "US"). When None, national-shaped input
            is recognized but never validated (status INVALID).
        output_format: Canonical output format ("e164" default, "rfc3966",
            or "national" for the national significant number).
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
    """

    capability_name: str = field(default="phone", init=False)

    # Capability-specific fields
    default_country: str | None = None
    output_format: str = "e164"

    # Standard contract fields
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        """All grammars active by default.

        All grammars are cheap regex scans; rules filter by shape and by
        contract parameters (e.g., national rules gate on default_country).

        Returns:
            List of grammar names to activate.
        """
        return [
            "e164_recognition",
            "tel_uri_recognition",
            "international_00_recognition",
            "national_recognition",
        ]

    def as_dict(self) -> dict[str, Any]:
        """Serialize for replay hash computation.

        Returns:
            Dictionary representation of all fields.
        """
        return {
            "capability_name": self.capability_name,
            "default_country": self.default_country,
            "output_format": self.output_format,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
        }
