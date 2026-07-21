"""Verdict: the structured outcome a capability returns — canonical form with evidence,
or an explicit refusal (PRD §5.3). The duality is the soul of Paxman.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paxman.artifacts.evidence import Evidence


@dataclass(frozen=True, slots=True)
class Verdict:
    """A successful canonicalization result: canonical form plus the evidence that justifies it.

    Carried inside an Artifact as the happy-path outcome (PRD §5.3).
    """

    canonical: str
    """The canonical form of the input."""

    evidence: Evidence
    """Structured evidence: rules fired, order, and authority behind this verdict."""
