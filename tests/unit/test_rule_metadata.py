"""Tests for Rule metadata enforcement at class-definition time."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

import pytest

import paxman.capabilities
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

_RULE_METADATA_ATTRS = (
    "name",
    "strategy",
    "provenance",
    "citation",
    "target_grammars",
    "requires_features",
)

_TEST_PROVENANCE = Provenance(
    authority="test",
    specification_name="test",
    kind="test",
    reference_url="https://test",
    version=None,
    lifecycle="active",
    publication_year=2024,
)


def _concrete_rule_classes() -> list[type[Rule[Any]]]:
    """Collect every concrete Rule subclass under paxman.capabilities."""
    classes: list[type[Rule[Any]]] = []
    for capability in pkgutil.iter_modules(paxman.capabilities.__path__):
        rules_package = importlib.import_module(
            f"{paxman.capabilities.__name__}.{capability.name}.rules"
        )
        for module in pkgutil.iter_modules(rules_package.__path__):
            rule_module = importlib.import_module(
                f"{rules_package.__name__}.{module.name}"
            )
            for obj in vars(rule_module).values():
                if isinstance(obj, type) and issubclass(obj, Rule) and obj is not Rule:
                    classes.append(obj)
    return classes


class TestRuleMetadataEnforcement:
    @pytest.mark.unit
    def test_all_concrete_rule_classes_define_metadata(self) -> None:
        """Every concrete Rule subclass in paxman.capabilities defines metadata.

        The lower bound guards against accidental rule regressions; the
        precise count is intentionally not pinned so that adding a new rule
        (the documented contributor workflow) does not break this guard.
        """
        rule_classes = _concrete_rule_classes()
        assert len(rule_classes) >= 18
        for rule_cls in rule_classes:
            for attr in _RULE_METADATA_ATTRS:
                assert hasattr(rule_cls, attr), f"{rule_cls.__name__} missing {attr}"

    @pytest.mark.unit
    def test_bare_rule_subclass_raises_type_error(self) -> None:
        """A Rule subclass missing all metadata fails at class-definition time."""

        with pytest.raises(TypeError, match="must define Rule metadata"):

            class _BareRule(Rule[str]):
                def matches(self, notation: str, contract: Contract) -> bool:
                    return True

                def normalize(self, notation: str, contract: Contract) -> str:
                    return ""

    @pytest.mark.unit
    @pytest.mark.parametrize("missing", _RULE_METADATA_ATTRS)
    def test_missing_single_metadata_attribute_raises(self, missing: str) -> None:
        """A Rule subclass missing one metadata attr fails at class-definition time."""

        with pytest.raises(TypeError, match=missing):

            class _IncompleteRule(Rule[str]):
                if missing != "name":
                    name = "test_rule"
                if missing != "strategy":
                    strategy = RuleStrategy.REGEX
                if missing != "provenance":
                    provenance = _TEST_PROVENANCE
                if missing != "citation":
                    citation = "test citation"
                if missing != "target_grammars":
                    target_grammars = frozenset({"test_grammar"})
                if missing != "requires_features":
                    requires_features = frozenset()

                def matches(self, notation: str, contract: Contract) -> bool:
                    return True

                def normalize(self, notation: str, contract: Contract) -> str:
                    return ""

    @pytest.mark.unit
    def test_empty_target_grammars_raises(self) -> None:
        """An empty target_grammars frozenset is valid type-wise but a bug:
        the rule would match nothing. The runtime guard must reject it."""
        with pytest.raises(TypeError, match="non-empty"):

            class _EmptyTargetGrammars(Rule[str]):
                name = "test_rule"
                strategy = RuleStrategy.REGEX
                provenance = _TEST_PROVENANCE
                citation = "test citation"
                target_grammars = frozenset()
                requires_features = frozenset()

                def matches(self, notation: str, contract: Contract) -> bool:
                    return True

                def normalize(self, notation: str, contract: Contract) -> str:
                    return ""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("attribute", "value"),
        [
            ("target_grammars", "test_grammar"),
            ("target_grammars", ["test_grammar"]),
            ("requires_features", frozenset({1})),
        ],
    )
    def test_affinity_metadata_requires_frozenset_of_strings(
        self, attribute: str, value: Any
    ) -> None:
        """Malformed affinity metadata fails during Rule subclass creation."""
        namespace: dict[str, Any] = {
            "name": "test_rule",
            "strategy": RuleStrategy.REGEX,
            "provenance": _TEST_PROVENANCE,
            "citation": "test citation",
            "target_grammars": frozenset({"test_grammar"}),
            "requires_features": frozenset(),
            "matches": lambda self, notation, contract: True,
            "normalize": lambda self, notation, contract: "",
        }
        namespace[attribute] = value

        with pytest.raises(TypeError, match=rf"{attribute} must be frozenset\[str\]"):
            type("_InvalidAffinityMetadata", (Rule,), namespace)
