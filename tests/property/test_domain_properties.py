"""Hypothesis property-based tests for domain objects."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.core.domain import Candidate, Provenance, Resolution


@pytest.mark.property
@given(
    authority=st.text(min_size=1, max_size=50),
    spec_name=st.text(min_size=1, max_size=100),
    kind=st.sampled_from(["specification", "registry", "policy"]),
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+", fullmatch=True),
    version=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    lifecycle=st.sampled_from(["active", "deprecated", "superseded"]),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_provenance_equality_is_reflexive(
    authority: str,
    spec_name: str,
    kind: str,
    url: str,
    version: str | None,
    lifecycle: str,
    year: int,
) -> None:
    """Provenance equality is reflexive: a == a."""
    prov = Provenance(
        authority=authority,
        specification_name=spec_name,
        kind=kind,
        reference_url=url,
        version=version,
        lifecycle=lifecycle,
        publication_year=year,
    )
    assert prov == prov


@pytest.mark.property
@given(
    authority=st.text(min_size=1, max_size=50),
    spec_name=st.text(min_size=1, max_size=100),
    kind=st.sampled_from(["specification", "registry", "policy"]),
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+", fullmatch=True),
    version=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    lifecycle=st.sampled_from(["active", "deprecated", "superseded"]),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_provenance_equality_is_symmetric(
    authority: str,
    spec_name: str,
    kind: str,
    url: str,
    version: str | None,
    lifecycle: str,
    year: int,
) -> None:
    """Provenance equality is symmetric: if a == b, then b == a."""
    prov1 = Provenance(
        authority=authority,
        specification_name=spec_name,
        kind=kind,
        reference_url=url,
        version=version,
        lifecycle=lifecycle,
        publication_year=year,
    )
    prov2 = Provenance(
        authority=authority,
        specification_name=spec_name,
        kind=kind,
        reference_url=url,
        version=version,
        lifecycle=lifecycle,
        publication_year=year,
    )
    assert prov1 == prov2
    assert prov2 == prov1


@pytest.mark.property
@given(
    authority=st.text(min_size=1, max_size=50),
    spec_name=st.text(min_size=1, max_size=100),
    kind=st.sampled_from(["specification", "registry", "policy"]),
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+", fullmatch=True),
    version=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    lifecycle=st.sampled_from(["active", "deprecated", "superseded"]),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_provenance_hash_consistent_with_equality(
    authority: str,
    spec_name: str,
    kind: str,
    url: str,
    version: str | None,
    lifecycle: str,
    year: int,
) -> None:
    """Provenance hash consistent with equality: a == b implies hash(a) == hash(b)."""
    prov1 = Provenance(
        authority=authority,
        specification_name=spec_name,
        kind=kind,
        reference_url=url,
        version=version,
        lifecycle=lifecycle,
        publication_year=year,
    )
    prov2 = Provenance(
        authority=authority,
        specification_name=spec_name,
        kind=kind,
        reference_url=url,
        version=version,
        lifecycle=lifecycle,
        publication_year=year,
    )
    assert prov1 == prov2
    assert hash(prov1) == hash(prov2)


@pytest.mark.property
@given(
    value=st.text(min_size=1, max_size=100),
    recognition_rule=st.text(min_size=1, max_size=50),
    validation_rule=st.text(min_size=1, max_size=50),
)
def test_candidate_equality_is_reflexive(
    value: str,
    recognition_rule: str,
    validation_rule: str,
) -> None:
    """Candidate equality is reflexive: a == a."""
    candidate = Candidate(
        value=value,
        recognition_rule=recognition_rule,
        validation_rule=validation_rule,
        provenance=[],
    )
    assert candidate == candidate


@pytest.mark.property
@given(
    value=st.text(min_size=1, max_size=100),
    recognition_rule=st.text(min_size=1, max_size=50),
    validation_rule=st.text(min_size=1, max_size=50),
)
def test_candidate_hash_consistent_with_equality(
    value: str,
    recognition_rule: str,
    validation_rule: str,
) -> None:
    """Candidate hash consistent with equality: a == b implies hash(a) == hash(b)."""
    candidate1 = Candidate(
        value=value,
        recognition_rule=recognition_rule,
        validation_rule=validation_rule,
        provenance=[],
    )
    candidate2 = Candidate(
        value=value,
        recognition_rule=recognition_rule,
        validation_rule=validation_rule,
        provenance=[],
    )
    assert candidate1 == candidate2
    assert hash(candidate1) == hash(candidate2)


@pytest.mark.property
def test_resolution_enum_has_exactly_four_values() -> None:
    """Resolution enum has exactly 4 values."""
    assert len(Resolution) == 4
    values = {r.value for r in Resolution}
    assert values == {"missing", "invalid", "success", "ambiguous"}
