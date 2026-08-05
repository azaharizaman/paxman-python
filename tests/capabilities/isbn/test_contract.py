"""Tests for ISBN contract."""

import dataclasses

import pytest

from paxman.capabilities.ISBN.contract import ISBNContract

pytestmark = [pytest.mark.capability]


def test_default_output_format() -> None:
    """output_format resolves to isbn13 by default."""
    assert ISBNContract().output_format == "isbn13"


def test_offered_output_formats() -> None:
    """Only the hyphenated format is offered beyond the default."""
    assert frozenset({"hyphenated"}) == ISBNContract.OFFERED_OUTPUT_FORMATS


def test_capability_name() -> None:
    """capability_name is fixed to isbn."""
    assert ISBNContract().capability_name == "isbn"


def test_feature_defaults() -> None:
    """Feature flags default to include_isbn10=True, range_validation=False."""
    contract = ISBNContract()
    assert contract.include_isbn10 is True
    assert contract.include_range_validation is False


def test_active_grammars_default() -> None:
    """Both isbn13 and isbn10 grammars are active by default."""
    assert ISBNContract().active_grammars == [
        "isbn13_recognition",
        "isbn10_recognition",
    ]


def test_active_grammars_isbn10_disabled() -> None:
    """Disabling isbn10 leaves only the isbn13 grammar active."""
    assert ISBNContract(include_isbn10=False).active_grammars == [
        "isbn13_recognition"
    ]


def test_frozen() -> None:
    """Assigning a field raises FrozenInstanceError."""
    contract = ISBNContract()
    with pytest.raises(dataclasses.FrozenInstanceError):
        contract.include_isbn10 = False  # type: ignore[misc]


def test_as_dict_includes_features() -> None:
    """as_dict serializes the capability-specific feature flags."""
    d = ISBNContract().as_dict()
    assert d["include_isbn10"] is True
    assert d["include_range_validation"] is False
