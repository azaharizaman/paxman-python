"""Integration tests for the Currency capability pipeline."""

import pytest

from paxman.api import canonicalize
from paxman.capabilities.Currency.capability import CurrencyCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Reset the capability registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


class TestCurrencyPipeline:
    """Full-pipeline tests for the Currency capability.

    Locked semantics (plan §1 e2e contract):
    - identifier-only: amounts are the Money capability's domain. ``USD 500``
      resolves via its ``USD`` span; amount-glued tokens (``US$5``, ``$500``)
      are not recognized at all -> MISSING (whole-token discipline, D5);
    - the code grammar is case-insensitive ``[A-Za-z]{3}`` (D3): ``usd`` /
      ``Gbp`` fold to uppercase at recognition and resolve, never MISSING;
    - the word grammar folds to lowercase (D4): ``euro`` / ``Euro`` both
      resolve via the lowercase-key CLDR name table;
    - shared bare symbols (``$`` -> 29 codes, ``£`` -> 6 codes, ``¥`` -> 2
      codes) are INVALID without the ``default_currency`` opt-in (D6); the
      opt-in is gated against ``CURRENCY_CODES`` and never remaps a
      definitive (``€`` -> EUR) or qualified (``US$`` -> USD) symbol;
    - a standalone 3-letter code shape that is not a known code (``ZZZ``,
      ``the``) is a recognized-but-unvalidated false positive -> INVALID
      (Country parity); prose that no grammar matches (``hello world``)
      is MISSING, and the plural ``Dollars`` is blocked by the word-boundary
      guard -> MISSING, never partial-matched;
    - INVALID rows carry no candidates (recognized, but no rule validated
      them) and MISSING rows carry no candidates (nothing recognized).
    """

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "text,contract_kwargs,expected_status,expected_value",
        [
            # --- SUCCESS rows ---
            ("USD", {}, Resolution.SUCCESS, "USD"),
            ("usd", {}, Resolution.SUCCESS, "USD"),  # D3: case-insensitive code
            ("Gbp", {}, Resolution.SUCCESS, "GBP"),
            ("GBP", {}, Resolution.SUCCESS, "GBP"),
            ("US$", {}, Resolution.SUCCESS, "USD"),  # qualified symbol
            ("\u20ac", {}, Resolution.SUCCESS, "EUR"),  # definitive bare symbol
            # D6 opt-in path: £ is shared (6 candidates), so the opt-in is
            # required to resolve it — locks the shared-symbol opt-in.
            ("\u00a3", {"default_currency": "GBP"}, Resolution.SUCCESS, "GBP"),
            ("$", {"default_currency": "USD"}, Resolution.SUCCESS, "USD"),
            ("\u00a5", {"default_currency": "CNY"}, Resolution.SUCCESS, "CNY"),
            ("euro", {}, Resolution.SUCCESS, "EUR"),  # lowercase word (D4)
            ("Euro", {}, Resolution.SUCCESS, "EUR"),
            ("US Dollar", {}, Resolution.SUCCESS, "USD"),
            ("XAU", {}, Resolution.SUCCESS, "XAU"),  # D2: full code set
            ("USD 500", {}, Resolution.SUCCESS, "USD"),
            # --- INVALID rows ---
            # CORRECTED from the plan (was SUCCESS "GBP"): committed data
            # SYMBOL_TO_CODES["£"] == ("FKP", "GBP", "GIP", "SHP", "SSP",
            # "SYP") — 6 candidates, a SHARED symbol. Per D6, a shared bare
            # symbol without default_currency opt-in is INVALID.
            ("\u00a3", {}, Resolution.INVALID, None),
            ("$", {}, Resolution.INVALID, None),  # shared: 29 candidates
            ("ZZZ", {}, Resolution.INVALID, None),  # shape-valid, unknown code
            ("the", {}, Resolution.INVALID, None),  # shape-only false positive
            # --- MISSING rows ---
            # CORRECTED from the plan (was INVALID): the word grammar is a
            # lexicon with word-boundary guards — "Dollars" is not a token in
            # WORD_TOKENS and the plural suffix is blocked, so nothing is
            # recognized (test_grammar.py locks ("Dollars", [])).
            ("Dollars", {}, Resolution.MISSING, None),
            ("US$5", {}, Resolution.MISSING, None),  # amount-glued (D5)
            ("$500", {}, Resolution.MISSING, None),  # amount-glued (D5)
            ("hello world", {}, Resolution.MISSING, None),
            ("123", {}, Resolution.MISSING, None),
            ("", {}, Resolution.MISSING, None),
        ],
    )
    def test_e2e_contract(
        self,
        text: str,
        contract_kwargs: dict[str, str],
        expected_status: Resolution,
        expected_value: str | None,
    ) -> None:
        """Every row of the plan §1 e2e contract through canonicalize()."""
        register_capability(CurrencyCapability())
        default_currency = contract_kwargs.get("default_currency")
        contract = CurrencyCapability.create_contract(default_currency=default_currency)
        result = canonicalize(text, contract)
        assert result.status == expected_status
        assert result.canonicalized_value == expected_value
        if expected_status != Resolution.SUCCESS:
            assert result.candidates == ()

    @pytest.mark.integration
    def test_provenance_code_iso_4217(self) -> None:
        """A code SUCCESS carries ISO 4217 provenance (Section-code)."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("USD", contract)
        assert result.status == Resolution.SUCCESS
        candidate = result.candidates[0]
        assert candidate.validation_rule == "Section-code"
        prov = candidate.provenance[0]
        assert prov.specification_name == "ISO 4217"
        assert prov.authority == "ISO"

    @pytest.mark.integration
    def test_provenance_symbol_unicode_cldr(self) -> None:
        """A definitive symbol SUCCESS carries Unicode CLDR provenance."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("\u20ac", contract)
        assert result.status == Resolution.SUCCESS
        candidate = result.candidates[0]
        assert candidate.validation_rule == "Section-symbols"
        prov = candidate.provenance[0]
        assert prov.specification_name == "Unicode CLDR"
        assert prov.authority == "Unicode CLDR"

    @pytest.mark.integration
    def test_provenance_word_unicode_cldr(self) -> None:
        """A word SUCCESS carries Unicode CLDR provenance (Section-names)."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("euro", contract)
        assert result.status == Resolution.SUCCESS
        candidate = result.candidates[0]
        assert candidate.validation_rule == "Section-names"
        prov = candidate.provenance[0]
        assert prov.specification_name == "Unicode CLDR"
        assert prov.authority == "Unicode CLDR"

    @pytest.mark.integration
    def test_frozen_registry_second_call_succeeds(self) -> None:
        """The registry freezes on first canonicalize(); a second call succeeds.

        The engine freezes the registry at pipeline start and never
        re-registers, so two calls through the same registered capability
        both resolve (never a CapabilityError on the second call).
        """
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        first = canonicalize("USD", contract)
        second = canonicalize("EUR", contract)
        assert first.status == Resolution.SUCCESS
        assert first.canonicalized_value == "USD"
        assert second.status == Resolution.SUCCESS
        assert second.canonicalized_value == "EUR"
