"""The registry: collects capability claims into a fixed table and freezes it.

Guardian of Invariant 2 (Determinism) by making the mapping observable (PRD §5.4).
"""

from __future__ import annotations

import types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paxman.capabilities.capability import Capability
    from paxman.contracts.contract import Contract
    from paxman.contracts.kind import Kind


class Registry:
    """Frozen mapping from contract kinds to the single owning capability.

    Constructed once, then immutable for the life of the process. Resolution
    is a closed lookup — no scoring, no ranking, no negotiation (PRD §5.4).
    """

    def __init__(self, capabilities: list[Capability]) -> None:
        """Build the registry, checking for overlapping owned kinds.

        Raises ValueError if any two capabilities claim overlapping kinds.
        """
        kind_map: dict[Kind, Capability] = {}
        for cap in capabilities:
            for kind in cap.owned_kinds:
                if kind in kind_map:
                    existing = kind_map[kind]
                    raise ValueError(
                        f"Overlap: kind '{kind.name}' is owned by both "
                        f"{type(existing).__name__} and {type(cap).__name__}"
                    )
                kind_map[kind] = cap
        self._capabilities = types.MappingProxyType(kind_map)

    def resolve(self, contract: Contract) -> Capability | None:
        """Look up the single owning capability for a contract's kind.

        Returns the capability that owns the kind, or None if no capability
        claims it.
        """
        return self._capabilities.get(contract.kind)
