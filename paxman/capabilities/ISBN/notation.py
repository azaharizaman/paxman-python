"""ISBN notation: shape discriminator + normalized digit string."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ISBNNotation:
    """ISBN shape discriminator + normalized digit string.

    ``shape`` is "isbn10" or "isbn13". ``digits`` is the digit string;
    ``X`` is allowed only as the final char of an "isbn10" shape.
    """

    shape: Literal["isbn10", "isbn13"]
    digits: str
