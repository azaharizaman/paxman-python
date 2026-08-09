"""Currency notation — an ISO 4217 currency identifier as written."""

from __future__ import annotations

from dataclasses import dataclass

_VALID_SHAPES = frozenset({"code", "qualified_symbol", "symbol", "word"})


@dataclass(frozen=True, slots=True)
class CurrencyNotation:
    """A currency identifier (no amount) as written in the input.

    Attributes:
        text: The identifier text. Codes are grammar-folded to uppercase
            and words to lowercase (grammar-owned case folding); symbols
            keep their exact casing.
        shape: One of "code", "qualified_symbol", "symbol", "word".
    """

    text: str
    shape: str

    def __post_init__(self) -> None:
        """Validate the shape and non-empty text.

        Raises:
            ValueError: If text is empty or shape is not a valid shape.
        """
        if not self.text:
            raise ValueError("text must be non-empty")
        if self.shape not in _VALID_SHAPES:
            raise ValueError(
                f"invalid shape {self.shape!r}; expected one of {sorted(_VALID_SHAPES)}"
            )

    def as_list(self) -> list[str]:
        """Flatten the notation for structural equality checks."""
        return [self.text, self.shape]
