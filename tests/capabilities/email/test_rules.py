"""Tests for Email validation rules."""

from __future__ import annotations

import pytest

from paxman.capabilities.Email.contract import EmailContract
from paxman.capabilities.Email.notation import EmailNotation
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
from paxman.capabilities.Email.rules.rfc_6761_ed2012 import Section63localhost
from paxman.core.domain import RuleStrategy


class TestSection341AddrSpec:
    """RFC 5322 Section 3.4.1 — addr-spec rule tests."""

    @pytest.mark.capability
    def test_matches_valid_email(self) -> None:
        rule = Section341AddrSpec()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="user", domain_part="example.com"), contract
            )
            is True
        )

    @pytest.mark.capability
    def test_matches_email_with_dots(self) -> None:
        rule = Section341AddrSpec()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="first.last", domain_part="domain.co.uk"),
                contract,
            )
            is True
        )

    @pytest.mark.capability
    def test_matches_email_with_plus(self) -> None:
        rule = Section341AddrSpec()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="user+tag", domain_part="gmail.com"), contract
            )
            is True
        )

    @pytest.mark.capability
    def test_rejects_local_part_with_spaces(self) -> None:
        rule = Section341AddrSpec()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="user name", domain_part="example.com"),
                contract,
            )
            is False
        )

    @pytest.mark.capability
    def test_rejects_domain_without_tld(self) -> None:
        rule = Section341AddrSpec()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="user", domain_part="localhost"), contract
            )
            is False
        )

    @pytest.mark.capability
    def test_normalize_lowercases(self) -> None:
        rule = Section341AddrSpec()
        contract = EmailContract()
        result = rule.normalize(
            EmailNotation(local_part="User", domain_part="Example.COM"), contract
        )
        assert result == "user@example.com"

    @pytest.mark.capability
    def test_provenance_attributes(self) -> None:
        rule = Section341AddrSpec()
        assert rule.provenance.authority == "IETF"
        assert rule.provenance.specification_name == "RFC 5322"
        assert rule.provenance.publication_year == 2008
        assert rule.provenance.lifecycle == "active"

    @pytest.mark.capability
    def test_rule_name(self) -> None:
        rule = Section341AddrSpec()
        assert rule.name == "Section 3.4.1-addr-spec"

    @pytest.mark.capability
    def test_strategy_is_regex(self) -> None:
        rule = Section341AddrSpec()
        assert rule.strategy == RuleStrategy.REGEX


class TestSection63Localhost:
    """RFC 6761 Section 6.3 — localhost rule tests."""

    @pytest.mark.capability
    def test_matches_localhost_email(self) -> None:
        rule = Section63localhost()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="admin", domain_part="localhost"), contract
            )
            is True
        )

    @pytest.mark.capability
    def test_matches_any_local_part(self) -> None:
        rule = Section63localhost()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="anything", domain_part="localhost"), contract
            )
            is True
        )

    @pytest.mark.capability
    def test_rejects_non_localhost_domain(self) -> None:
        rule = Section63localhost()
        contract = EmailContract()
        assert (
            rule.matches(
                EmailNotation(local_part="user", domain_part="example.com"), contract
            )
            is False
        )

    @pytest.mark.capability
    def test_normalize_preserves_case(self) -> None:
        rule = Section63localhost()
        contract = EmailContract()
        result = rule.normalize(
            EmailNotation(local_part="Admin", domain_part="localhost"), contract
        )
        assert result == "Admin@localhost"

    @pytest.mark.capability
    def test_provenance_attributes(self) -> None:
        rule = Section63localhost()
        assert rule.provenance.authority == "IETF"
        assert rule.provenance.specification_name == "RFC 6761"
        assert rule.provenance.publication_year == 2012
        assert rule.provenance.lifecycle == "active"

    @pytest.mark.capability
    def test_rule_name(self) -> None:
        rule = Section63localhost()
        assert rule.name == "Section 6.3-localhost"

    @pytest.mark.capability
    def test_strategy_is_regex(self) -> None:
        rule = Section63localhost()
        assert rule.strategy == RuleStrategy.REGEX
