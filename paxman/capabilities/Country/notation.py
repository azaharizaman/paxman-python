"""Country notation — intermediate representation for country recognition."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CountryNotation:
    """Intermediate representation for country recognition.

    Attributes:
        shape: Discriminator set by grammar ("alpha2", "alpha3", "numeric", "name").
        value: Raw input value (e.g., "US", "USA", "840", "United States").
    """

    shape: str
    value: str
