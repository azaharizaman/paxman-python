import pytest

from paxman.core.domain import (
    Candidate,
    GrammarRule,
    Provenance,
    Resolution,
    RuleStrategy,
    VersionStamp,
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


class TestResolution:
    @pytest.mark.unit
    def test_has_missing(self) -> None:
        assert Resolution.MISSING.value == "missing"

    @pytest.mark.unit
    def test_has_invalid(self) -> None:
        assert Resolution.INVALID.value == "invalid"

    @pytest.mark.unit
    def test_has_success(self) -> None:
        assert Resolution.SUCCESS.value == "success"

    @pytest.mark.unit
    def test_has_ambiguous(self) -> None:
        assert Resolution.AMBIGUOUS.value == "ambiguous"

    @pytest.mark.unit
    def test_all_statuses(self) -> None:
        assert len(Resolution) == 4


class TestProvenance:
    @pytest.mark.unit
    def test_immutable(self) -> None:
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        with pytest.raises(AttributeError):
            prov.authority = "ISO"

    @pytest.mark.unit
    def test_equality_by_value(self) -> None:
        kwargs = dict(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        assert Provenance(**kwargs) == Provenance(**kwargs)

    @pytest.mark.unit
    def test_inequality_by_value(self) -> None:
        a = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        b = Provenance(
            authority="ISO",
            specification_name="ISO 8601",
            kind="specification",
            reference_url="https://www.iso.org/iso-8601-date-and-time-format.html",
            version="2019",
            lifecycle="active",
            publication_year=2019,
        )
        assert a != b

    @pytest.mark.unit
    def test_hashable(self) -> None:
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        assert hash(prov) is not None
        assert hash(prov) == hash(prov)


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


class TestCandidate:
    @pytest.mark.unit
    def test_immutable(self) -> None:
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        c = Candidate(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        with pytest.raises(AttributeError):
            c.value = "other@example.com"

    @pytest.mark.unit
    def test_equality(self) -> None:
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        kwargs = dict(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        assert Candidate(**kwargs) == Candidate(**kwargs)

    @pytest.mark.unit
    def test_hashable(self) -> None:
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        c = Candidate(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        assert hash(c) is not None


class TestVersionStamp:
    @pytest.mark.unit
    def test_immutable(self) -> None:
        vs = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        with pytest.raises(AttributeError):
            vs.paxman_version = "0.2.0"

    @pytest.mark.unit
    def test_equality(self) -> None:
        a = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        b = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        assert a == b

    @pytest.mark.unit
    def test_inequality(self) -> None:
        a = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        b = VersionStamp(paxman_version="0.1.0", replay_hash="def456")
        assert a != b

    @pytest.mark.unit
    def test_hashable(self) -> None:
        vs = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        assert hash(vs) is not None
