"""Refusal: a first-class, reasoned statement that the input determines no unique form.

Stored in the artifact exactly like a success (PRD §5.3). Refusing is a feature.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paxman.contracts.kind import Kind


@dataclass(frozen=True, slots=True)
class Refusal:
    """An explicit statement that the input does not determine a unique canonical form.

    Carried inside an Artifact as the equally-valid alternative to a Verdict.
    Refusal is a first-class result, not an error (PRD §5.3).
    """

    reason: str
    """Human-readable explanation of why canonical form cannot be determined."""

    kind: Kind
    """The contract kind that was refused — identifies what could not be canonicalized."""
