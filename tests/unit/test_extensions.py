"""Tests for the community grammar/rule extension registries."""

from __future__ import annotations

from typing import Any

import pytest

from paxman.core.domain import (
    Grammar,
    Provenance,
    RecognitionMatch,
    Rule,
    RuleStrategy,
)
from paxman.core.errors import CapabilityError
from paxman.core.extensions import (
    _grammar_registry,
    _rule_registry,
    freeze_extensions,
    get_extended_grammars,
    get_extended_rules,
    register_grammar,
    register_rule,
    reset_extensions,
)

# --- Concrete test doubles ---


_PROVENANCE = Provenance(
    authority="community",
    specification_name="test double",
    kind="test",
    reference_url="https://example.com/test",
    version=None,
    lifecycle="active",
    publication_year=2026,
)


class _DotDateGrammar(Grammar[Any]):
    """Minimal community grammar test double."""

    name = "dot_date_recognition"
    semantics = "dot_date_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[Any]]:
        return []


class _SecondGrammar(Grammar[Any]):
    """Second grammar — tests registration order."""

    name = "second_recognition"
    semantics = "second_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[Any]]:
        return []


class _NamelessGrammar(Grammar[Any]):
    """Grammar with an empty name — tests name validation."""

    name = ""
    semantics = "nameless_grammar"

    def recognize(self, text: str) -> list[RecognitionMatch[Any]]:
        return []


class _MixedCaseGrammar(Grammar[Any]):
    """Grammar with a mixed-case name — tests lowercase enforcement."""

    name = "DotDateRecognition"
    semantics = "DotDateRecognition"

    def recognize(self, text: str) -> list[RecognitionMatch[Any]]:
        return []


class _DotDateRule(Rule[Any]):
    """Minimal community rule test double."""

    name = "dot_date_rule"
    strategy = RuleStrategy.PARSER
    provenance = _PROVENANCE
    citation = "community test double"
    target_semantics = frozenset({"dot_date_recognition"})
    requires_features = frozenset()

    def matches(self, notation: Any, contract: Any) -> bool:
        return True

    def normalize(self, notation: Any, contract: Any) -> str:
        return ""


class _NamelessRule(Rule[Any]):
    """Rule with an empty name — tests name validation."""

    name = ""
    strategy = RuleStrategy.PARSER
    provenance = _PROVENANCE
    citation = "community test double"
    target_semantics = frozenset({"x"})
    requires_features = frozenset()

    def matches(self, notation: Any, contract: Any) -> bool:
        return True

    def normalize(self, notation: Any, contract: Any) -> str:
        return ""


# --- Tests ---


@pytest.fixture(autouse=True)
def _clean_extensions() -> None:
    """Reset extension registries before every test to avoid cross-test pollution."""
    reset_extensions()
    yield
    reset_extensions()


class TestRegisterGrammar:
    @pytest.mark.unit
    def test_register_and_get(self) -> None:
        register_grammar("date", _DotDateGrammar)
        instances = get_extended_grammars("date")
        assert len(instances) == 1
        assert isinstance(instances[0], _DotDateGrammar)
        assert instances[0].name == "dot_date_recognition"

    @pytest.mark.unit
    def test_get_empty_for_unknown_capability(self) -> None:
        assert get_extended_grammars("nope") == []
        assert get_extended_rules("nope") == []

    @pytest.mark.unit
    def test_duplicate_registration_raises(self) -> None:
        register_grammar("date", _DotDateGrammar)
        with pytest.raises(CapabilityError):
            register_grammar("date", _DotDateGrammar)

    @pytest.mark.unit
    @pytest.mark.parametrize("bad", [object, _DotDateGrammar()])
    def test_non_grammar_subclass_raises(self, bad: Any) -> None:
        with pytest.raises(CapabilityError):
            register_grammar("date", bad)

    @pytest.mark.unit
    def test_empty_name_raises(self) -> None:
        with pytest.raises(CapabilityError):
            register_grammar("date", _NamelessGrammar)

    @pytest.mark.unit
    def test_mixed_case_name_raises(self) -> None:
        with pytest.raises(CapabilityError):
            register_grammar("date", _MixedCaseGrammar)

    @pytest.mark.unit
    def test_frozen_registration_raises(self) -> None:
        freeze_extensions()
        with pytest.raises(CapabilityError):
            register_grammar("date", _DotDateGrammar)

    @pytest.mark.unit
    def test_same_name_allowed_across_capabilities(self) -> None:
        register_grammar("date", _DotDateGrammar)
        register_grammar("email", _DotDateGrammar)
        assert [g.name for g in get_extended_grammars("date")] == [
            "dot_date_recognition"
        ]
        assert [g.name for g in get_extended_grammars("email")] == [
            "dot_date_recognition"
        ]

    @pytest.mark.unit
    def test_registration_order_preserved(self) -> None:
        register_grammar("date", _DotDateGrammar)
        register_grammar("date", _SecondGrammar)
        names = [g.name for g in get_extended_grammars("date")]
        assert names == ["dot_date_recognition", "second_recognition"]

    @pytest.mark.unit
    def test_getters_return_fresh_instances(self) -> None:
        register_grammar("date", _DotDateGrammar)
        first = get_extended_grammars("date")[0]
        second = get_extended_grammars("date")[0]
        assert first is not second
        assert first.name == second.name == "dot_date_recognition"


class TestRegisterRule:
    @pytest.mark.unit
    def test_register_and_get(self) -> None:
        register_rule("date", _DotDateRule)
        instances = get_extended_rules("date")
        assert len(instances) == 1
        assert isinstance(instances[0], _DotDateRule)
        assert instances[0].name == "dot_date_rule"

    @pytest.mark.unit
    def test_duplicate_registration_raises(self) -> None:
        register_rule("date", _DotDateRule)
        with pytest.raises(CapabilityError):
            register_rule("date", _DotDateRule)

    @pytest.mark.unit
    def test_non_rule_subclass_raises(self) -> None:
        with pytest.raises(CapabilityError):
            register_rule("date", object)

    @pytest.mark.unit
    def test_empty_name_raises(self) -> None:
        with pytest.raises(CapabilityError):
            register_rule("date", _NamelessRule)

    @pytest.mark.unit
    def test_frozen_registration_raises(self) -> None:
        freeze_extensions()
        with pytest.raises(CapabilityError):
            register_rule("date", _DotDateRule)

    @pytest.mark.unit
    def test_getters_return_fresh_instances(self) -> None:
        register_rule("date", _DotDateRule)
        first = get_extended_rules("date")[0]
        second = get_extended_rules("date")[0]
        assert first is not second
        assert first.name == second.name == "dot_date_rule"


class TestRegistryInternals:
    @pytest.mark.unit
    def test_registration_populates_internal_registries(self) -> None:
        register_grammar("date", _DotDateGrammar)
        register_rule("date", _DotDateRule)
        assert list(_grammar_registry) == ["date"]
        assert list(_rule_registry) == ["date"]

    @pytest.mark.unit
    def test_reset_clears_registries_and_unfreezes(self) -> None:
        register_grammar("date", _DotDateGrammar)
        freeze_extensions()
        reset_extensions()
        assert _grammar_registry == {}
        assert _rule_registry == {}
        # Registries are unfrozen again: registration succeeds.
        register_grammar("date", _DotDateGrammar)
        assert len(get_extended_grammars("date")) == 1
