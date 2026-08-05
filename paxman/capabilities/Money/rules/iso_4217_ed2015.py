"""ISO 4217:2015 rule: currency code validation.

ISO 4217 assigns alpha-3 currency codes and the minor-unit exponent for
each currency. This rule validates the code against the List One table
and, in strict precision mode, rejects amounts with more decimal digits
than the code's minor units.
"""

from __future__ import annotations

from typing import cast

from paxman.capabilities.Money.contract import MoneyContract
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.capabilities.Money.parsing import (
    ParsedAmount,
    format_amount,
    parse_amount,
)
from paxman.capabilities.Money.rules.data.iso4217_list_one import (
    CURRENCY_CODES,
    MINOR_UNITS,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 4217",
    kind="specification",
    reference_url="https://www.iso.org/iso-4217-currency-codes.html",
    version=None,
    lifecycle="active",
    publication_year=2015,
)


def _valid_amount(
    parsed: ParsedAmount,
    code: str,
    contract: MoneyContract,
) -> bool:
    """Strict over-precision check: the amount may not exceed the minor units.

    Args:
        parsed: Parsed amount to check.
        code: ISO 4217 currency code (guaranteed present in MINOR_UNITS
            because matches() already rejected codes outside CURRENCY_CODES).
        contract: Money contract (precision mode).

    Returns:
        True when precision is not "strict", or when the parsed amount has
        at most MINOR_UNITS[code] decimal digits.
    """
    return not (
        contract.precision == "strict" and parsed.decimal_digits() > MINOR_UNITS[code]
    )


class SectionCode(Rule[MoneyNotation]):
    """ISO 4217 Section: currency codes.

    Validates a "code"-shaped notation: the currency part must be an
    uppercase alpha-3 code in the ISO 4217 List One table, and the amount
    must parse and (in strict precision mode) not exceed the code's minor
    units. Lowercase codes are rejected: case folding is the grammar's
    concern, mirroring how ISBN folds x to X at recognition time.
    """

    name = "Section-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 4217 currency codes"
    target_grammars = frozenset({"code_recognition"})
    requires_features = frozenset()

    def matches(self, notation: MoneyNotation, contract: Contract) -> bool:
        """Check if the notation is a known currency code with a valid amount.

        Args:
            notation: Money notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "code", the code is in CURRENCY_CODES, the
            amount parses, and strict precision is not exceeded.
        """
        if notation.currency_shape != "code":
            return False
        code = notation.currency_part
        if code not in CURRENCY_CODES:
            return False
        typed_contract = cast(MoneyContract, contract)
        parsed = parse_amount(notation.amount_part)
        if parsed is None:
            return False
        return _valid_amount(parsed, code, typed_contract)

    def normalize(self, notation: MoneyNotation, contract: Contract) -> str:
        """Normalize to the canonical CODE + amount form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "{code} {amount}" where the amount is padded, rounded, or
            truncated to the code's minor units per the contract precision.
        """
        typed_contract = cast(MoneyContract, contract)
        parsed = parse_amount(notation.amount_part)
        if parsed is None:
            return notation.amount_part  # unreachable post-matches(); defensive
        minor_units = MINOR_UNITS[notation.currency_part]
        amount = format_amount(parsed, minor_units, typed_contract.precision)
        return f"{notation.currency_part} {amount}"
