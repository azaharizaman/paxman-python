"""Hypothesis property-based tests for domain objects."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.core.domain import Candidate, Provenance, Resolution, VersionStamp


@given(
    authority=st.text(min_size=1, max_size=50),
    spec_name=st.text(min_size=1, max_size=100),
    kind=st.sampled_from(["specification", "registry", "policy"]),
    url=st.from_regex(r"https?://[a-z0-9.-]+", fullmatch=True),
    version=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    lifecycle=st.sampled_from(["active", "deprecated", "superseded"]),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_provenance_is_immutable(
    authority: str,
    spec_name: str,
    kind: str,
    url: str,
    version: str | None,
    lifecycle: str,
    year: int,
) -> None:
    """Provenance instances cannot be mutated after creation."""
    prov = Provenance(
        authority=authority,
        specification_name=spec_name,
        kind=kind,
        reference_url=url,
        version=version,
        lifecycle=lifecycle,
        publication_year=year,
    )
    with pytest.raises(AttributeError):
        prov.authority = "changed"  # type: ignore[misc]


@given(
    value=st.text(min_size=1, max_size=100),
    recognition_rule=st.text(min_size=1, max_size=50),
    validation_rule=st.text(min_size=1, max_size=50),
)
def test_candidate_is_immutable(
    value: str,
    recognition_rule: str,
    validation_rule: str,
) -> None:
    """Candidate instances cannot be mutated after creation."""
    candidate = Candidate(
        value=value,
        recognition_rule=recognition_rule,
        validation_rule=validation_rule,
        provenance=[],
    )
    with pytest.raises(AttributeError):
        candidate.value = "changed"  # type: ignore[misc]


@given(
    paxman_version=st.text(min_size=1, max_size=20),
    replay_hash=st.text(min_size=1, max_size=64),
)
def test_version_stamp_is_immutable(
    paxman_version: str,
    replay_hash: str,
) -> None:
    """VersionStamp instances cannot be mutated after creation."""
    stamp = VersionStamp(
        paxman_version=paxman_version,
        replay_hash=replay_hash,
    )
    with pytest.raises(AttributeError):
        stamp.paxman_version = "changed"  # type: ignore[misc]


def test_resolution_enum_values() -> None:
    """Resolution enum has exactly 4 values."""
    assert len(Resolution) == 4
    assert Resolution.MISSING.value == "missing"
    assert Resolution.INVALID.value == "invalid"
    assert Resolution.SUCCESS.value == "success"
    assert Resolution.AMBIGUOUS.value == "ambiguous"


def test_resolution_enum_members_are_unique() -> None:
    """Resolution enum values are all distinct."""
    values = [r.value for r in Resolution]
    assert len(values) == len(set(values))
