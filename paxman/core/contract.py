from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Contract(Protocol):
    """Base protocol for all capability contracts."""

    @property
    def capability_name(self) -> str:
        """Name of the capability this contract configures."""
        ...

    @property
    def active_grammars(self) -> list[str]:
        """List of grammar names to activate."""
        ...

    @property
    def excluded_rules(self) -> list[str]:
        """List of rule names to exclude."""
        ...

    @property
    def year(self) -> int | None:
        """Year for temporal filtering (publication_year <= year)."""
        ...

    def as_dict(self) -> dict[str, Any]:
        """Serialize contract for replay_hash."""
        ...
