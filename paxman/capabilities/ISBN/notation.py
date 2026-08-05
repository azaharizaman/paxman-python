"""ISBN notation: shape discriminator + normalized digit string."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ISBNNotation:
    """ISBN shape discriminator + normalized digit string.

    ``shape`` is "isbn10" or "isbn13". ``digits`` is the digit string;
    ``X`` is allowed only as the final char of an "isbn10" shape.
    """

    shape: str
    digits: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for the generic Rule interface."""
        return [self.shape, self.digits]
