"""Contract model: declarative, versioned agreement of kind + optional authority pin.

The key to engine resolution; carries no behavior (PRD §5.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paxman.contracts.authority_pin import AuthorityPin
    from paxman.contracts.kind import Kind


@dataclass(frozen=True, slots=True)
class Contract:
    """Declarative agreement between caller and engine naming the kind of information.

    A contract carries exactly one Kind and an optional AuthorityPin that
    references a real-world standard. It carries no behavior — the caller
    states intent, never how (PRD §5.2).
    """

    kind: Kind
    """The category of information to canonicalize."""

    authority_pin: AuthorityPin | None = None
    """Optional pin to a specific edition of a real-world authority."""
