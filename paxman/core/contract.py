from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Contract(Protocol):
    """Base protocol for all capability contracts."""

    @property
    def capability_name(self) -> str:
        """Name of the capability this contract configures."""
        ...

    @property
    def active_grammars(self) -> Sequence[str]:
        """Grammar names to activate."""
        ...

    @property
    def excluded_rules(self) -> Sequence[str]:
        """Rule names to exclude."""
        ...

    @property
    def year(self) -> int | None:
        """Year for temporal filtering (publication_year <= year)."""
        ...

    @property
    def output_format(self) -> str | None:
        """Output format for canonical values (e.g., 'ISO', 'US')."""
        ...

    @property
    def two_digit_base_year(self) -> int | None:
        """Base year for interpreting two-digit years (e.g., 2000 for '25' -> 2025)."""
        ...

    def as_dict(self) -> dict[str, Any]:
        """Serialize contract for replay_hash."""
        ...
