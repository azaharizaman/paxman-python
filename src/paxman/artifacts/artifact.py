"""Artifact: the sealed, self-describing record emitted by the engine.

Faithful, byte-for-byte return to the original on replay (Invariant 3).
"""

from __future__ import annotations

from dataclasses import dataclass

from paxman.contracts.authority_pin import AuthorityPin
from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict


@dataclass(frozen=True, slots=True)
class Artifact:
    """Self-describing, replayable record of a canonicalization.

    An Artifact carries the contract, the result (Verdict or Refusal), and the
    config digest so it needs nothing outside itself to be understood or
    replayed (PRD §5.1, §3).
    """

    contract: Contract
    """The contract that was canonicalized."""

    result: Verdict | Refusal
    """The outcome — either a canonical verdict or an explicit refusal."""

    config_digest: str
    """Deterministic fingerprint of the EngineConfig that produced this artifact."""

    def to_dict(self) -> dict[str, object]:
        """Serialize to a plain dict for JSON round-trip.

        Produces a deterministic structure with sort_keys for faithful
        reconstruction (Issue #9 acceptance criteria).
        """
        result_dict: dict[str, object]
        if isinstance(self.result, Verdict):
            result_dict = {
                "type": "Verdict",
                "canonical": self.result.canonical,
                "evidence": self.result.evidence,
            }
        else:
            result_dict = {"type": "Refusal", "reason": self.result.reason}

        pin_dict: dict[str, str] | None = None
        if self.contract.authority_pin is not None:
            pin_dict = {
                "authority": self.contract.authority_pin.authority,
                "edition": self.contract.authority_pin.edition,
            }

        return {
            "contract": {
                "kind": {"name": self.contract.kind.name},
                "authority_pin": pin_dict,
            },
            "result": result_dict,
            "config_digest": self.config_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Artifact:
        """Deserialize from a plain dict produced by to_dict().

        Inverse of to_dict — reconstructs the Artifact faithfully without
        re-executing any capability logic (Invariant 3).
        """
        raw_contract = data.get("contract")
        assert isinstance(raw_contract, dict)

        raw_kind = raw_contract.get("kind")
        assert isinstance(raw_kind, dict)
        kind_name = raw_kind.get("name")
        assert isinstance(kind_name, str)
        kind = Kind(name=kind_name)

        raw_pin = raw_contract.get("authority_pin")
        authority_pin: AuthorityPin | None = None
        if isinstance(raw_pin, dict):
            auth = raw_pin.get("authority")
            edit = raw_pin.get("edition")
            assert isinstance(auth, str)
            assert isinstance(edit, str)
            authority_pin = AuthorityPin(authority=auth, edition=edit)

        contract = Contract(kind=kind, authority_pin=authority_pin)

        raw_result = data.get("result")
        assert isinstance(raw_result, dict)
        result_type = raw_result.get("type")
        assert isinstance(result_type, str)

        result: Verdict | Refusal
        if result_type == "Verdict":
            canonical = raw_result.get("canonical")
            evidence = raw_result.get("evidence")
            assert isinstance(canonical, str)
            assert isinstance(evidence, str)
            result = Verdict(canonical=canonical, evidence=evidence)
        elif result_type == "Refusal":
            reason = raw_result.get("reason")
            assert isinstance(reason, str)
            result = Refusal(reason=reason)
        else:
            raise ValueError(f"Unknown result type: {result_type}")

        raw_digest = data.get("config_digest")
        assert isinstance(raw_digest, str)

        return cls(contract=contract, result=result, config_digest=raw_digest)
