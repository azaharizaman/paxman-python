"""Tests for SIUnitContract."""

import dataclasses

import pytest

from paxman.capabilities.SIUnit.contract import SIUnitContract
from paxman.core.capability_contract import CapabilityContract
from paxman.core.errors import ContractError


@pytest.mark.capability
@pytest.mark.si_unit
class TestSIUnitContract:
    """Tests for SIUnitContract."""

    def test_is_capability_contract_subclass(self) -> None:
        assert issubclass(SIUnitContract, CapabilityContract)

    def test_capability_name(self) -> None:
        assert SIUnitContract().capability_name == "si_unit"

    def test_default_output_format(self) -> None:
        assert SIUnitContract().output_format == "symbol"

    def test_offered_formats(self) -> None:
        assert frozenset() == SIUnitContract.OFFERED_OUTPUT_FORMATS

    def test_default_format_resolution(self) -> None:
        for fmt in (None, "default", "symbol"):
            assert SIUnitContract(output_format=fmt).output_format == "symbol"

    def test_unknown_format_rejected(self) -> None:
        with pytest.raises(ContractError):
            SIUnitContract(output_format="name")

    def test_active_grammars_is_base_default(self) -> None:
        # SEAM: no feature gating -> the contract does NOT override
        # active_grammars; the base returns None and the engine runs every
        # shipped grammar in get_grammars() declaration order.
        assert SIUnitContract().active_grammars is None

    def test_extra_grammars_defaults_empty(self) -> None:
        # SEAM: the community opt-in field is inherited from the base.
        assert SIUnitContract().extra_grammars == ()

    def test_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            SIUnitContract().capability_name = "other"  # type: ignore[misc]

    def test_no_slots(self) -> None:
        """Contracts are @dataclass(frozen=True) WITHOUT slots (project
        convention — enforced by the surface guard)."""
        assert hasattr(SIUnitContract(), "__dict__")
