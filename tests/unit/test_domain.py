"""Tests for domain objects.

Classes moved to dedicated modules:
- TestProvenance    → test_provenance.py
- TestCandidate     → test_candidate.py
- TestRecognizedRep → test_recognized_rep.py
- TestVersionStamp  → test_version_stamp.py
- TestResolution    → test_resolution.py
"""

from __future__ import annotations

import pytest

from paxman.core.domain import (
    GrammarRule,
    Notation,
    RuleStrategy,
)


class TestRuleStrategy:
    @pytest.mark.unit
    def test_has_regex(self) -> None:
        assert RuleStrategy.REGEX.value == "regex"

    @pytest.mark.unit
    def test_has_lookup_table(self) -> None:
        assert RuleStrategy.LOOKUP_TABLE.value == "lookup_table"

    @pytest.mark.unit
    def test_has_parser(self) -> None:
        assert RuleStrategy.PARSER.value == "parser"

    @pytest.mark.unit
    def test_all_strategies(self) -> None:
        assert len(RuleStrategy) == 3


class TestGrammarRule:
    @pytest.mark.unit
    def test_immutable(self) -> None:
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        with pytest.raises(AttributeError):
            gr.capability_name = "date"

    @pytest.mark.unit
    def test_equality(self) -> None:
        a = GrammarRule(capability_name="email", grammar_name="standard")
        b = GrammarRule(capability_name="email", grammar_name="standard")
        assert a == b

    @pytest.mark.unit
    def test_inequality(self) -> None:
        a = GrammarRule(capability_name="email", grammar_name="standard")
        b = GrammarRule(capability_name="email", grammar_name="obfuscated")
        assert a != b

    @pytest.mark.unit
    def test_hashable(self) -> None:
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        assert hash(gr) is not None


class TestNotation:
    @pytest.mark.unit
    def test_is_list_of_strings(self) -> None:
        n: Notation = ["local", "domain"]
        assert n[0] == "local"
        assert n[1] == "domain"

    @pytest.mark.unit
    def test_accepts_variable_length(self) -> None:
        n1: Notation = ["a"]
        n2: Notation = ["a", "b"]
        n3: Notation = ["a", "b", "c"]
        assert len(n1) == 1
        assert len(n2) == 2
        assert len(n3) == 3


class TestRuleAcceptsContract:
    """Verify that Rule.matches() and Rule.normalize() accept a contract parameter."""

    @pytest.mark.unit
    def test_rule_matches_accepts_contract(self) -> None:
        from paxman.capabilities.Email.contract import EmailContract
        from paxman.capabilities.Email.notation import EmailNotation
        from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec

        rule = Section341AddrSpec()
        notation = EmailNotation(local_part="user", domain_part="example.com")
        contract = EmailContract()
        assert rule.matches(notation, contract) is True

    @pytest.mark.unit
    def test_rule_normalize_accepts_contract(self) -> None:
        from paxman.capabilities.Email.contract import EmailContract
        from paxman.capabilities.Email.notation import EmailNotation
        from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec

        rule = Section341AddrSpec()
        notation = EmailNotation(local_part="USER", domain_part="EXAMPLE.COM")
        contract = EmailContract()
        assert rule.normalize(notation, contract) == "user@example.com"
