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
        contract = _parse_contract(data)
        result = _parse_result(data)
        raw_digest = _require_str(data.get("config_digest"), "config_digest")
        return cls(contract=contract, result=result, config_digest=raw_digest)


def _require_str(value: object, field_path: str) -> str:
    """Assert that *value* is a ``str`` or raise :class:`TypeError`."""
    if not isinstance(value, str):
        raise TypeError(f"Expected '{field_path}' to be a str, got {type(value).__name__}")
    return value


def _require_dict(value: object, field_path: str) -> dict[str, object]:
    """Assert that *value* is a ``dict`` or raise :class:`TypeError`."""
    if not isinstance(value, dict):
        raise TypeError(f"Expected '{field_path}' to be a dict, got {type(value).__name__}")
    return value


def _parse_contract(data: dict[str, object]) -> Contract:
    """Parse the ``contract`` section of a serialized Artifact."""
    raw_kind = _require_dict(data.get("contract"), "contract").get("kind")
    kind_name = _require_str(
        _require_dict(raw_kind, "contract.kind").get("name"), "contract.kind.name"
    )
    kind = Kind(name=kind_name)

    raw_pin = _require_dict(data.get("contract"), "contract").get("authority_pin")
    authority_pin: AuthorityPin | None = None
    if isinstance(raw_pin, dict):
        auth = _require_str(raw_pin.get("authority"), "authority_pin.authority")
        edit = _require_str(raw_pin.get("edition"), "authority_pin.edition")
        authority_pin = AuthorityPin(authority=auth, edition=edit)

    return Contract(kind=kind, authority_pin=authority_pin)


def _parse_result(data: dict[str, object]) -> Verdict | Refusal:
    """Parse the ``result`` section of a serialized Artifact."""
    raw_result = _require_dict(data.get("result"), "result")
    result_type = _require_str(raw_result.get("type"), "result.type")

    if result_type == "Verdict":
        canonical = _require_str(raw_result.get("canonical"), "result.canonical")
        evidence = _require_str(raw_result.get("evidence"), "result.evidence")
        return Verdict(canonical=canonical, evidence=evidence)
    if result_type == "Refusal":
        reason = _require_str(raw_result.get("reason"), "result.reason")
        return Refusal(reason=reason)
    raise ValueError(f"Unknown result type: {result_type}")
