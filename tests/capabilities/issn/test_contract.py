"""Tests for ISSNContract — TDD Task 2."""

import dataclasses

import pytest

from paxman.capabilities.ISSN.contract import ISSNContract
from paxman.core.errors import ContractError

pytestmark = [pytest.mark.capability]


def test_default_output_format() -> None:
    """Default output_format resolves to hyphenated."""
    assert ISSNContract().output_format == "hyphenated"


def test_offered_output_formats() -> None:
    """Offered output formats are compact and urn."""
    assert frozenset({"compact", "urn"}) == ISSNContract.OFFERED_OUTPUT_FORMATS


def test_capability_name() -> None:
    """capability_name is fixed to issn."""
    assert ISSNContract().capability_name == "issn"


def test_default_is_hyphenated_via_none_and_default_string() -> None:
    """None, default, and hyphenated all resolve to hyphenated."""
    assert ISSNContract(output_format=None).output_format == "hyphenated"
    assert ISSNContract(output_format="default").output_format == "hyphenated"
    assert ISSNContract(output_format="hyphenated").output_format == "hyphenated"


def test_offered_compact_and_urn() -> None:
    """Compact and urn output formats resolve correctly."""
    assert ISSNContract(output_format="compact").output_format == "compact"
    assert ISSNContract(output_format="urn").output_format == "urn"


def test_frozen() -> None:
    """Assigning a field raises FrozenInstanceError."""
    contract = ISSNContract()
    with pytest.raises(dataclasses.FrozenInstanceError):
        contract.output_format = "compact"  # type: ignore[misc]


def test_invalid_output_format_raises() -> None:
    """Unknown output_format raises ContractError."""
    with pytest.raises(ContractError):
        ISSNContract(output_format="issn")


def test_active_grammars_is_none() -> None:
    """ISSN has no active_grammars override — base returns None."""
    assert ISSNContract().active_grammars is None
