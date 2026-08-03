"""Integration tests for the engine orchestrator pipeline."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.capability import Capability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Grammar, Provenance, Resolution, Rule, RuleStrategy
from paxman.core.errors import ContractError, RecognitionError, ValidationError
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestRunCapability:
    @pytest.mark.integration
    def test_standard_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("Contact user@example.com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"
        assert len(result.candidates) >= 1

    @pytest.mark.integration
    def test_obfuscated_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(include_obfuscated=True)
        result = run_capability("Email user at example dot com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.integration
    def test_localhost_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.integration
    def test_missing_input(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("no email here", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_version_stamp_present(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("user@example.com", contract)

        assert result.version_stamp is not None
        assert isinstance(result.version_stamp.paxman_version, str)
        assert len(result.version_stamp.replay_hash) == 64  # SHA-256 hex

    @pytest.mark.integration
    def test_replay_determinism(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        r1 = run_capability("user@example.com", contract)
        r2 = run_capability("user@example.com", contract)

        assert r1.version_stamp.replay_hash == r2.version_stamp.replay_hash
        assert r1.canonicalized_value == r2.canonicalized_value


# ---------------------------------------------------------------------------
# Error-wrapping stubs
# ---------------------------------------------------------------------------


class CrashGrammar(Grammar[EmailNotation]):
    """Grammar whose recognize() always raises."""

    name = "crash_grammar"

    def recognize(self, text: str) -> list[EmailNotation]:
        raise RuntimeError("grammar crashed")


class SimpleGrammar(Grammar[EmailNotation]):
    """Grammar that returns a fixed notation."""

    name = "simple_grammar"

    def recognize(self, text: str) -> list[EmailNotation]:
        return [EmailNotation(local_part="user", domain_part="example.com")]


class StubRule(Rule[EmailNotation]):
    """Rule that always matches."""

    name = "stub_rule"
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
    target_grammars = frozenset({"crash_grammar"})
    requires_features = frozenset()

    def matches(self, notation: EmailNotation, contract: object) -> bool:
        return True

    def normalize(self, notation: EmailNotation, contract: object) -> str:
        return "stub"


class ExplodingRule(Rule[EmailNotation]):
    """Rule whose matches() always raises."""

    name = "exploding_rule"
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
    target_grammars = frozenset({"simple_grammar"})
    requires_features = frozenset()

    def matches(self, notation: EmailNotation, contract: object) -> bool:
        raise ValueError("rule crashed")

    def normalize(self, notation: EmailNotation, contract: object) -> str:
        return "stub"


class CrashCapability(Capability):
    """Capability with a crashing grammar."""

    name = "crash"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar[EmailNotation]]:
        return [CrashGrammar()]

    def get_rules(self) -> list[Rule[EmailNotation]]:
        return [StubRule()]


class ExplodingRuleCapability(Capability):
    """Capability with a working grammar but crashing rule."""

    name = "exploding_rule_cap"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar[EmailNotation]]:
        return [SimpleGrammar()]

    def get_rules(self) -> list[Rule[EmailNotation]]:
        return [ExplodingRule()]


class _ErrorContract:
    """Minimal contract stub for error-wrapping tests."""

    @property
    def capability_name(self) -> str:
        return "crash"

    @property
    def active_grammars(self) -> list[str]:
        return ["crash_grammar"]

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

    def as_dict(self) -> dict[str, object]:
        return {"capability_name": "crash"}


class _ExplodingContract(_ErrorContract):
    """Contract variant for ExplodingRuleCapability."""

    @property
    def capability_name(self) -> str:
        return "exploding_rule_cap"

    @property
    def active_grammars(self) -> list[str]:
        return ["simple_grammar"]

    def as_dict(self) -> dict[str, object]:
        return {"capability_name": "exploding_rule_cap"}


class TestErrorWrapping:
    """Verify orchestrator wraps grammar/rule exceptions correctly."""

    @pytest.mark.integration
    def test_recognition_error_wrapped(self) -> None:
        register_capability(CrashCapability())
        contract = _ErrorContract()
        with pytest.raises(RecognitionError):
            run_capability("test input", contract)

    @pytest.mark.integration
    def test_validation_error_wrapped(self) -> None:
        register_capability(ExplodingRuleCapability())
        contract = _ExplodingContract()
        with pytest.raises(ValidationError):
            run_capability("test input", contract)


class TestPinnedRules:
    """Verify pinned_rules filtering behavior."""

    @pytest.mark.integration
    def test_pinned_rules_excludes_unpinned(self) -> None:
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(
            pinned_rules=("Section 3.4.1-addr-spec",)
        )
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.INVALID
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_pinned_rules_only_runs_pinned(self) -> None:
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(
            pinned_rules=("Section 6.3-localhost",)
        )
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"
        assert len(result.candidates) == 1
        assert result.candidates[0].validation_rule == "Section 6.3-localhost"

    @pytest.mark.integration
    def test_pinned_rules_overrides_excluded_rules(self) -> None:
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(
            excluded_rules=["Section 6.3-localhost"],
            pinned_rules=("Section 6.3-localhost",),
        )
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.integration
    def test_pinned_rules_with_year_filter(self) -> None:
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(
            pinned_rules=("Section 3.4.1-addr-spec", "Section 6.3-localhost"),
            year=2010,
        )
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.INVALID
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_pinned_rules_none_uses_excluded_rules(self) -> None:
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(
            excluded_rules=["Section 6.3-localhost"]
        )
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_pinned_rules_empty_tuple_excludes_all(self) -> None:
        register_capability(EmailCapability())
        contract = EmailCapability.create_contract(pinned_rules=())
        result = run_capability("user@example.com", contract)

        assert result.status == Resolution.INVALID
        assert len(result.candidates) == 0


class _PhantomGrammar(Grammar[EmailNotation]):
    """Grammar referenced by a rule that does not exist in the capability."""

    name = "phantom_grammar"

    def recognize(self, text: str) -> list[EmailNotation]:
        return [EmailNotation(local_part="user", domain_part="example.com")]


class _PhantomRule(Rule[EmailNotation]):
    """Rule whose target_grammars names a non-existent grammar."""

    name = "phantom_rule"
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
    target_grammars = frozenset({"does_not_exist"})
    requires_features = frozenset()

    def matches(self, notation: EmailNotation, contract: object) -> bool:
        return True

    def normalize(self, notation: EmailNotation, contract: object) -> str:
        return "phantom"


class _PhantomCapability(Capability):
    """Capability whose rule declares a grammar the capability lacks."""

    name = "phantom"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar[EmailNotation]]:
        return [_PhantomGrammar()]

    def get_rules(self) -> list[Rule[EmailNotation]]:
        return [_PhantomRule()]


class _PhantomContract:
    """Minimal contract stub for the phantom capability."""

    @property
    def capability_name(self) -> str:
        return "phantom"

    @property
    def active_grammars(self) -> list[str]:
        return ["phantom_grammar"]

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

    def as_dict(self) -> dict[str, object]:
        return {"capability_name": "phantom"}


class TestGrammarRuleAffinity:
    """F1: grammar→rule affinity declared via Rule.target_grammars."""

    @pytest.mark.integration
    @pytest.mark.parametrize("output_format", [None, "ISO", "US"])
    def test_date_ambiguity_preserved_under_output_format(
        self, output_format: str | None
    ) -> None:
        """01/02/2026 is recognized by both US and EU grammars; both rules
        validate both notations, yielding two distinct canonical values.

        The result is AMBIGUOUS regardless of output_format: formatting is a
        post-status presentation transform and can neither create nor resolve
        ambiguity (see HOW_TO_ADD_NEW_CAPABILITY.md presentational-only invariant).
        """
        register_capability(DateCapability())
        contract = DateCapability.create_contract(output_format=output_format)
        result = run_capability("01/02/2026", contract)

        # Ambiguity is locked from the canonical candidate values before any
        # output_format formatting, so it must hold for every output_format.
        assert result.status == Resolution.AMBIGUOUS
        assert len(result.candidates) == 4
        # Two genuinely distinct canonical values -> AMBIGUOUS (not SUCCESS).
        assert len({c.value for c in result.candidates}) == 2

    @pytest.mark.integration
    def test_date_same_interpretation_is_success(self) -> None:
        """When both slash interpretations agree, F1 must not invent ambiguity."""
        register_capability(DateCapability())
        contract = DateCapability.create_contract()
        result = run_capability("12/12/2026", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-12-12"

    @pytest.mark.integration
    def test_date_ambiguity_value_set_independent_of_output_format(self) -> None:
        """The candidate value set (and thus the status) must not change when the
        caller requests a different output_format — formatting is a post-status
        presentation transform (HOW_TO presentational-only invariant)."""
        register_capability(DateCapability())
        base = run_capability("01/02/2026", DateCapability.create_contract())
        us = run_capability(
            "01/02/2026", DateCapability.create_contract(output_format="US")
        )

        assert base.status == us.status == Resolution.AMBIGUOUS
        # output_format reformats the canonical value (a per-format bijection),
        # so the literal strings differ between ISO and US — but the NUMBER of
        # distinct canonical values (and therefore the ambiguity) is invariant.
        # That is the presentational-only guarantee: status is decided before
        # formatting and cannot be created or resolved by output_format.
        assert len({c.value for c in base.candidates}) == 2
        assert len({c.value for c in us.candidates}) == 2

    @pytest.mark.integration
    def test_affinity_validation_rejects_unknown_grammar(self) -> None:
        """A rule declaring a grammar the capability lacks must fail fast with
        ContractError, not silently drop the rule (which would yield INVALID)."""
        register_capability(_PhantomCapability())
        with pytest.raises(ContractError):
            run_capability("test input", _PhantomContract())
