"""IP contract for IP capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class IPContract:
    """User-facing contract for IP capability."""

    capability_name: str = field(default="ip", init=False)
    include_ipv6: bool = True
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None

    @property
    def active_grammars(self) -> list[str]:
        grammars: list[str] = ["ipv4_recognition"]
        if self.include_ipv6:
            grammars.append("ipv6_recognition")
        return grammars

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "include_ipv6": self.include_ipv6,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
            "output_format": self.output_format,
        }
