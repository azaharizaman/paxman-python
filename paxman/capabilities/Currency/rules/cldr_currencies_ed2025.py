"""Unicode CLDR currency rules: currency symbols and display names.

Currency symbols and display names share the CLDR publication and lookup
tables. Both rules resolve a symbol/word token to an ISO 4217 code: a
token with exactly one candidate is definitive; a multi-candidate token
resolves via the opt-in ``contract.default_currency`` (None, the default,
-> matches() False -> INVALID, never silently dropped).
"""

from __future__ import annotations

from typing import cast

from paxman.capabilities.Currency.contract import CurrencyContract
from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.capabilities.Currency.rules.data.cldr_currencies import (
    NAME_TO_CODES,
    SYMBOL_TO_CODES,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="Unicode CLDR",
    specification_name="Unicode CLDR",
    kind="specification",
    reference_url="https://cldr.unicode.org/",
    version="47",
    lifecycle="active",
    publication_year=2025,
)


def _resolve_symbol_code(
    notation: CurrencyNotation,
    contract: CurrencyContract,
) -> str | None:
    """Resolve a symbol/qualified_symbol notation to an ISO 4217 code.

    A token with exactly one candidate resolves to it; a multi-candidate
    token (e.g. "$", "¥") resolves via the opt-in ``contract.default_currency``
    when that code is one of the token's own candidates (guarded against the
    symbol's candidate tuple, not the global CURRENCY_CODES set, so a valid
    code that never represents the symbol — "$" with MYR — can never produce
    a SUCCESS). Resolves to None otherwise, which makes matches() return
    False (INVALID).

    Args:
        notation: Currency notation to resolve.
        contract: Currency contract (default_currency).

    Returns:
        The resolved ISO 4217 code, or None when no code can be resolved.
    """
    codes = SYMBOL_TO_CODES.get(notation.text)
    if codes is None:
        return None
    if len(codes) == 1:
        return codes[0]
    candidate = contract.default_currency
    return candidate if candidate in codes else None


def _resolve_name_code(
    notation: CurrencyNotation,
    contract: CurrencyContract,
) -> str | None:
    """Resolve a word notation to an ISO 4217 code.

    The grammar folded the word to lowercase; the table keys are
    lowercase, so the lookup is exact. Same definitiveness policy as
    symbols (single candidate definitive; multi-candidate via the opt-in
    default_currency, gated against the token's own candidate tuple).

    Args:
        notation: Currency notation to resolve.
        contract: Currency contract (default_currency).

    Returns:
        The resolved ISO 4217 code, or None when no code can be resolved.
    """
    codes = NAME_TO_CODES.get(notation.text)
    if codes is None:
        return None
    if len(codes) == 1:
        return codes[0]
    candidate = contract.default_currency
    return candidate if candidate in codes else None


class SectionSymbols(Rule[CurrencyNotation]):
    """CLDR Section: currency symbols.

    Validates "symbol"/"qualified_symbol" shapes. A definitive token
    resolves to its single candidate; a multi-candidate token resolves
    via ``contract.default_currency`` when set to one of the token's own
    candidate codes.
    """

    name = "Section-symbols"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "CLDR v47 currency symbols"
    target_grammars = frozenset({"symbol_recognition"})
    requires_features = frozenset()

    def matches(self, notation: CurrencyNotation, contract: Contract) -> bool:
        """Check if the notation is a resolvable currency symbol.

        Args:
            notation: Currency notation to validate.
            contract: Contract configuration.

        Returns:
            True if the shape is "symbol"/"qualified_symbol" and a code
            can be resolved.
        """
        if notation.shape not in ("symbol", "qualified_symbol"):
            return False
        typed_contract = cast(CurrencyContract, contract)
        return _resolve_symbol_code(notation, typed_contract) is not None

    def normalize(self, notation: CurrencyNotation, contract: Contract) -> str:
        """Normalize to the canonical alpha-3 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            The resolved uppercase code.
        """
        typed_contract = cast(CurrencyContract, contract)
        code = _resolve_symbol_code(notation, typed_contract)
        return code if code is not None else notation.text  # unreachable post-matches()


class SectionNames(Rule[CurrencyNotation]):
    """CLDR Section: currency display names.

    Validates "word" shapes. Same definitiveness policy as SectionSymbols.
    """

    name = "Section-names"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "CLDR v47 currency display names"
    target_grammars = frozenset({"word_recognition"})
    requires_features = frozenset()

    def matches(self, notation: CurrencyNotation, contract: Contract) -> bool:
        """Check if the notation is a resolvable display-name word.

        Args:
            notation: Currency notation to validate.
            contract: Contract configuration.

        Returns:
            True if the shape is "word" and a code can be resolved.
        """
        if notation.shape != "word":
            return False
        typed_contract = cast(CurrencyContract, contract)
        return _resolve_name_code(notation, typed_contract) is not None

    def normalize(self, notation: CurrencyNotation, contract: Contract) -> str:
        """Normalize to the canonical alpha-3 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            The resolved uppercase code.
        """
        typed_contract = cast(CurrencyContract, contract)
        code = _resolve_name_code(notation, typed_contract)
        return code if code is not None else notation.text  # unreachable post-matches()
