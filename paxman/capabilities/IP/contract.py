"""IP contract for IP capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.contract import CapabilityContract


@dataclass(frozen=True)
class IPContract(CapabilityContract):
    """User-facing contract for IP capability."""

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "ip"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset()

    capability_name: str = field(default="ip", init=False)
    include_ipv6: bool = True

    @property
    def active_grammars(self) -> list[str]:
        grammars: list[str] = ["ipv4_recognition"]
        if self.include_ipv6:
            grammars.append("ipv6_recognition")
        return grammars
