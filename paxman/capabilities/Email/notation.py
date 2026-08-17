"""Email notation types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmailNotation:
    """Email notation: local_part and domain_part."""

    local_part: str
    domain_part: str
