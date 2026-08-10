"""Date contract for Date capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.contract import CapabilityContract


@dataclass(frozen=True)
class DateContract(CapabilityContract):
    """User-facing contract for Date capability.

    Date's default canonical output is ``"ISO"``. Accepted ``output_format``
    values are ``None`` (unset), ``"default"``, ``"ISO"`` (the default), and
    the offered alternative ``"US"``; anything else raises
    :class:`ContractError` from the base ``__post_init__``.
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "ISO"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset({"US"})

    capability_name: str = field(default="date", init=False)
    two_digit_base_year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        return [
            "iso8601_recognition",
            "us_recognition",
            "european_recognition",
        ]
