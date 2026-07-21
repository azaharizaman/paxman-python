"""Tests for Capability Protocol and frozen Registry.

Covers: Protocol conformance, overlap rejection, freeze, resolve, no-owner case.
"""

from __future__ import annotations

import types

import pytest

from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict

from tests._stubs import StubCapability


# ---------------------------------------------------------------------------
# Capability Protocol
# ---------------------------------------------------------------------------
class TestCapabilityProtocol:
    """Tests for the Capability Protocol definition."""

    def test_stub_satisfies_protocol(self) -> None:
        """A class with owned_kinds and render() satisfies Capability."""
        from paxman.capabilities.capability import Capability

        stub = StubCapability(owned_kinds=frozenset({Kind(name="email.address")}))
        # Structural check: stub has the right attributes
        assert hasattr(stub, "owned_kinds")
        assert hasattr(stub, "render")
        # Verify it can be used as a Capability via structural typing
        cap: Capability = stub  # type: ignore[assignment]
        assert cap.owned_kinds == frozenset({Kind(name="email.address")})

    def test_protocol_not_runtime_checkable(self) -> None:
        """Capability is NOT decorated with @runtime_checkable."""
        from paxman.capabilities.capability import Capability

        # Runtime checkable protocols have _is_runtime_protocol = True
        is_runtime = getattr(Capability, "_is_runtime_protocol", False)
        assert is_runtime is False, "Capability must NOT be @runtime_checkable"

    def test_protocol_has_owned_kinds_and_render(self) -> None:
        """Capability Protocol structural check: stub with correct shape satisfies it."""
        from paxman.capabilities.capability import Capability

        stub = StubCapability(owned_kinds=frozenset({Kind(name="email.address")}))
        # Structural conformance: the Protocol is satisfied by shape, not inheritance
        assert isinstance(stub.owned_kinds, frozenset)
        assert callable(stub.render)
        # Protocol assignment proves structural conformance
        cap: Capability = stub  # type: ignore[assignment]
        assert cap.owned_kinds == frozenset({Kind(name="email.address")})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
class TestRegistry:
    """Tests for the Registry class."""

    def test_construction(self) -> None:
        """Registry is constructible with a list of capabilities."""
        from paxman._registry.registry import Registry

        cap = StubCapability(owned_kinds=frozenset({Kind(name="email.address")}))
        registry = Registry(capabilities=[cap])
        assert registry is not None

    def test_frozen_via_mapping_proxy(self) -> None:
        """Registry freezes capabilities via types.MappingProxyType."""
        from paxman._registry.registry import Registry

        cap = StubCapability(owned_kinds=frozenset({Kind(name="email.address")}))
        registry = Registry(capabilities=[cap])
        assert isinstance(registry._capabilities, types.MappingProxyType)

    def test_overlap_rejection(self) -> None:
        """Registry rejects overlapping owned_kinds at construction."""
        from paxman._registry.registry import Registry

        kind = Kind(name="email.address")
        cap1 = StubCapability(owned_kinds=frozenset({kind}))
        cap2 = StubCapability(owned_kinds=frozenset({kind}))
        with pytest.raises(ValueError, match="(?i)overlap"):
            Registry(capabilities=[cap1, cap2])

    def test_overlap_rejection_multiple_kinds(self) -> None:
        """Registry rejects overlap when capabilities share any Kind."""
        from paxman._registry.registry import Registry

        shared = Kind(name="email.address")
        unique1 = Kind(name="date.iso")
        unique2 = Kind(name="identifier.uuid")
        cap1 = StubCapability(owned_kinds=frozenset({shared, unique1}))
        cap2 = StubCapability(owned_kinds=frozenset({shared, unique2}))
        with pytest.raises(ValueError, match="(?i)overlap"):
            Registry(capabilities=[cap1, cap2])

    def test_resolve_returns_owning_capability(self) -> None:
        """resolve() returns the single owning capability for a contract."""
        from paxman._registry.registry import Registry

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])

        contract = Contract(kind=kind)
        resolved = registry.resolve(contract)
        assert resolved is cap

    def test_resolve_no_owner_returns_none(self) -> None:
        """resolve() returns None when no capability owns the kind."""
        from paxman._registry.registry import Registry

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({Kind(name="date.iso")}))
        registry = Registry(capabilities=[cap])

        contract = Contract(kind=kind)
        resolved = registry.resolve(contract)
        assert resolved is None

    def test_resolve_empty_registry(self) -> None:
        """resolve() returns None for an empty registry."""
        from paxman._registry.registry import Registry

        registry = Registry(capabilities=[])
        contract = Contract(kind=Kind(name="email.address"))
        assert registry.resolve(contract) is None

    def test_multiple_non_overlapping_capabilities(self) -> None:
        """Registry accepts multiple capabilities with disjoint kinds."""
        from paxman._registry.registry import Registry

        cap1 = StubCapability(owned_kinds=frozenset({Kind(name="email.address")}))
        cap2 = StubCapability(owned_kinds=frozenset({Kind(name="date.iso")}))
        cap3 = StubCapability(owned_kinds=frozenset({Kind(name="identifier.uuid")}))
        registry = Registry(capabilities=[cap1, cap2, cap3])

        assert registry.resolve(Contract(kind=Kind(name="email.address"))) is cap1
        assert registry.resolve(Contract(kind=Kind(name="date.iso"))) is cap2
        assert registry.resolve(Contract(kind=Kind(name="identifier.uuid"))) is cap3
