"""Evidence: the named rules, order, and authority behind a canonical verdict.

The receipt that lets a reader trust the verdict and replay reconstruct it (PRD §5.3).

Note: In V1, Verdict.evidence is a plain str because no bundled capabilities exist
yet. This Evidence type is reserved for future use when real capabilities arrive
and need structured, machine-readable evidence (PRD §11 roadmap).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """Structured evidence behind a canonical verdict.

    Reserved for future use when real capabilities need machine-readable
    evidence (PRD §11 roadmap). In V1, Verdict.evidence is a plain str.
    """

    rules: tuple[str, ...]
    """Ordered references to the standards, rules, or orderings that produced the verdict."""
