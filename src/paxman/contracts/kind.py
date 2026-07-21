"""Contract kind: names the category of information being canonicalized.

Drives deterministic lookup of the single owning capability (PRD §5.2).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Kind:
    """Names the category of information being canonicalized.

    Every contract carries exactly one Kind, and every capability declares which
    Kinds it owns. The engine resolves a contract to its single owning
    capability via this name (PRD §5.2).
    """

    name: str
    """Unique identifier for this kind (e.g. 'email.address', 'date.iso')."""
