"""Tests for EmailNotation and EmailCapability."""

from __future__ import annotations

import pytest

from paxman.capabilities.Email.capability import EmailCapability, EmailNotation
from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


# --- EmailNotation tests ---


class TestEmailNotation:
    @pytest.mark.capability
    def test_creates_with_local_and_domain(self) -> None:
        """EmailNotation stores local_part and domain_part."""
        notation = EmailNotation(local_part="user", domain_part="example.com")
        assert notation.local_part == "user"
        assert notation.domain_part == "example.com"

    @pytest.mark.capability
    def test_is_frozen(self) -> None:
        """EmailNotation is immutable (frozen dataclass)."""
        notation = EmailNotation(local_part="user", domain_part="example.com")
        with pytest.raises(AttributeError):
            notation.local_part = "other"  # type: ignore[misc]

    @pytest.mark.capability
    def test_as_list_returns_two_element_list(self) -> None:
        """as_list() bridges to generic list[str] interface."""
        notation = EmailNotation(local_part="user", domain_part="example.com")
        result = notation.as_list()
        assert result == ["user", "example.com"]
        assert isinstance(result, list)

    @pytest.mark.capability
    def test_as_list_preserves_order(self) -> None:
        """as_list() returns [local_part, domain_part] in order."""
        notation = EmailNotation(local_part="azahari", domain_part="gmail.com")
        assert notation.as_list()[0] == "azahari"
        assert notation.as_list()[1] == "gmail.com"

    @pytest.mark.capability
    def test_equality(self) -> None:
        """Two notations with same fields are equal."""
        n1 = EmailNotation(local_part="user", domain_part="example.com")
        n2 = EmailNotation(local_part="user", domain_part="example.com")
        assert n1 == n2

    @pytest.mark.capability
    def test_inequality(self) -> None:
        """Two notations with different fields are not equal."""
        n1 = EmailNotation(local_part="user", domain_part="example.com")
        n2 = EmailNotation(local_part="user", domain_part="other.com")
        assert n1 != n2

    @pytest.mark.capability
    def test_hashable(self) -> None:
        """EmailNotation can be used in sets and as dict keys."""
        n1 = EmailNotation(local_part="user", domain_part="example.com")
        n2 = EmailNotation(local_part="user", domain_part="example.com")
        s = {n1, n2}
        assert len(s) == 1


# --- EmailCapability tests ---


class TestEmailCapability:
    @pytest.mark.capability
    def test_is_capability_subclass(self) -> None:
        """EmailCapability is a concrete Capability."""
        cap = EmailCapability()
        assert isinstance(cap, Capability)

    @pytest.mark.capability
    def test_name(self) -> None:
        """Capability name is 'email'."""
        assert EmailCapability().name == "email"

    @pytest.mark.capability
    def test_version(self) -> None:
        """Capability version is '1.0.0'."""
        assert EmailCapability().version == "1.0.0"

    @pytest.mark.capability
    def test_get_grammars_returns_standard_email_grammar(self) -> None:
        """get_grammars() returns StandardEmailGrammar."""
        cap = EmailCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 1
        assert isinstance(grammars[0], StandardEmailGrammar)
        assert isinstance(grammars[0], Grammar)

    @pytest.mark.capability
    def test_get_rules_returns_section341_addr_spec(self) -> None:
        """get_rules() returns Section341AddrSpec."""
        cap = EmailCapability()
        rules = cap.get_rules()
        assert len(rules) == 1
        assert isinstance(rules[0], Section341AddrSpec)
        assert isinstance(rules[0], Rule)

    @pytest.mark.capability
    def test_grammar_name(self) -> None:
        """Stub grammar has expected name."""
        grammar = StandardEmailGrammar()
        assert grammar.name == "standard_recognition"

    @pytest.mark.capability
    def test_rule_name(self) -> None:
        """Stub rule has expected name."""
        rule = Section341AddrSpec()
        assert rule.name == "Section 3.4.1-addr-spec"

    @pytest.mark.capability
    def test_rule_citation(self) -> None:
        """Stub rule has expected citation."""
        rule = Section341AddrSpec()
        assert rule.citation == "Section 3.4.1 (addr-spec)"


# --- Package import tests ---


class TestEmailPackageImports:
    @pytest.mark.capability
    def test_package_exports_email_capability(self) -> None:
        """Email package exports EmailCapability."""
        from paxman.capabilities.Email import EmailCapability as EC

        assert EC is EmailCapability

    @pytest.mark.capability
    def test_package_exports_email_notation(self) -> None:
        """Email package exports EmailNotation."""
        from paxman.capabilities.Email import EmailNotation as EN

        assert EN is EmailNotation
