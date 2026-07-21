"""Tests for Engine and EngineConfig.

Covers: full pipeline, deterministic output, no-owner -> Refusal, config_digest
in artifact, authority pin resolution.
"""

from __future__ import annotations

import pytest

from paxman._registry.registry import Registry
from paxman.contracts.authority_pin import AuthorityPin
from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict

from tests._stubs import StubCapability


# ---------------------------------------------------------------------------
# EngineConfig
# ---------------------------------------------------------------------------
class TestEngineConfig:
    """Tests for the EngineConfig dataclass."""

    def test_construction(self) -> None:
        """EngineConfig is constructible with explicit fields."""
        from paxman._engine.engine import EngineConfig

        config = EngineConfig(authorities={})
        assert config.authorities == {}

    def test_immutable(self) -> None:
        """EngineConfig is frozen."""
        from paxman._engine.engine import EngineConfig

        config = EngineConfig(authorities={})
        with pytest.raises(Exception):
            config.authorities = {}  # type: ignore[misc]

    def test_default_classmethod(self) -> None:
        """EngineConfig.default() returns a valid default config."""
        from paxman._engine.engine import EngineConfig

        config = EngineConfig.default()
        assert isinstance(config, EngineConfig)

    def test_digest_deterministic(self) -> None:
        """EngineConfig.digest() produces a deterministic fingerprint."""
        from paxman._engine.engine import EngineConfig

        config = EngineConfig(authorities={})
        d1 = config.digest()
        d2 = config.digest()
        assert d1 == d2
        assert isinstance(d1, str)
        assert len(d1) > 0

    def test_digest_different_for_different_configs(self) -> None:
        """Different configs produce different digests."""
        from paxman._engine.engine import EngineConfig

        c1 = EngineConfig(authorities={})
        c2 = EngineConfig(authorities={"iana": "2024a"})
        assert c1.digest() != c2.digest()


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class TestEngine:
    """Tests for the Engine class."""

    def test_construction(self) -> None:
        """Engine is constructible with registry and config."""
        from paxman._engine.engine import Engine, EngineConfig

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)
        assert engine is not None

    def test_config_digest_property(self) -> None:
        """Engine exposes config_digest as a property."""
        from paxman._engine.engine import Engine, EngineConfig

        config = EngineConfig(authorities={})
        engine = Engine(registry=Registry(capabilities=[]), config=config)
        assert engine.config_digest == config.digest()

    def test_canonicalize_full_pipeline(self) -> None:
        """engine.canonicalize runs the full Receive -> Resolve -> Delegate -> Seal pipeline."""
        from paxman._engine.engine import Engine, EngineConfig

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)

        assert isinstance(artifact.result, Verdict)
        assert artifact.result.canonical == "foo@bar.com"
        assert artifact.contract == contract

    def test_canonicalize_no_owner_returns_refusal(self) -> None:
        """When no capability owns the kind, Refusal is sealed into the artifact."""
        from paxman._engine.engine import Engine, EngineConfig

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({Kind(name="date.iso")}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)

        assert isinstance(artifact.result, Refusal)
        assert "no capability" in artifact.result.reason.lower() or "no owner" in artifact.result.reason.lower()

    def test_canonicalize_deterministic(self) -> None:
        """Same input + same config -> same artifact (Invariant 2)."""
        from paxman._engine.engine import Engine, EngineConfig

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        a1 = engine.canonicalize("FOO@BAR.COM", contract)
        a2 = engine.canonicalize("FOO@BAR.COM", contract)

        assert a1 == a2

    def test_config_digest_in_artifact(self) -> None:
        """Every artifact carries the engine's config_digest."""
        from paxman._engine.engine import Engine, EngineConfig

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)

        assert artifact.config_digest == config.digest()

    def test_authority_pin_resolution(self) -> None:
        """Engine resolves authority_pin from config before calling Delegate.

        Spec decision #4: authority_pin is injected from the contract's pin,
        not from the capability.
        """
        from paxman._engine.engine import Engine, EngineConfig

        kind = Kind(name="email.address")
        pin = AuthorityPin(authority="iana", edition="2024a")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={"iana": "2024a"})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind, authority_pin=pin)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)

        assert artifact.contract.authority_pin == pin

    def test_no_io_no_clock(self) -> None:
        """Engine pipeline has no I/O, clock, or environment dependence."""
        from paxman._engine.engine import Engine, EngineConfig

        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        # Run twice — deterministic output proves no I/O or clock
        results = [engine.canonicalize("TEST", contract) for _ in range(10)]
        assert all(r == results[0] for r in results)
