"""The engine: a pure, stateless referee that runs the canonicalization pipeline.

Concentrates the three invariants — Boundary, Determinism, Replay — in one
sealed component (PRD §5.1). Holds no domain opinion; only the rules of
engagement.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paxman._registry.registry import Registry
    from paxman.contracts.contract import Contract
    from paxman.contracts.verdict import Verdict

from paxman.artifacts.artifact import Artifact
from paxman.contracts.refusal import Refusal


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """Immutable configuration for the engine.

    Carries authority pinning and any other engine-wide settings. Frozen
    so the engine's behavior is fully determined at construction time.
    """

    authorities: dict[str, str] = field(default_factory=dict)
    """Map of authority name -> pinned edition (e.g. {'iana': '2024a'})."""

    @classmethod
    def default(cls) -> EngineConfig:
        """Return the default engine configuration.

        Loads authority defaults from the authorities/ package. Currently
        returns an empty config as no authority editions are bundled yet.
        """
        return cls(authorities={})

    def digest(self) -> str:
        """Produce a deterministic fingerprint of this configuration.

        The digest is a hex-encoded SHA-256 of the sorted JSON representation,
        so equal configs always produce equal digests (Invariant 2).
        """
        canonical = json.dumps(self.authorities, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Engine:
    """The sealed core: a pure, stateless referee running the canonicalization pipeline.

    Pipeline: Receive -> Resolve -> Delegate -> Seal. No I/O, no clock, no
    environment access. Holds a frozen Registry and immutable EngineConfig
    (PRD §5.1).
    """

    def __init__(self, registry: Registry, config: EngineConfig) -> None:
        """Construct the engine with a frozen registry and immutable config."""
        self._registry = registry
        self._config = config
        self._config_digest = config.digest()

    @property
    def config_digest(self) -> str:
        """Deterministic hash of the engine's configuration."""
        return self._config_digest

    def canonicalize(self, raw: str, contract: Contract) -> Artifact:
        """Run the full canonicalization pipeline.

        Receive the input and contract, resolve the owning capability,
        delegate for a verdict (or build a Refusal if none owns the kind),
        and seal the result into an Artifact.

        No capability logic is re-executed — the artifact is the sealed record.
        """
        capability = self._registry.resolve(contract)

        if capability is None:
            result: Verdict | Refusal = Refusal(
                reason=f"No capability owns kind '{contract.kind.name}'"
            )
        else:
            result = capability.render(raw, contract)
        return Artifact(
            contract=contract,
            result=result,
            config_digest=self._config_digest,
        )

    def replay(self, artifact: Artifact) -> Artifact:
        """Return the sealed record unchanged — no re-execution, byte-for-byte faithful.

        Invariant 3: every artifact Paxman emits can be handed back and
        reconstructed exactly, without re-running any logic.
        """
        return artifact
