"""Phone contract — user-facing configuration for Phone capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, cast

from paxman.core.contract import CapabilityContract
from paxman.core.errors import ContractError


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


@dataclass(frozen=True)
class PhoneContract(CapabilityContract):
    """User-facing configuration for Phone capability.

    Attributes:
        capability_name: Fixed to "phone" (not user-settable).
        default_country: ISO 3166-1 alpha-2 country code used to interpret
            national-shaped input (e.g., "US" for "(555) 234-5678"). When None,
            national-shaped input is recognized but never validated (status
            INVALID) — national-shaped numbers carry no country code in their
            digits and so cannot be resolved without a default country. For
            E.164, tel-URI, and NANP inputs the country code is embedded in the
            value itself, so "national" output works without default_country.
        output_format: Canonical output format ("e164" default, "rfc3966",
            or "national" for the national significant number). Optional —
            None/"default"/"e164" all resolve to "e164".
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "e164"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset(
        {"rfc3966", "national"}
    )

    capability_name: str = field(default="phone", init=False)

    # Capability-specific fields
    default_country: str | None = None

    def __post_init__(self) -> None:
        """Validate contract configuration.

        Calls the base resolution first, then enforces Phone-specific rules:
        default_country must be an uppercase alpha-2 code when present.

        ``output_format="national"`` is permitted with or without
        ``default_country``. It is required only for *national-shaped* input,
        which carries no country code in its digits — that requirement is
        enforced by the NANP rules' ``matches()`` (they return False when
        ``default_country`` is not a NANP country). For E.164, tel-URI, and
        NANP inputs the country code is embedded in the value and is split out
        by the rules, so ``"national"`` output works without default_country.

        Raises:
            ContractError: If output_format is unsupported or default_country is
                present but not an uppercase alpha-2 code.
        """
        super().__post_init__()
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

    def _extra_dict_fields(self) -> dict[str, object]:
        return {"default_country": self.default_country}
