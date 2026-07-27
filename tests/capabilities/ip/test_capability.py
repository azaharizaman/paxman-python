"""Tests for IPNotation and IPCapability."""

from __future__ import annotations

import pytest

from paxman.capabilities.IP.capability import IPCapability, IPNotation
from paxman.capabilities.IP.contract import IPContract
from paxman.capabilities.IP.grammar.ipv4_recognition import IPv4Grammar
from paxman.capabilities.IP.rules.rfc_791_ed1981 import Section3Dot2IPv4Address
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule

# --- IPNotation tests ---


class TestIPNotation:
    @pytest.mark.capability
    def test_creates_with_address(self) -> None:
        """IPNotation stores address."""
        notation = IPNotation(address="192.168.1.1")
        assert notation.address == "192.168.1.1"

    @pytest.mark.capability
    def test_is_frozen(self) -> None:
        """IPNotation is immutable (frozen dataclass)."""
        notation = IPNotation(address="192.168.1.1")
        with pytest.raises(AttributeError):
            notation.address = "10.0.0.1"  # type: ignore[misc]

    @pytest.mark.capability
    def test_as_list_returns_single_element(self) -> None:
        """as_list() bridges to generic list[str] interface."""
        notation = IPNotation(address="192.168.1.1")
        result = notation.as_list()
        assert result == ["192.168.1.1"]
        assert isinstance(result, list)

    @pytest.mark.capability
    def test_equality(self) -> None:
        """Two notations with same address are equal."""
        n1 = IPNotation(address="192.168.1.1")
        n2 = IPNotation(address="192.168.1.1")
        assert n1 == n2

    @pytest.mark.capability
    def test_inequality(self) -> None:
        """Two notations with different addresses are not equal."""
        n1 = IPNotation(address="192.168.1.1")
        n2 = IPNotation(address="10.0.0.1")
        assert n1 != n2

    @pytest.mark.capability
    def test_hashable(self) -> None:
        """IPNotation can be used in sets and as dict keys."""
        n1 = IPNotation(address="192.168.1.1")
        n2 = IPNotation(address="192.168.1.1")
        s = {n1, n2}
        assert len(s) == 1


# --- IPCapability tests ---


class TestIPCapability:
    @pytest.mark.capability
    def test_is_capability_subclass(self) -> None:
        """IPCapability is a concrete Capability."""
        cap = IPCapability()
        assert isinstance(cap, Capability)

    @pytest.mark.capability
    def test_name(self) -> None:
        """Capability name is 'ip'."""
        assert IPCapability().name == "ip"

    @pytest.mark.capability
    def test_version(self) -> None:
        """Capability version is '1.0.0'."""
        assert IPCapability().version == "1.0.0"

    @pytest.mark.capability
    def test_get_grammars_returns_all_ip_grammars(self) -> None:
        """get_grammars() returns both IPv4 and IPv6 grammars."""
        cap = IPCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 2
        assert isinstance(grammars[0], IPv4Grammar)
        assert isinstance(grammars[0], Grammar)

    @pytest.mark.capability
    def test_get_rules_returns_all_ip_rules(self) -> None:
        """get_rules() returns both IP validation rules."""
        cap = IPCapability()
        rules = cap.get_rules()
        assert len(rules) == 2
        assert isinstance(rules[0], Section3Dot2IPv4Address)
        assert isinstance(rules[0], Rule)

    @pytest.mark.capability
    def test_grammar_name(self) -> None:
        """IPv4 grammar has expected name."""
        grammar = IPv4Grammar()
        assert grammar.name == "ipv4_recognition"

    @pytest.mark.capability
    def test_rule_name(self) -> None:
        """IPv4 rule has expected name."""
        rule = Section3Dot2IPv4Address()
        assert rule.name == "Section 3.2-ipv4-address"

    @pytest.mark.capability
    def test_rule_citation(self) -> None:
        """IPv4 rule has expected citation."""
        rule = Section3Dot2IPv4Address()
        assert rule.citation == "Section 3.2 (internet addressing)"


# --- IPContract tests ---


@pytest.mark.capability
class TestIPContract:
    """Tests for IPContract."""

    def test_defaults(self) -> None:
        contract = IPContract()
        assert contract.capability_name == "ip"
        assert contract.include_ipv6 is True
        assert contract.excluded_rules == ()
        assert contract.year is None
        assert contract.output_format is None

    def test_active_grammars_default(self) -> None:
        contract = IPContract()
        assert contract.active_grammars == ["ipv4_recognition", "ipv6_recognition"]

    def test_active_grammars_ipv6_disabled(self) -> None:
        contract = IPContract(include_ipv6=False)
        assert contract.active_grammars == ["ipv4_recognition"]

    def test_as_dict_includes_all_fields(self) -> None:
        contract = IPContract(include_ipv6=False, year=2010)
        d = contract.as_dict()
        assert d["capability_name"] == "ip"
        assert d["include_ipv6"] is False
        assert d["year"] == 2010


# --- Package import tests ---


class TestIPPackageImports:
    @pytest.mark.capability
    def test_package_exports_ip_capability(self) -> None:
        """IP package exports IPCapability."""
        from paxman.capabilities.IP import IPCapability as IPCapabilityExport

        assert IPCapabilityExport is IPCapability

    @pytest.mark.capability
    def test_package_exports_ip_notation(self) -> None:
        """IP package exports IPNotation."""
        from paxman.capabilities.IP import IPNotation as IPNotationExport

        assert IPNotationExport is IPNotation
