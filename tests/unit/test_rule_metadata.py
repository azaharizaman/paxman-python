"""Tests for Rule metadata enforcement at class-definition time."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

import pytest

import paxman.capabilities
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

_RULE_METADATA_ATTRS = ("name", "strategy", "provenance", "citation")

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
        """Every concrete Rule subclass in paxman.capabilities defines metadata."""
        rule_classes = _concrete_rule_classes()
        assert len(rule_classes) == 18
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

                def matches(self, notation: str, contract: Contract) -> bool:
                    return True

                def normalize(self, notation: str, contract: Contract) -> str:
                    return ""
