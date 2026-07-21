"""Evidence: the named rules, order, and authority behind a canonical verdict.

The receipt that lets a reader trust the verdict and replay reconstruct it (PRD §5.3).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """The named rules, order, and authority behind a canonical verdict.

    Accompanies a Verdict inside an Artifact so that a reader can understand
    and independently verify the canonical form without re-executing any logic
    (PRD §5.3).
    """

    rules: tuple[str, ...]
    """Ordered references to the standards, rules, or orderings that produced the verdict."""
