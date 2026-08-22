"""Tests for the IBAN capability wiring (scaffold)."""

import pytest

from paxman.api import canonicalize
from paxman.capabilities.IBAN.capability import IBANCapability
from paxman.capabilities.IBAN.contract import IBANContract
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution


@pytest.mark.capability
class TestIBANCapability:
    """Capability wiring — grammars, rules, factory."""

    def setup_method(self) -> None:
        self.capability = IBANCapability()

    def test_metadata(self) -> None:
        assert self.capability.name == "iban"

    def test_get_grammars(self) -> None:
        names = {g.name for g in self.capability.get_grammars()}
        assert names == {"iban_recognition"}

    def test_get_rules(self) -> None:
        names = {r.name for r in self.capability.get_rules()}
        assert names == {"Section 1-overview"}

    def test_create_contract_defaults(self) -> None:
        contract = self.capability.create_contract()
        assert isinstance(contract, IBANContract)
        assert contract.output_format == "electronic"


@pytest.mark.capability
class TestIBANCapabilityPipeline:
    """End-to-end: scaffold probe resolves to MISSING."""

    @pytest.fixture(autouse=True)
    def _clean_registry(self) -> None:
        reset_registry()
        yield
        reset_registry()

    def test_scaffold_probe_missing(self) -> None:
        register_capability(IBANCapability())
        contract = IBANCapability.create_contract()
        result = canonicalize("scaffold probe", contract)
        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
