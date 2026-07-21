"""Evidence: the named rules, order, and authority behind a canonical verdict.

The receipt that lets a reader trust the verdict and replay reconstruct it (PRD §5.3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paxman.contracts.authority_pin import AuthorityPin


@dataclass(frozen=True, slots=True)
class Evidence:
    """Structured evidence behind a canonical verdict.

    Records which rules fired, in what order, against which authority edition.
    Carried inside a Verdict so the result is fully self-describing (PRD §5.3).
    """

    rules_fired: tuple[str, ...]
    """Ordered references to the standards, rules, or orderings that produced the verdict."""

    order: int
    """Number of rules applied, for ordering and audit trails."""

    authority: AuthorityPin
    """The pinned authority edition this verdict was produced against."""
