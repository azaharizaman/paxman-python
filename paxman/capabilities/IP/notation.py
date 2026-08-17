"""IP notation types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IPNotation:
    """IP address notation: a single address string."""

    address: str
