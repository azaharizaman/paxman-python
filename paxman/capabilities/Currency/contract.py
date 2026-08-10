# paxman/capabilities/Currency/contract.py
"""Currency contract — user-facing configuration for Currency capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, cast

from paxman.core.capability_contract import CapabilityContract
from paxman.core.errors import ContractError


def _validate_alpha3(value: str | None) -> None:
    """Validate an ISO 4217 alpha-3 currency code.

    Args:
        value: Currency code to validate (None is allowed — means "no default").

    Raises:
        ContractError: If the value is present but not an uppercase
            3-letter ASCII ISO 4217 alpha-3 code (or not a str at all).
    """
    if value is None:
        return
    candidate = cast(object, value)
    if not isinstance(candidate, str):
        raise ContractError(
            "default_currency must be an uppercase ISO 4217 alpha-3 code, "
            f"got {value!r}"
        )
    if (
        len(candidate) != 3
        or not candidate.isascii()
        or not candidate.isalpha()
        or not candidate.isupper()
    ):
        raise ContractError(
            "default_currency must be an uppercase ISO 4217 alpha-3 code, "
            f"got {value!r}"
        )


@dataclass(frozen=True)
class CurrencyContract(CapabilityContract):
    """User-facing configuration for Currency capability.

    Attributes:
        capability_name: Fixed to "currency" (not user-settable).
        default_currency: ISO 4217 alpha-3 code (opt-in) used to resolve
            shared bare symbol input (e.g. "$", "¥"). Defaults to None:
            a shared bare symbol is then recognized but never resolved
            (status INVALID). Never remaps a definitive symbol (e.g.
            "€" -> EUR) or a qualified symbol ("US$" -> USD).
        output_format: Canonical output format — "code" (the uppercase
            alpha-3 code) is the only format. Optional — None/"default"/
            "code" all resolve to "code".
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "code"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset()

    capability_name: str = field(default="currency", init=False)

    # Capability-specific field
    default_currency: str | None = None

    def __post_init__(self) -> None:
        """Validate contract configuration.

        Calls the base output_format resolution first, then enforces
        Currency-specific rules: default_currency must be an uppercase
        ISO 4217 alpha-3 code when present.

        Raises:
            ContractError: If output_format is unsupported or
                default_currency is present but not an uppercase alpha-3
                code.
        """
        super().__post_init__()
        _validate_alpha3(self.default_currency)

    @property
    def active_grammars(self) -> tuple[str, ...]:
        """All grammars active by default.

        All three recognition grammars are always active; Currency has no
        input-shape feature flags.

        Returns:
            The three recognition grammar names.
        """
        return ("code_recognition", "symbol_recognition", "word_recognition")
