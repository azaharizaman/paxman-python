# tests/capabilities/url/test_contract.py
"""Tests for the URL capability contract."""

import dataclasses

import pytest

from paxman.capabilities.URL.contract import URLCapabilityContract
from paxman.core.errors import ContractError

pytestmark = [pytest.mark.capability, pytest.mark.url]

_STANDARD_KEYS = frozenset(
    {"capability_name", "excluded_rules", "pinned_rules", "year", "output_format"}
)


@pytest.mark.capability
class TestURLCapabilityContractDefaults:
    """Default field values."""

    def test_defaults(self) -> None:
        """Every standard field takes its base default; grammar is the only one."""
        contract = URLCapabilityContract()
        assert contract.capability_name == "url"
        assert contract.excluded_rules == ()
        assert contract.pinned_rules is None
        assert contract.year is None
        assert contract.output_format == "url"
        assert contract.active_grammars == ("absolute_uri_recognition",)

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


@pytest.mark.capability
class TestURLCapabilityContractSerialization:
    """as_dict surface."""

    def test_extra_dict_fields_empty(self) -> None:
        """D14 — no feature flags, so no extra contract keys."""
        assert URLCapabilityContract()._extra_dict_fields() == {}

    def test_contract_keys(self) -> None:
        """asdict() keys are exactly the standard contract keys — guard that no
        feature key leaks into the replay-hash surface (Traps 4.9)."""
        assert set(dataclasses.asdict(URLCapabilityContract()).keys()) == _STANDARD_KEYS

    def test_as_dict_deterministic_key_set(self) -> None:
        """as_dict() emits the standard keys with no extras."""
        assert set(URLCapabilityContract().as_dict().keys()) == _STANDARD_KEYS

    def test_as_dict_includes_resolved_output_format(self) -> None:
        """as_dict() emits the resolved (non-None) output_format."""
        assert URLCapabilityContract().as_dict()["output_format"] == "url"
