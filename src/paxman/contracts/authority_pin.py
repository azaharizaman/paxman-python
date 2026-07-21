"""Authority pin: optional reference to a specific edition of a real-world authority.

Recorded in the artifact so verdicts stay reproducible against the same standard
(PRD §5.2, §5.5).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthorityPin:
    """Pins a verdict to a specific edition of a real-world authority.

    When a contract carries an AuthorityPin, the engine passes it to the
    capability before delegation so the verdict is produced against that
    exact standard (PRD §5.5).
    """

    authority: str
    """Name of the authority (e.g. 'iana', 'unicode', 'iso')."""

    edition: str
    """Named edition of the authority (e.g. '2024a', '15.0')."""
