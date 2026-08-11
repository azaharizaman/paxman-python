"""F2 Task 3: engine-enforced ``requires_features`` feature gating.

Integration tests proving the authority-feature gate lives in the engine
(``_filter_rules``), not inside ``matches()``:

- A rule naming a contract field the contract does not have fails fast with
  ``ContractError`` before candidate collection (dangling feature names must
  never silently turn a valid input into ``INVALID``).
- A rule whose required feature is present-but-false is dropped, so a
  recognized-but-unvalidated input yields ``INVALID`` (authority gate).
- Grammar-level input-shape gates (Email obfuscated, IP IPv6) keep their
  ``MISSING`` semantics unchanged — F2 must not move them to rule gating.
"""

from __future__ import annotations

import pytest

from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.cldr_localized_ed2025 import (
    SectionLocalizedNames,
)
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.IP.capability import IPCapability
from paxman.capabilities.ISBN.capability import ISBNCapability
from paxman.core.capability import Capability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import (
    Grammar,
    Provenance,
    RecognitionMatch,
    Resolution,
    Rule,
    RuleStrategy,
)
from paxman.core.errors import ContractError
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


# ---------------------------------------------------------------------------
# Localized authority-gate fixture
# ---------------------------------------------------------------------------


class _NameRecognitionGrammar(Grammar[CountryNotation]):
    """Grammar emitting the CLDR localized key "Estados Unidos".

    Uses the real ``name_recognition`` grammar name so
    ``SectionLocalizedNames``' declared ``target_semantics`` resolves, without
    relying on the real ``NameGrammar``'s English/historical/Chinese lookup
    tables (localized recognition remediation is F3 scope, not F2).
    """

    name = "name_recognition"
    semantics = "name_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        return [
            RecognitionMatch(
                notation=CountryNotation(shape="name", value="Estados Unidos"),
                start=0,
                end=14,
                raw_text="Estados Unidos",
            )
        ]


class _LocalizedFixtureContract:
    """Minimal Contract-protocol contract with the localized authority flag.

    Exposes every ``Contract`` protocol property plus ``include_localized``,
    mirroring the real ``CountryContract`` field the rule gates on.
    """

    def __init__(self, *, include_localized: bool) -> None:
        self._include_localized = include_localized

    @property
    def capability_name(self) -> str:
        return "country"

    @property
    def active_grammars(self) -> list[str]:
        return ["name_recognition"]

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def pinned_rules(self) -> list[str] | None:
        return None

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
        return None

    @property
    def include_localized(self) -> bool:
        return self._include_localized


class _LocalizedOnlyCapability(Capability[CountryNotation]):
    """Capability exposing only the localized rule over the fixture grammar."""

    name = "country"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar[CountryNotation]]:
        return [_NameRecognitionGrammar()]

    def get_rules(self) -> list[Rule[CountryNotation]]:
        return [SectionLocalizedNames()]


# ---------------------------------------------------------------------------
# Dangling-feature fixture
# ---------------------------------------------------------------------------


class _DanglingFeatureRule(Rule[CountryNotation]):
    """Rule declaring a contract feature the fixture contract does not have."""

    name = "dangling_feature_rule"
    strategy = RuleStrategy.REGEX
    provenance = Provenance(
        authority="test",
        specification_name="test",
        kind="test",
        reference_url="https://test",
        version=None,
        lifecycle="active",
        publication_year=2024,
    )
    citation = "test"
    target_semantics = frozenset({"name_recognition"})
    requires_features = frozenset({"not_a_contract_field"})

    def matches(self, notation: CountryNotation, contract: object) -> bool:
        return True

    def normalize(self, notation: CountryNotation, contract: object) -> str:
        return "US"


class _DanglingFeatureCapability(Capability[CountryNotation]):
    """Capability exposing a rule that names a nonexistent contract feature."""

    name = "dangling_feature"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar[CountryNotation]]:
        return [_NameRecognitionGrammar()]

    def get_rules(self) -> list[Rule[CountryNotation]]:
        return [_DanglingFeatureRule()]


class _DanglingFeatureContract:
    """Minimal contract without the ``not_a_contract_field`` property."""

    @property
    def capability_name(self) -> str:
        return "dangling_feature"

    @property
    def active_grammars(self) -> list[str]:
        return ["name_recognition"]

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def pinned_rules(self) -> list[str] | None:
        return None

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
        return None


class _DanglingGrammarRule(Rule[CountryNotation]):
    """Rule whose grammar affinity points at a nonexistent grammar."""

    name = "dangling_grammar_rule"
    strategy = RuleStrategy.REGEX
    provenance = Provenance(
        authority="test",
        specification_name="test",
        kind="test",
        reference_url="https://test",
        version=None,
        lifecycle="active",
        publication_year=2024,
    )
    citation = "test"
    target_semantics = frozenset({"missing_grammar"})
    requires_features = frozenset()

    def matches(self, notation: CountryNotation, contract: object) -> bool:
        return True

    def normalize(self, notation: CountryNotation, contract: object) -> str:
        return "US"


class _DanglingGrammarCapability(Capability[CountryNotation]):
    """Capability exposing a rule with a dangling grammar affinity."""

    name = "dangling_grammar"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar[CountryNotation]]:
        return [_NameRecognitionGrammar()]

    def get_rules(self) -> list[Rule[CountryNotation]]:
        return [_DanglingGrammarRule()]


class _ExcludedDanglingGrammarContract(_LocalizedFixtureContract):
    """Contract that excludes the malformed rule from normal execution."""

    @property
    def capability_name(self) -> str:
        return "dangling_grammar"

    @property
    def excluded_rules(self) -> list[str]:
        return ["dangling_grammar_rule"]


# ---------------------------------------------------------------------------
# Existing test cases
# ---------------------------------------------------------------------------


class TestDanglingGrammarValidation:
    """Affinity validation must precede rule filtering."""

    @pytest.mark.integration
    def test_excluded_rule_with_unknown_grammar_still_fails_fast(self) -> None:
        register_capability(_DanglingGrammarCapability())
        contract = _ExcludedDanglingGrammarContract(include_localized=False)

        with pytest.raises(
            ContractError,
            match=r"dangling_grammar_rule.*missing_grammar",
        ):
            run_capability("Estados Unidos", contract)


class TestDanglingFeatureValidation:
    """A rule naming a contract field the contract lacks fails fast."""

    @pytest.mark.integration
    def test_dangling_feature_raises_contract_error_before_candidates(self) -> None:
        register_capability(_DanglingFeatureCapability())
        contract = _DanglingFeatureContract()

        with pytest.raises(
            ContractError,
            match=r"dangling_feature_rule.*not_a_contract_field",
        ):
            run_capability("Estados Unidos", contract)


class TestLocalizedAuthorityGate:
    """Authority-feature gating is engine-enforced via ``requires_features``."""

    @pytest.mark.integration
    def test_localized_disabled_yields_invalid(self) -> None:
        register_capability(_LocalizedOnlyCapability())
        contract = _LocalizedFixtureContract(include_localized=False)
        result = run_capability("Estados Unidos", contract)

        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_localized_enabled_yields_success(self) -> None:
        register_capability(_LocalizedOnlyCapability())
        contract = _LocalizedFixtureContract(include_localized=True)
        result = run_capability("Estados Unidos", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"


class TestRealCapabilityGates:
    """Real capabilities: grammar gates keep MISSING, authority gate keeps INVALID."""

    @pytest.mark.integration
    def test_country_pinned_disabled_historical_yields_invalid(self) -> None:
        """A pinned gated rule with a false feature yields INVALID, not SUCCESS.

        Feature filtering applies after pinning: the pinned historical rule is
        dropped, so the recognized "Burma" name has no validating rule.
        """
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract(
            pinned_rules=("Section-historical-names",),
            include_historical=False,
        )
        result = run_capability("Burma", contract)

        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    @pytest.mark.integration
    def test_email_obfuscated_disabled_yields_missing(self) -> None:
        """Input-shape gate: obfuscated grammar off means nothing is recognized."""
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(include_obfuscated=False)
        result = run_capability("user at example dot com", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_email_obfuscated_enabled_yields_success(self) -> None:
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(include_obfuscated=True)
        result = run_capability("user at example dot com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.integration
    def test_ip_ipv6_disabled_yields_missing(self) -> None:
        """Input-shape gate: IPv6 grammar off means nothing is recognized."""
        register_capability(IPCapability())
        contract = IPCapability.create_contract(include_ipv6=False)
        result = run_capability("2001:db8::1", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_ip_ipv6_enabled_yields_success(self) -> None:
        register_capability(IPCapability())
        contract = IPCapability.create_contract(include_ipv6=True)
        result = run_capability("2001:db8::1", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2001:db8::1"


class TestISBNFeatureGates:
    """Real ISBN gates: range authority keeps INVALID, ISBN-10 grammar keeps MISSING."""

    @pytest.mark.integration
    def test_isbn_range_pinned_disabled_yields_invalid(self) -> None:
        """Feature filtering applies after pinning: the pinned range rule is
        dropped, so no authority validates. Same mechanism as Country
        historical."""
        register_capability(ISBNCapability())
        contract = ISBNCapability.create_contract(
            pinned_rules=("Section 4-registrant-range",),
            include_range_validation=False,
        )
        result = run_capability("9780110002224", contract)

        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    @pytest.mark.integration
    def test_isbn_range_pinned_enabled_yields_success(self) -> None:
        register_capability(ISBNCapability())
        contract = ISBNCapability.create_contract(
            pinned_rules=("Section 4-registrant-range",),
            include_range_validation=True,
        )
        result = run_capability("9780110002224", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "9780110002224"

    @pytest.mark.integration
    def test_isbn10_disabled_yields_missing(self) -> None:
        """Grammar-level gate: only isbn13_recognition active, so nothing is
        recognized."""
        register_capability(ISBNCapability())
        contract = ISBNCapability.create_contract(include_isbn10=False)
        result = run_capability("0306406152", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_isbn10_enabled_yields_success(self) -> None:
        register_capability(ISBNCapability())
        contract = ISBNCapability.create_contract()
        result = run_capability("0306406152", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "9780306406157"
