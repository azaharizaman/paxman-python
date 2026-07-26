"""Tests for Provenance dataclass."""

from __future__ import annotations

import pytest

from paxman.core.domain import Provenance


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
