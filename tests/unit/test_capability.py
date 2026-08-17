"""Tests for Capability base class."""

from __future__ import annotations

import pytest

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.domain import Grammar, Provenance, Rule, RuleStrategy

# --- Concrete test doubles ---


class StubGrammar(Grammar):
    """Minimal concrete grammar for testing Capability."""

    name: str = "stub_grammar"
    semantics = "stub_grammar"

    def recognize(self, text: str) -> list[list[str]]:
        return []


class StubRule(Rule):
    """Minimal concrete rule for testing Capability."""

    name: str = "stub_rule"
    strategy: RuleStrategy = RuleStrategy.REGEX
    provenance: Provenance = Provenance(
        authority="test",
        specification_name="test",
        kind="test",
        reference_url="https://test",
        version=None,
        lifecycle="active",
        publication_year=2024,
    )
    citation: str = "test citation"
    target_semantics = frozenset({"stub_grammar"})
    requires_features = frozenset()

    def matches(self, notation: list[str], contract: Contract) -> bool:
        return True

    def normalize(self, notation: list[str], contract: Contract) -> str:
        return "stub"


class ConcreteCapability(Capability):
    """Concrete capability that fully implements the ABC."""

    name = "test_cap"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar]:
        return [StubGrammar()]

    def get_rules(self) -> list[Rule]:
        return [StubRule()]


# --- Capability ABC tests ---


class TestCapabilityABC:
    @pytest.mark.unit
    def test_cannot_instantiate_abc_directly(self) -> None:
        """Capability is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Capability()  # type: ignore[abstract]

    @pytest.mark.unit
    def test_cannot_instantiate_without_abstract_methods(self) -> None:
        """A subclass missing abstract methods cannot be instantiated."""

        class IncompleteCapability(Capability):
            name = "incomplete"
            version = "0.1.0"
            # Missing get_grammars and get_rules

        with pytest.raises(TypeError):
            IncompleteCapability()  # type: ignore[abstract]

    @pytest.mark.unit
    def test_cannot_instantiate_missing_get_grammars(self) -> None:
        """Missing only get_grammars still prevents instantiation."""

        class PartialCapability(Capability):
            name = "partial"
            version = "0.1.0"

            def get_rules(self) -> list[Rule]:
                return []

        with pytest.raises(TypeError):
            PartialCapability()  # type: ignore[abstract]

    @pytest.mark.unit
    def test_cannot_instantiate_missing_get_rules(self) -> None:
        """Missing only get_rules still prevents instantiation."""

        class PartialCapability(Capability):
            name = "partial"
            version = "0.1.0"

            def get_grammars(self) -> list[Grammar]:
                return []

        with pytest.raises(TypeError):
            PartialCapability()  # type: ignore[abstract]

    @pytest.mark.unit
    def test_concrete_subclass_instantiates(self) -> None:
        """A fully implemented subclass can be instantiated."""
        cap = ConcreteCapability()
        assert cap.name == "test_cap"
        assert cap.version == "0.1.0"

    @pytest.mark.unit
    def test_get_grammars_returns_list(self) -> None:
        cap = ConcreteCapability()
        grammars = cap.get_grammars()
        assert isinstance(grammars, list)
        assert len(grammars) == 1
        assert isinstance(grammars[0], Grammar)

    @pytest.mark.unit
    def test_get_rules_returns_list(self) -> None:
        cap = ConcreteCapability()
        rules = cap.get_rules()
        assert isinstance(rules, list)
        assert len(rules) == 1
        assert isinstance(rules[0], Rule)

    @pytest.mark.unit
    def test_capability_is_not_hashable_by_default(self) -> None:
        """Capability instances do not have __eq__/__hash__ by default."""
        cap = ConcreteCapability()
        # ABC doesn't define __eq__, so identity-based equality works
        assert cap == cap
        assert cap != ConcreteCapability()
