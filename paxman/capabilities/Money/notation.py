"""Money notation — intermediate representation for currency amount recognition."""

from __future__ import annotations

from dataclasses import dataclass

_VALID_CURRENCY_SHAPES = frozenset({"code", "symbol", "qualified_symbol", "word"})
_VALID_AMOUNT_SHAPES = frozenset(
    {"integer", "dot_decimal", "comma_decimal", "space_decimal", "accounting"}
)


@dataclass(frozen=True, slots=True)
class MoneyNotation:
    """Intermediate representation for currency amount recognition.

    Attributes:
        currency_part: The currency token as written (e.g., "USD", "$", "CA$",
            "euro"), taken verbatim from the input by the grammar.
        amount_part: The amount token as written (e.g., "1,234.56", "500"),
            taken verbatim from the input by the grammar.
        currency_shape: Discriminator assigned by the grammar: "code",
            "symbol", "qualified_symbol", or "word"; "" when not yet assigned.
        amount_shape: Discriminator assigned by the grammar: "integer",
            "dot_decimal", "comma_decimal", "space_decimal", or "accounting";
            "" when not yet assigned.
    """

    currency_part: str
    amount_part: str
    currency_shape: str = ""
    amount_shape: str = ""

    def __post_init__(self) -> None:
        """Validate shape discriminators.

        Grammars assign only the enumerated values; "" is the allowed unset
        default. Any other value is a recognition-layer bug surfaced loudly.

        Raises:
            ValueError: If a shape field holds a value outside its enumerated
                set (the empty string is the allowed unset sentinel).
        """
        if self.currency_shape and self.currency_shape not in _VALID_CURRENCY_SHAPES:
            raise ValueError(f"invalid currency_shape: {self.currency_shape!r}")
        if self.amount_shape and self.amount_shape not in _VALID_AMOUNT_SHAPES:
            raise ValueError(f"invalid amount_shape: {self.amount_shape!r}")
