"""Phone contract — user-facing configuration for Phone capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from paxman.core.errors import ContractError

_VALID_OUTPUT_FORMATS: frozenset[str] = frozenset({"e164", "rfc3966", "national"})


def _validate_alpha2(value: str | None) -> None:
    """Validate an ISO 3166-1 alpha-2 country code.

    Args:
        value: Country code to validate (None is allowed — means "no default").

    Raises:
        ContractError: If the value is present but not an uppercase
            2-letter ASCII ISO 3166-1 alpha-2 code (or not a str at all).
    """
    if value is None:
        return
    candidate = cast(object, value)
    if not isinstance(candidate, str):
        raise ContractError(
            "default_country must be an uppercase ISO 3166-1 alpha-2 code, "
            f"got {value!r}"
        )
    if (
        len(candidate) != 2
        or not candidate.isascii()
        or not candidate.isalpha()
        or not candidate.isupper()
    ):
        raise ContractError(
            "default_country must be an uppercase ISO 3166-1 alpha-2 code, "
            f"got {value!r}"
        )


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

    def __post_init__(self) -> None:
        """Validate contract configuration.

        Raises:
            ContractError: If output_format is unsupported or default_country
                is present but not an uppercase alpha-2 code.
        """
        candidate = cast(object, self.output_format)
        if not isinstance(candidate, str) or candidate not in _VALID_OUTPUT_FORMATS:
            raise ContractError(
                f"output_format must be one of {sorted(_VALID_OUTPUT_FORMATS)}, "
                f"got {self.output_format!r}"
            )
        _validate_alpha2(self.default_country)

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
