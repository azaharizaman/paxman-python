"""SI Unit contract — user-facing configuration for SI Unit capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.capability_contract import CapabilityContract


@dataclass(frozen=True)
class SIUnitContract(CapabilityContract):
    """User-facing configuration for SI Unit capability.

    Attributes:
        capability_name: Fixed to "si_unit" (not user-settable).
        output_format: Canonical output format — "symbol" (the canonical
            unit symbol) is the only format. Optional — None/"default"/
            "symbol" all resolve to "symbol".
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over
            excluded_rules).
        year: Year for temporal filtering.
        extra_grammars: Community grammar names (opt-in) to run alongside
            the shipped grammars, in order (SEAM — inherited from base).
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "symbol"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset()

    capability_name: str = field(default="si_unit", init=False)
