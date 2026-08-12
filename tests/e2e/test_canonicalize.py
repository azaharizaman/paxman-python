"""End-to-end tests for the public canonicalize() API."""

from __future__ import annotations

import pytest

from paxman.api import canonicalize
from paxman.capabilities.Currency.capability import CurrencyCapability
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.capabilities.SIUnit.capability import SIUnitCapability
from paxman.capabilities.URL.capability import URLCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.core.errors import CapabilityError


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


class TestCanonicalize:
    @pytest.mark.e2e
    def test_standard_email(self):
        """Standard email canonicalization via public API."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract()
        result = canonicalize("user@example.com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.e2e
    def test_obfuscated_email(self):
        """Obfuscated email canonicalization via public API."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract(include_obfuscated=True)
        result = canonicalize("user at example dot com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.e2e
    def test_localhost_email(self):
        """Localhost email canonicalization via public API."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract()
        result = canonicalize("admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.e2e
    def test_no_match_returns_missing(self):
        """Input with no email patterns returns MISSING."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract()
        result = canonicalize("hello world", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None

    @pytest.mark.e2e
    def test_unknown_capability_raises_error(self):
        """Unknown capability name raises CapabilityError."""

        class FakeContract:
            @property
            def capability_name(self) -> str:
                return "nonexistent"

            @property
            def active_grammars(self) -> list[str]:
                return []

            @property
            def excluded_rules(self) -> list[str]:
                return []

            @property
            def year(self) -> int | None:
                return None

            @property
            def output_format(self) -> str | None:
                return None

        with pytest.raises(CapabilityError, match="Unknown capability"):
            canonicalize("test", FakeContract())


class TestDateCapabilityE2E:
    """End-to-end tests for Date capability via public API."""

    @pytest.mark.e2e
    def test_iso_date(self) -> None:
        """ISO date canonicalization via public API."""
        register_capability(DateCapability())
        contract = DateCapability.create_contract()
        result = canonicalize("2026-01-15", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-01-15"

    @pytest.mark.e2e
    def test_date_ambiguity(self) -> None:
        """Ambiguous date returns AMBIGUOUS status."""
        register_capability(DateCapability())
        contract = DateCapability.create_contract()
        result = canonicalize("07/02/2026", contract)
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None


class TestCanonicalizePhone:
    """End-to-end tests for the Phone capability through paxman.canonicalize."""

    @pytest.mark.e2e
    def test_canonicalize_phone_success(self) -> None:
        """Full happy path through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("+44 20 7946 0958", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+442079460958"

    @pytest.mark.e2e
    def test_canonicalize_phone_national(self) -> None:
        """National number with default_country through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(default_country="US")
        result = canonicalize("(555) 234-5678", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+15552345678"

    @pytest.mark.e2e
    def test_canonicalize_phone_missing(self) -> None:
        """No phone pattern recognized."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("no phone number here", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_canonicalize_phone_invalid(self) -> None:
        """Unassigned country code is invalid."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("+999123456789", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.e2e
    def test_canonicalize_phone_with_options(self) -> None:
        """output_format option through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(output_format="rfc3966")
        result = canonicalize("+15551234567", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "tel:+15551234567"

    @pytest.mark.e2e
    def test_canonicalize_phone_email_plus_tag_missing(self) -> None:
        """Email plus-addresses are not phone numbers (public API)."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("user+1555@example.com", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_canonicalize_phone_no_plus_tel_uri(self) -> None:
        """No-plus tel: URIs are local numbers — not global candidates."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("tel:2125550123", contract)
        assert result.status == Resolution.INVALID
        assert all(c.validation_rule != "Section 3-tel-uri" for c in result.candidates)


class TestURLCapabilityE2E:
    """End-to-end tests for the URL capability through paxman.canonicalize."""

    @pytest.mark.e2e
    def test_url_capability_milestone(self) -> None:
        """Milestone: absolute URI canonicalizes through the full pipeline."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("HTTPS://Example.COM:443/path/../other", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "https://example.com/other"

    @pytest.mark.e2e
    def test_url_missing(self) -> None:
        """Input with no absolute-URI pattern returns MISSING."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("no url here", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_url_invalid_port(self) -> None:
        """Out-of-range port is recognized but rejected by the WHATWG rule."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("http://example.com:99999/", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.e2e
    def test_url_opaque_scheme_verbatim(self) -> None:
        """Opaque (non-special) schemes serialize verbatim."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("mailto:user@example.com", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "mailto:user@example.com"


class TestCurrencyCapabilityE2E:
    """End-to-end tests for the Currency capability through paxman.canonicalize.

    Rows are the public-API-facing subset of the plan §1 e2e contract,
    with the two Task-8 corrections applied (the £ shared-symbol row and
    the Dollars plural row — see the marked tests below).
    """

    @pytest.mark.e2e
    def test_currency_milestone_qualified_symbol(self) -> None:
        """Milestone: "US$" resolves to "USD" via the qualified symbol."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("US$", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "USD"

    @pytest.mark.e2e
    def test_currency_milestone_lowercase_word(self) -> None:
        """Milestone: "euro" resolves to "EUR" via the lowercase word (D4)."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("euro", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "EUR"

    @pytest.mark.e2e
    def test_currency_milestone_code(self) -> None:
        """Milestone: "GBP" resolves to "GBP"."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("GBP", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "GBP"

    @pytest.mark.e2e
    def test_currency_case_insensitive_code(self) -> None:
        """D3: the case-insensitive code grammar folds "usd" to "USD"."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("usd", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "USD"

    @pytest.mark.e2e
    def test_currency_definitive_bare_symbol(self) -> None:
        """A definitive bare symbol ("€") resolves without any opt-in."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("\u20ac", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "EUR"

    @pytest.mark.e2e
    def test_currency_pound_shared_symbol_invalid(self) -> None:
        """CORRECTED from the plan §1 table (was SUCCESS "GBP"): "£" is a
        SHARED bare symbol — SYMBOL_TO_CODES["£"] has 6 candidates (FKP, GBP,
        GIP, SHP, SSP, SYP) — so without the default_currency opt-in it is
        INVALID (D6), never SUCCESS "GBP" (Task 8 correction, locked in
        tests/integration/test_currency_pipeline.py).
        """
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("\u00a3", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.e2e
    def test_currency_bare_dollar_invalid_without_opt_in(self) -> None:
        """D6: shared "$" (29 dollar-family candidates) is INVALID without opt-in."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("$", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.e2e
    def test_currency_bare_dollar_with_default_currency(self) -> None:
        """D6 opt-in: "$" with default_currency="USD" resolves to "USD"."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract(default_currency="USD")
        result = canonicalize("$", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "USD"

    @pytest.mark.e2e
    def test_currency_full_code_set_no_minor_units(self) -> None:
        """D2: "XAU" (no minor units) resolves — the full 178-code set."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("XAU", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "XAU"

    @pytest.mark.e2e
    def test_currency_code_span_amount_ignored(self) -> None:
        """USD 500 resolves via its USD span; amounts are Money's domain."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("USD 500", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "USD"

    @pytest.mark.e2e
    def test_currency_unknown_code_invalid(self) -> None:
        """ZZZ is shape-valid but unknown — recognized but INVALID."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("ZZZ", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.e2e
    def test_currency_plural_word_missing(self) -> None:
        """CORRECTED from the plan §1 table (was INVALID): "Dollars" is not a
        WORD_TOKENS entry and the plural suffix is blocked by the word-boundary
        guard — nothing is recognized, so MISSING, never INVALID (Task 8
        correction, locked in tests/integration/test_currency_pipeline.py).
        """
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("Dollars", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_currency_amount_glued_token_missing(self) -> None:
        """D5 whole-token discipline: amount-glued "US$5" is never partial-matched."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("US$5", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_currency_empty_input_missing(self) -> None:
        """Empty input matches nothing — MISSING."""
        register_capability(CurrencyCapability())
        contract = CurrencyCapability.create_contract()
        result = canonicalize("", contract)
        assert result.status == Resolution.MISSING


class TestSIUnitCapabilityE2E:
    """End-to-end tests for the SI Unit capability through paxman.canonicalize.

    Rows are the full plan §1 e2e contract (27 rows, plan lines 192–219):
    the three Milestone rows first, then the SUCCESS/INVALID/MISSING/
    AMBIGUOUS remainder, ending with the cross-capability "USD" row.
    """

    @pytest.mark.e2e
    def test_si_unit_milestone_name_kilogram(self) -> None:
        """Milestone: "Kilogram" resolves to "kg" via the name fold (D4)."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("Kilogram", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "kg"

    @pytest.mark.e2e
    def test_si_unit_milestone_prefixed_name_megahertz(self) -> None:
        """Milestone: "megahertz" resolves to "MHz" via the generated prefix name."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("megahertz", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "MHz"

    @pytest.mark.e2e
    def test_si_unit_milestone_compound(self) -> None:
        """Milestone: "m/s²" resolves to "m/s2" via the compound rule."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m/s²", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "m/s2"

    @pytest.mark.e2e
    def test_si_unit_name_kelvin(self) -> None:
        """The name "Kelvin" resolves to "K" via the BIPM Table 1 name rule."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("Kelvin", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "K"

    @pytest.mark.e2e
    def test_si_unit_base_symbol_metre(self) -> None:
        """Base-unit symbol "m" resolves to itself."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "m"

    @pytest.mark.e2e
    def test_si_unit_base_symbol_kilogram(self) -> None:
        """Base-unit symbol "kg" resolves to itself."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("kg", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "kg"

    @pytest.mark.e2e
    def test_si_unit_base_symbol_candela(self) -> None:
        """Base-unit symbol "cd" resolves to itself."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("cd", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "cd"

    @pytest.mark.e2e
    def test_si_unit_derived_symbol_pascal(self) -> None:
        """Derived special-name symbol "Pa" resolves to itself."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("Pa", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "Pa"

    @pytest.mark.e2e
    def test_si_unit_nonsi_symbol_degree_celsius(self) -> None:
        """Non-SI symbol "°C" resolves to itself."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("°C", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "°C"

    @pytest.mark.e2e
    def test_si_unit_litre_lowercase_l(self) -> None:
        """D3: the lowercase written form "l" canonicalizes to "L"."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("l", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "L"

    @pytest.mark.e2e
    def test_si_unit_litre_uppercase_l(self) -> None:
        """Non-SI symbol "L" resolves to itself."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("L", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "L"

    @pytest.mark.e2e
    def test_si_unit_prefixed_symbol_km(self) -> None:
        """Prefixed symbol "km" resolves to itself (BIPM §3.2)."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("km", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "km"

    @pytest.mark.e2e
    def test_si_unit_prefixed_symbol_microgram(self) -> None:
        """Prefixed symbol "µg" resolves to itself (BIPM §3.2)."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("µg", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "µg"

    @pytest.mark.e2e
    def test_si_unit_compound_km_per_hour(self) -> None:
        """Compound "km/h" resolves to itself (ISO 80000-1 §6.5)."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("km/h", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "km/h"

    @pytest.mark.e2e
    def test_si_unit_compound_newton_metre(self) -> None:
        """Compound "N·m" resolves to itself via the middle-dot separator."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("N·m", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "N·m"

    @pytest.mark.e2e
    def test_si_unit_compound_kg_m_per_s2(self) -> None:
        """Compound "kg·m/s²" resolves with its superscript folded to ASCII."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("kg·m/s²", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "kg·m/s2"

    @pytest.mark.e2e
    def test_si_unit_compound_g_per_cm3(self) -> None:
        """Compound "g/cm³" resolves with its superscript folded to ASCII."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("g/cm³", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "g/cm3"

    @pytest.mark.e2e
    def test_si_unit_compound_m_per_s_minus2(self) -> None:
        """Compound "m·s⁻²" resolves with its superscript minus folded to "-"."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m·s⁻²", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "m·s-2"

    @pytest.mark.e2e
    def test_si_unit_bare_prefix_da_invalid(self) -> None:
        """Bare prefix "da" is recognized but no rule validates it — INVALID."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("da", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    @pytest.mark.e2e
    def test_si_unit_bare_prefix_k_invalid(self) -> None:
        """Bare prefix "k" is recognized but no rule validates it — INVALID."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("k", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    @pytest.mark.e2e
    def test_si_unit_unknown_compound_invalid(self) -> None:
        """Compound shape "QQQ/zzz" is recognized but the groups are unknown."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("QQQ/zzz", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    @pytest.mark.e2e
    def test_si_unit_case_mismatch_pa_missing(self) -> None:
        """D6: "pa" is not the case-exact symbol — nothing is recognized."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("pa", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_si_unit_case_mismatch_khz_missing(self) -> None:
        """R1: "KHz" (wrong case) never falls back to a prefix+Hz split."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("KHz", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_si_unit_case_mismatch_kg_missing(self) -> None:
        """D6: "Kg" (wrong case) is never partial-matched to "K"+"g"."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("Kg", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_si_unit_quantity_glued_missing(self) -> None:
        """D7: quantity-glued "25°C" is never partial-matched to "°C"."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("25°C", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_si_unit_space_separated_ambiguous(self) -> None:
        """R2: "m s" yields two candidates ("m" and "s") — AMBIGUOUS."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m s", contract)
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None

    @pytest.mark.e2e
    def test_si_unit_foreign_token_missing(self) -> None:
        """Cross-capability: "USD" is not an SI token — MISSING."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("USD", contract)
        assert result.status == Resolution.MISSING
