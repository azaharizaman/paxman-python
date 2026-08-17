"""SI unit notation — an SI unit expression as written."""

from __future__ import annotations

from dataclasses import dataclass

_VALID_SHAPES = frozenset(
    {
        "symbol",
        "name",
        "compound",
        # A word/symbol prefix split across whitespace from its unit, captured
        # as ONE span so the trailing unit is never emitted as a competing
        # candidate (see grammar subsumption + split-prefix rules).
        "split_word_prefix",
        "split_symbol_prefix",
    }
)


@dataclass(frozen=True, slots=True)
class SIUnitNotation:
    """An SI unit (no quantity, no magnitude) as written in the input.

    Attributes:
        text: The unit text. Symbols keep their exact casing; names are
            grammar-folded to lowercase; compounds keep the written form.
        shape: One of "symbol", "name", "compound", "split_word_prefix", "split_symbol_prefix".
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
