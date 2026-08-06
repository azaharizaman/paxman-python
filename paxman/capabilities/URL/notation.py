"""URL notation types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class URLNotation:
    """URL notation: a single URL string.

    Shape-only carrier (D15): it stores the recognized text exactly as
    scanned and never validates it — validity is the rule layer's job (D7).
    The single ``text`` component maps one-to-one through ``as_list()``.
    """

    text: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.text]
