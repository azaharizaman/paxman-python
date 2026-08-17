"""Tests for Candidate dataclass."""

from __future__ import annotations

import pytest

from paxman.core.domain import Candidate, Provenance


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

    @pytest.mark.unit
    def test_span_defaults_to_none_and_is_settable(self) -> None:
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        base = dict(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        without = Candidate(**base)
        assert without.span is None
        with_span = Candidate(**base, span=(0, 2))
        assert with_span.span == (0, 2)
        # span participates in equality and hashing
        assert without != with_span
        assert hash(with_span) is not None

    @pytest.mark.unit
    def test_span_rejects_invalid_range(self) -> None:
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        base = dict(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        with pytest.raises(ValueError):
            Candidate(**base, span=(-1, 2))
        with pytest.raises(ValueError):
            Candidate(**base, span=(4, 3))
