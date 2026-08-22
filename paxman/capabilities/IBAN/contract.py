"""IBAN contract — user-facing configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.capability_contract import CapabilityContract


@dataclass(frozen=True)
class IBANContract(CapabilityContract):
    """User-facing contract for IBAN capability."""

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "electronic"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset({"paper"})

    capability_name: str = field(default="iban", init=False)
