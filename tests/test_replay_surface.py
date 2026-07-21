"""Tests for Engine.replay and the public surface re-exports.

Covers: replay returns artifact unchanged, no re-execution, full round-trip.
"""

from __future__ import annotations

from paxman._engine.engine import Engine, EngineConfig
from paxman._registry.registry import Registry
from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict

from tests._stubs import CountingStubCapability, StubCapability


# ---------------------------------------------------------------------------
# Replay tests
# ---------------------------------------------------------------------------
class TestReplay:
    """Tests for engine.replay()."""

    def test_replay_returns_artifact_unchanged(self) -> None:
        """replay(artifact) returns the artifact as-is — Invariant 3."""
        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)
        replayed = engine.replay(artifact)

        assert replayed is artifact

    def test_replay_performs_no_re_execution(self) -> None:
        """replay does not invoke capability.render() — counter stays at 1.

        Uses CountingStubCapability with a mutable counter to prove that
        render() was called once by canonicalize() but NOT by replay().
        """
        kind = Kind(name="email.address")
        counter: list[int] = [0]
        cap = CountingStubCapability(
            owned_kinds=frozenset({kind}), _render_count=counter
        )
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)

        # render() was called once during canonicalize
        assert counter[0] == 1

        # replay should not touch the capability at all
        replayed = engine.replay(artifact)

        assert replayed is artifact
        # counter is still 1 — replay did NOT invoke render()
        assert counter[0] == 1

    def test_full_roundtrip_canonicalize_replay_identical(self) -> None:
        """canonicalize -> replay -> identical artifact (Invariant 3)."""
        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)
        replayed = engine.replay(artifact)

        assert artifact == replayed
        assert artifact.contract == replayed.contract
        assert artifact.result == replayed.result
        assert artifact.config_digest == replayed.config_digest

    def test_replay_preserves_verdict(self) -> None:
        """Replay preserves the exact verdict from canonicalize."""
        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)
        replayed = engine.replay(artifact)

        assert isinstance(replayed.result, Verdict)
        assert replayed.result.canonical == "foo@bar.com"
        assert replayed.result.evidence == "stub"

    def test_replay_preserves_refusal(self) -> None:
        """Replay preserves the exact refusal from canonicalize."""
        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({Kind(name="date.iso")}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)
        replayed = engine.replay(artifact)

        assert isinstance(replayed.result, Refusal)


# ---------------------------------------------------------------------------
# Public surface tests
# ---------------------------------------------------------------------------
class TestPublicSurface:
    """Tests for the public re-exports in paxman.__init__."""

    def test_engine_reexported(self) -> None:
        """Engine is re-exported from the root package."""
        from paxman import Engine as RootEngine

        from paxman._engine.engine import Engine

        assert RootEngine is Engine

    def test_engine_config_reexported(self) -> None:
        """EngineConfig is re-exported from the root package."""
        from paxman import EngineConfig as RootEngineConfig

        from paxman._engine.engine import EngineConfig

        assert RootEngineConfig is EngineConfig

    def test_kind_reexported(self) -> None:
        """Kind is re-exported from the root package."""
        from paxman import Kind as RootKind

        from paxman.contracts.kind import Kind

        assert RootKind is Kind

    def test_contract_reexported(self) -> None:
        """Contract is re-exported from the root package."""
        from paxman import Contract as RootContract

        from paxman.contracts.contract import Contract

        assert RootContract is Contract

    def test_registry_reexported(self) -> None:
        """Registry is re-exported from the root package."""
        from paxman import Registry as RootRegistry

        from paxman._registry.registry import Registry

        assert RootRegistry is Registry

    def test_verdict_reexported(self) -> None:
        """Verdict is re-exported from the root package."""
        from paxman import Verdict as RootVerdict

        from paxman.contracts.verdict import Verdict

        assert RootVerdict is Verdict

    def test_refusal_reexported(self) -> None:
        """Refusal is re-exported from the root package."""
        from paxman import Refusal as RootRefusal

        from paxman.contracts.refusal import Refusal

        assert RootRefusal is Refusal
