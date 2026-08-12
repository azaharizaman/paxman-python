"""Tests for the SIUnit capability wiring."""

import pytest

from paxman.capabilities.SIUnit.capability import SIUnitCapability
from paxman.capabilities.SIUnit.contract import SIUnitContract
from paxman.capabilities.SIUnit.notation import SIUnitNotation


@pytest.mark.capability
@pytest.mark.si_unit
class TestSIUnitCapability:
    """Capability wiring — grammars, rules, factory, exports."""

    def setup_method(self) -> None:
        self.capability = SIUnitCapability()

    def test_metadata(self) -> None:
        # name == "si_unit"; version == "1.0.0"
        assert self.capability.name == "si_unit"
        assert self.capability.version == "1.0.0"

    def test_get_grammars(self) -> None:
        # 3 instances with names {symbol_recognition, name_recognition,
        # compound_recognition}
        names = {g.name for g in self.capability.get_grammars()}
        assert names == {
            "symbol_recognition",
            "name_recognition",
            "compound_recognition",
        }

    def test_get_rules(self) -> None:
        # 6 instances: 5 BIPM sections + 1 ISO compound section
        names = {r.name for r in self.capability.get_rules()}
        assert names == {
            "Section 2.3.1-base-units",
            "Section 2.3.2-derived-units",
            "Section 4.1-non-si-units",
            "Section 3.2-prefixes",
            "Section-names",
            "Section 6.5-compounds",
        }

    def test_create_contract_defaults(self) -> None:
        # create_contract() returns SIUnitContract with defaults
        contract = self.capability.create_contract()
        assert isinstance(contract, SIUnitContract)
        assert contract.excluded_rules == ()
        assert contract.pinned_rules is None
        assert contract.output_format == "symbol"  # DEFAULT_OUTPUT_FORMAT

    def test_create_contract_excluded_rules(self) -> None:
        contract = self.capability.create_contract(excluded_rules=["Section-names"])
        assert contract.excluded_rules == ("Section-names",)

    def test_create_contract_extra_grammars(self) -> None:
        # SEAM: the community opt-in field is forwarded by the factory
        # (surface guard: default () + forwarding through create_contract).
        contract = self.capability.create_contract(
            extra_grammars=["dot_unit_recognition"]
        )
        assert contract.extra_grammars == ("dot_unit_recognition",)
        assert self.capability.create_contract().extra_grammars == ()

    def test_create_contract_keyword_only(self) -> None:
        # ContractFactory conformance: the common block is keyword-only
        with pytest.raises(TypeError):
            self.capability.create_contract("Section-names")  # type: ignore[call-arg]

    def test_format_value_identity(self) -> None:
        # offered formats are empty -> base identity is the contract
        notation = SIUnitNotation(text="kg", shape="symbol")
        assert self.capability.format_value("kg", "symbol", notation) == "kg"


def test_package_exports() -> None:
    # __all__ exports SIUnitCapability, SIUnitContract, SIUnitNotation
    from paxman.capabilities.SIUnit import (
        SIUnitCapability as CapabilityExport,
    )
    from paxman.capabilities.SIUnit import (
        SIUnitContract as ContractExport,
    )
    from paxman.capabilities.SIUnit import (
        SIUnitNotation as NotationExport,
    )

    assert CapabilityExport is SIUnitCapability
    assert ContractExport is SIUnitContract
    assert NotationExport is SIUnitNotation
