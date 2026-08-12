"""Tests for capability discovery registry."""

from __future__ import annotations

import pytest

from paxman.core.capability import Capability
from paxman.core.discovery import (
    freeze_registry,
    get_capability,
    is_registry_frozen,
    register_capability,
    reset_registry,
)
from paxman.core.domain import Grammar, RecognitionMatch, Rule
from paxman.core.errors import CapabilityError
from paxman.core.extensions import get_extended_grammars, register_grammar

# --- Concrete test doubles ---


class StubCapability(Capability):
    """Minimal capability for testing the registry."""

    name = "stub"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar]:
        return []

    def get_rules(self) -> list[Rule]:
        return []


class StubCapabilityV2(Capability):
    """Same name, different class — tests name collision."""

    name = "stub"
    version = "2.0.0"

    def get_grammars(self) -> list[Grammar]:
        return []

    def get_rules(self) -> list[Rule]:
        return []


class AnotherCapability(Capability):
    """Different capability name — tests multiple registrations."""

    name = "another"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar]:
        return []

    def get_rules(self) -> list[Rule]:
        return []


class DotDateGrammar(Grammar):
    """Minimal community grammar for extension delegation tests."""

    name = "dot_date_recognition"
    semantics = "dot_date_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch]:
        return []


# --- Tests ---


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Reset registry before every test to avoid cross-test pollution."""
    reset_registry()
    yield
    reset_registry()


class TestRegisterCapability:
    @pytest.mark.unit
    def test_register_single_capability(self) -> None:
        cap = StubCapability()
        register_capability(cap)
        assert get_capability("stub") is cap

    @pytest.mark.unit
    def test_register_multiple_capabilities(self) -> None:
        stub = StubCapability()
        another = AnotherCapability()
        register_capability(stub)
        register_capability(another)
        assert get_capability("stub") is stub
        assert get_capability("another") is another

    @pytest.mark.unit
    def test_reject_duplicate_name(self) -> None:
        register_capability(StubCapability())
        with pytest.raises(CapabilityError, match="already registered"):
            register_capability(StubCapabilityV2())

    @pytest.mark.unit
    def test_reject_non_capability_instance(self) -> None:
        with pytest.raises(CapabilityError, match="Expected Capability instance"):
            register_capability("not a capability")  # type: ignore[arg-type]

    @pytest.mark.unit
    def test_reject_none(self) -> None:
        with pytest.raises(CapabilityError, match="Expected Capability instance"):
            register_capability(None)  # type: ignore[arg-type]

    @pytest.mark.unit
    def test_reject_dict(self) -> None:
        with pytest.raises(CapabilityError, match="Expected Capability instance"):
            register_capability({"name": "fake"})  # type: ignore[arg-type]


class TestGetCapability:
    @pytest.mark.unit
    def test_get_registered_capability(self) -> None:
        cap = StubCapability()
        register_capability(cap)
        assert get_capability("stub") is cap

    @pytest.mark.unit
    def test_get_unknown_capability_raises(self) -> None:
        with pytest.raises(CapabilityError, match="Unknown capability"):
            get_capability("nonexistent")

    @pytest.mark.unit
    def test_get_after_register_returns_same_instance(self) -> None:
        cap = StubCapability()
        register_capability(cap)
        result = get_capability("stub")
        assert result is cap


class TestFreezeRegistry:
    @pytest.mark.unit
    def test_initially_not_frozen(self) -> None:
        assert is_registry_frozen() is False

    @pytest.mark.unit
    def test_freeze_blocks_registration(self) -> None:
        freeze_registry()
        with pytest.raises(CapabilityError, match="frozen"):
            register_capability(StubCapability())

    @pytest.mark.unit
    def test_freeze_still_allows_lookup(self) -> None:
        cap = StubCapability()
        register_capability(cap)
        freeze_registry()
        assert get_capability("stub") is cap

    @pytest.mark.unit
    def test_freeze_is_idempotent(self) -> None:
        freeze_registry()
        freeze_registry()  # second call should not raise
        assert is_registry_frozen() is True


class TestIsRegistryFrozen:
    @pytest.mark.unit
    def test_returns_false_by_default(self) -> None:
        assert is_registry_frozen() is False

    @pytest.mark.unit
    def test_returns_true_after_freeze(self) -> None:
        freeze_registry()
        assert is_registry_frozen() is True


class TestResetRegistry:
    @pytest.mark.unit
    def test_clears_all_capabilities(self) -> None:
        register_capability(StubCapability())
        register_capability(AnotherCapability())
        reset_registry()
        with pytest.raises(CapabilityError, match="Unknown capability"):
            get_capability("stub")

    @pytest.mark.unit
    def test_unfreezes_registry(self) -> None:
        freeze_registry()
        reset_registry()
        assert is_registry_frozen() is False

    @pytest.mark.unit
    def test_allows_reregistration_after_reset(self) -> None:
        register_capability(StubCapability())
        freeze_registry()
        reset_registry()
        # Should not raise now
        register_capability(StubCapability())
        assert get_capability("stub") is not None

    @pytest.mark.unit
    def test_reset_on_empty_registry_is_noop(self) -> None:
        reset_registry()  # should not raise
        assert is_registry_frozen() is False


class TestExtensionFreezeDelegation:
    @pytest.mark.unit
    def test_freeze_registry_blocks_extension_registration(self) -> None:
        freeze_registry()
        with pytest.raises(CapabilityError, match="frozen"):
            register_grammar("date", DotDateGrammar)

    @pytest.mark.unit
    def test_reset_registry_clears_extensions(self) -> None:
        register_grammar("date", DotDateGrammar)
        reset_registry()
        assert get_extended_grammars("date") == []
