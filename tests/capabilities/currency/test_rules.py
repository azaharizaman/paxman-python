"""Tests for Currency capability validation rules.

Rules are exercised directly (no grammar): each test builds a
CurrencyNotation and drives matches()/normalize() against the committed
data tables. Case folding and tokenization are grammar-owned; the rules
perform exact lookups on grammar-folded text (codes uppercase, words
lowercase, symbols verbatim).
"""

from __future__ import annotations

import pytest

from paxman.capabilities.Currency.contract import CurrencyContract
from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.capabilities.Currency.rules.cldr_currencies_ed2025 import (
    SectionNames,
    SectionSymbols,
)
from paxman.capabilities.Currency.rules.iso_4217_ed2015 import SectionCode
from paxman.core.domain import RuleStrategy

pytestmark = [pytest.mark.capability, pytest.mark.currency]


def _notation(text: str, shape: str) -> CurrencyNotation:
    """Build a CurrencyNotation directly (no grammar) for rule-level testing."""
    return CurrencyNotation(text=text, shape=shape)


class TestSectionCode:
    """Tests for SectionCode rule."""

    def setup_method(self) -> None:
        self.rule = SectionCode()

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("USD", "USD"),
            ("GBP", "GBP"),
            ("XAU", "XAU"),
        ],
    )
    def test_canonical_code(self, text: str, expected: str) -> None:
        """Known ISO 4217 alpha-3 codes resolve to the canonical code (D2)."""
        contract = CurrencyContract()
        notation = _notation(text, "code")
        assert self.rule.matches(notation, contract) is True
        assert self.rule.normalize(notation, contract) == expected

    @pytest.mark.parametrize(
        ("text", "shape"),
        [
            ("ZZZ", "code"),
            ("the", "code"),
            ("usd", "code"),
            ("USD", "word"),
            ("USD", "symbol"),
        ],
    )
    def test_rejected(self, text: str, shape: str) -> None:
        """Unknown codes, non-code shapes, and un-folded text are rejected.

        "usd" (lowercase) is rejected here: the grammar folds codes to
        uppercase and the rule does an exact lookup — folding is
        grammar-owned, not rule-owned. "the" is a shape-only false
        positive (Country parity): recognized as a code lookalike but
        not in the code set.
        """
        contract = CurrencyContract()
        notation = _notation(text, shape)
        assert self.rule.matches(notation, contract) is False

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, kind, year, lifecycle, version."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.specification_name == "ISO 4217"
        assert self.rule.provenance.kind == "specification"
        assert self.rule.provenance.publication_year == 2015
        assert self.rule.provenance.lifecycle == "active"
        assert self.rule.provenance.version is None

    def test_citation_mentions_specification(self) -> None:
        """Citation names the ISO 4217:2015 specification."""
        assert "ISO 4217:2015" in self.rule.citation

    def test_citation_mentions_maintenance_agency(self) -> None:
        """Citation names the Maintenance Agency (the code list authority)."""
        assert "Maintenance Agency" in self.rule.citation

    def test_rule_name(self) -> None:
        """Verify name follows the Section-{description} convention (Country style)."""
        assert self.rule.name == "Section-code"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_target_grammars(self) -> None:
        """The code rule targets only the code grammar."""
        assert self.rule.target_grammars == frozenset({"code_recognition"})

    def test_requires_features_empty(self) -> None:
        """The ISO rule never gates on contract features (always runs)."""
        assert self.rule.requires_features == frozenset()


class TestSectionSymbols:
    """Tests for SectionSymbols rule."""

    def setup_method(self) -> None:
        self.rule = SectionSymbols()

    @pytest.mark.parametrize(
        ("text", "shape", "expected"),
        [
            ("US$", "qualified_symbol", "USD"),
            ("\u20ac", "symbol", "EUR"),
        ],
    )
    def test_canonical_symbol_default_contract(
        self, text: str, shape: str, expected: str
    ) -> None:
        """Definitive symbols resolve under the default contract (D6)."""
        contract = CurrencyContract()
        notation = _notation(text, shape)
        assert self.rule.matches(notation, contract) is True
        assert self.rule.normalize(notation, contract) == expected

    @pytest.mark.parametrize(
        "text",
        ["$", "\u00a5", "\u00a3"],
    )
    def test_shared_symbol_default_contract_rejected(self, text: str) -> None:
        """Shared bare symbols ($, ¥, £) are multi-candidate in the committed
        table, so without the default_currency opt-in they are INVALID (D6).

        "£" maps to six codes (FKP, GBP, GIP, SHP, SSP, SYP) in
        SYMBOL_TO_CODES, so it is a shared symbol — not the definitive
        GBP token the plan's prose once claimed. The generic
        multi-candidate path handles it exactly like "$" and "¥".
        """
        contract = CurrencyContract()
        notation = _notation(text, "symbol")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """A word-shaped notation is not validated by the symbol rule."""
        contract = CurrencyContract()
        notation = _notation("US$", "word")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_unknown_symbol(self) -> None:
        """An unknown symbol token is not in SYMBOL_TO_CODES (© is absent)."""
        contract = CurrencyContract()
        notation = _notation("\u00a9", "symbol")
        assert self.rule.matches(notation, contract) is False

    @pytest.mark.parametrize(
        ("text", "shape", "default_currency", "expected"),
        [
            ("$", "symbol", "USD", "USD"),
            ("\u00a5", "symbol", "CNY", "CNY"),
        ],
    )
    def test_shared_symbol_resolves_via_default_currency(
        self, text: str, shape: str, default_currency: str, expected: str
    ) -> None:
        """A shared symbol resolves via the opt-in default_currency (D6)."""
        contract = CurrencyContract(default_currency=default_currency)
        notation = _notation(text, shape)
        assert self.rule.matches(notation, contract) is True
        assert self.rule.normalize(notation, contract) == expected

    def test_unknown_default_currency_never_resolves(self) -> None:
        """A shape-valid but unknown default_currency (ZZZ) is gated against
        CURRENCY_CODES: the shared symbol is INVALID, never resolved (D6).
        """
        contract = CurrencyContract(default_currency="ZZZ")
        notation = _notation("$", "symbol")
        assert self.rule.matches(notation, contract) is False

    @pytest.mark.parametrize(
        ("text", "default_currency"),
        [
            # Valid ISO codes, but NOT candidates of the symbol itself:
            # "$" never means MYR (ringgit's symbol is RM), "£" never means
            # USD, "¥" never means EUR. The opt-in may only pick among the
            # symbol's own candidate codes (D6, tightened per review).
            ("$", "MYR"),
            ("\u00a3", "USD"),
            ("\u00a5", "EUR"),
        ],
    )
    def test_non_candidate_default_currency_rejected(
        self, text: str, default_currency: str
    ) -> None:
        """A valid-but-non-candidate default_currency never resolves the
        shared symbol: the opt-in is gated against the symbol's own candidate
        tuple, not the global CURRENCY_CODES set.
        """
        contract = CurrencyContract(default_currency=default_currency)
        notation = _notation(text, "symbol")
        assert self.rule.matches(notation, contract) is False

    def test_definitive_symbol_never_remapped(self) -> None:
        """A definitive symbol ignores default_currency (never remapped, D6)."""
        contract = CurrencyContract(default_currency="USD")
        notation = _notation("\u20ac", "symbol")
        assert self.rule.matches(notation, contract) is True
        assert self.rule.normalize(notation, contract) == "EUR"

    def test_qualified_symbol_never_remapped(self) -> None:
        """A definitive qualified symbol ignores default_currency (D6)."""
        contract = CurrencyContract(default_currency="CNY")
        notation = _notation("US$", "qualified_symbol")
        assert self.rule.matches(notation, contract) is True
        assert self.rule.normalize(notation, contract) == "USD"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, kind, year, lifecycle, version."""
        assert self.rule.provenance.authority == "Unicode CLDR"
        assert self.rule.provenance.specification_name == "Unicode CLDR"
        assert self.rule.provenance.kind == "specification"
        assert self.rule.provenance.publication_year == 2025
        assert self.rule.provenance.lifecycle == "active"
        assert self.rule.provenance.version == "47"

    def test_rule_name(self) -> None:
        """Verify name follows the Section-{description} convention (Country style)."""
        assert self.rule.name == "Section-symbols"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_target_grammars(self) -> None:
        """The symbol rule targets only the symbol grammar."""
        assert self.rule.target_grammars == frozenset({"symbol_recognition"})

    def test_requires_features_empty(self) -> None:
        """Never gate on default_currency: a shared bare symbol yields
        INVALID, not MISSING.
        """
        assert self.rule.requires_features == frozenset()


class TestSectionNames:
    """Tests for SectionNames rule."""

    def setup_method(self) -> None:
        self.rule = SectionNames()

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("euro", "EUR"),
            ("dollar", "USD"),
            ("ringgit", "MYR"),
            ("pound", "GBP"),
        ],
    )
    def test_canonical_word(self, text: str, expected: str) -> None:
        """Curated display-name words resolve to their code (definitive).

        Words arrive lowercase (the grammar folds them); the table keys
        are lowercase, so the lookup is exact. "pound" is a curated
        definitive token in the committed table (GBP) — the plan's prose
        listed it as non-curated, which the committed data contradicts.
        """
        contract = CurrencyContract()
        notation = _notation(text, "word")
        assert self.rule.matches(notation, contract) is True
        assert self.rule.normalize(notation, contract) == expected

    def test_rejects_unknown_word(self) -> None:
        """Shilling is a real currency word but is not a curated token in
        NAME_TO_CODES, so it is INVALID at the rule level.
        """
        contract = CurrencyContract()
        notation = _notation("shilling", "word")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """A symbol-shaped notation is not validated by the word rule."""
        contract = CurrencyContract()
        notation = _notation("dollar", "symbol")
        assert self.rule.matches(notation, contract) is False

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, kind, year, lifecycle, version."""
        assert self.rule.provenance.authority == "Unicode CLDR"
        assert self.rule.provenance.specification_name == "Unicode CLDR"
        assert self.rule.provenance.kind == "specification"
        assert self.rule.provenance.publication_year == 2025
        assert self.rule.provenance.lifecycle == "active"
        assert self.rule.provenance.version == "47"

    def test_rule_name(self) -> None:
        """Verify name follows the Section-{description} convention (Country style)."""
        assert self.rule.name == "Section-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_target_grammars(self) -> None:
        """The word rule targets only the word grammar."""
        assert self.rule.target_grammars == frozenset({"word_recognition"})

    def test_requires_features_empty(self) -> None:
        """The CLDR name rule never gates on contract features."""
        assert self.rule.requires_features == frozenset()
