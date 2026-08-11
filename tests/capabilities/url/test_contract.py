# tests/capabilities/url/test_contract.py
"""Tests for the URL capability contract."""

import dataclasses

import pytest

from paxman.capabilities.URL.contract import URLCapabilityContract
from paxman.core.errors import ContractError

pytestmark = [pytest.mark.capability, pytest.mark.url]


@pytest.mark.capability
class TestURLCapabilityContractDefaults:
    """Default field values."""

    def test_defaults(self) -> None:
        """Every standard field takes its base default; active_grammars is None."""
        contract = URLCapabilityContract()
        assert contract.capability_name == "url"
        assert contract.excluded_rules == ()
        assert contract.pinned_rules is None
        assert contract.year is None
        assert contract.output_format == "url"
        assert contract.active_grammars is None

    def test_frozen(self) -> None:
        """Assigning a field raises FrozenInstanceError."""
        contract = URLCapabilityContract()
        with pytest.raises(dataclasses.FrozenInstanceError):
            contract.excluded_rules = ("x",)  # type: ignore[misc]

    def test_no_slots(self) -> None:
        """Contracts are @dataclass(frozen=True) WITHOUT slots (project
        convention — enforced by the surface guard)."""
        assert hasattr(URLCapabilityContract(), "__dict__")


@pytest.mark.capability
class TestURLCapabilityContractOutputFormat:
    """output_format resolution (base-class rules)."""

    def test_default_resolves_to_url(self) -> None:
        """The single canonical output format is 'url' — the WHATWG
        serialization (D14: one output format, identity formatter)."""
        assert URLCapabilityContract().output_format == "url"
        assert URLCapabilityContract(output_format=None).output_format == "url"
        assert URLCapabilityContract(output_format="default").output_format == "url"

    def test_url_is_explicitly_accepted(self) -> None:
        """output_format='url' resolves to itself."""
        assert URLCapabilityContract(output_format="url").output_format == "url"

    @pytest.mark.parametrize("fmt", ["", "none", "None", "compact", "ISO", "e164"])
    def test_unknown_format_raises_contract_error(self, fmt: str) -> None:
        """Unoffered output_format values raise ContractError at construction."""
        with pytest.raises(ContractError):
            URLCapabilityContract(output_format=fmt)
