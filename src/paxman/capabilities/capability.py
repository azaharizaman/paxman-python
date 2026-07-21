"""Capability interface: the uniform contract every domain specialist implements.

Two duties only — declare owned contract kinds, and render a verdict or refusal
(PRD §5.3). The whole game for an extender; engine remains sealed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from paxman.contracts.contract import Contract
    from paxman.contracts.kind import Kind
    from paxman.contracts.refusal import Refusal
    from paxman.contracts.verdict import Verdict


class Capability(Protocol):
    """The uniform interface every domain specialist implements.

    A capability declares which contract kinds it owns and renders a verdict
    (with evidence) or a refusal. Not @runtime_checkable — spec decision #3.
    """

    @property
    def owned_kinds(self) -> frozenset[Kind]:
        """The set of contract kinds this capability owns."""
        ...

    def render(self, raw: str, contract: Contract) -> Verdict | Refusal:
        """Render a canonical verdict or explicit refusal for the given input."""
        ...
