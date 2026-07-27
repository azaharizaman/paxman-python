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
    def pinned_rules(self) -> Sequence[str] | None:
        """Pin to specific rules by name. If set, ONLY these rules run.

        Takes precedence over excluded_rules — when pinned_rules is non-None,
        excluded_rules is ignored. Year filtering still applies after pinning.
        An empty tuple () pins to nothing (no rules run).
        """
        ...

    @property
    def year(self) -> int | None:
        """Year for temporal filtering (publication_year <= year)."""
        ...

    @property
    def output_format(self) -> str | None:
        """Output format for canonical values (e.g., 'ISO', 'US')."""
        ...

    def as_dict(self) -> dict[str, Any]:
        """Serialize contract for replay_hash."""
        ...
