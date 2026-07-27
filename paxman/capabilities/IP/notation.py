"""IP notation types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IPNotation:
    """IP address notation: a single address string."""

    address: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.address]
