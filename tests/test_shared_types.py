"""Tests for shared types: Kind, AuthorityPin, Contract, Verdict, Refusal, Evidence, Artifact.

Covers: construction, immutability, equality, hashability, and Artifact JSON round-trip.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest


# ---------------------------------------------------------------------------
# Kind
# ---------------------------------------------------------------------------
class TestKind:
    """Tests for the Kind dataclass."""

    def test_construction(self) -> None:
        """Kind is constructible with a name string."""
        from paxman.contracts.kind import Kind

        kind = Kind(name="email.address")
        assert kind.name == "email.address"

    def test_immutable(self) -> None:
        """Kind is frozen — attribute assignment raises."""
        from paxman.contracts.kind import Kind

        kind = Kind(name="email.address")
        with pytest.raises(FrozenInstanceError):
            kind.name = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Kinds with the same name are equal."""
        from paxman.contracts.kind import Kind

        a = Kind(name="email.address")
        b = Kind(name="email.address")
        assert a == b

    def test_inequality(self) -> None:
        """Kinds with different names are not equal."""
        from paxman.contracts.kind import Kind

        a = Kind(name="email.address")
        b = Kind(name="date.iso")
        assert a != b

    def test_hashable(self) -> None:
        """Kind instances can live in sets and dicts."""
        from paxman.contracts.kind import Kind

        a = Kind(name="email.address")
        b = Kind(name="email.address")
        s = {a, b}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# AuthorityPin
# ---------------------------------------------------------------------------
class TestAuthorityPin:
    """Tests for the AuthorityPin dataclass."""

    def test_construction(self) -> None:
        """AuthorityPin stores authority name and edition."""
        from paxman.contracts.authority_pin import AuthorityPin

        pin = AuthorityPin(authority="iana", edition="2024a")
        assert pin.authority == "iana"
        assert pin.edition == "2024a"

    def test_immutable(self) -> None:
        """AuthorityPin is frozen."""
        from paxman.contracts.authority_pin import AuthorityPin

        pin = AuthorityPin(authority="iana", edition="2024a")
        with pytest.raises(FrozenInstanceError):
            pin.authority = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        """AuthorityPins with the same values are equal."""
        from paxman.contracts.authority_pin import AuthorityPin

        a = AuthorityPin(authority="iana", edition="2024a")
        b = AuthorityPin(authority="iana", edition="2024a")
        assert a == b

    def test_hashable(self) -> None:
        """AuthorityPin instances can live in sets."""
        from paxman.contracts.authority_pin import AuthorityPin

        a = AuthorityPin(authority="iana", edition="2024a")
        b = AuthorityPin(authority="iana", edition="2024a")
        assert len({a, b}) == 1


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------
class TestContract:
    """Tests for the Contract dataclass."""

    def test_construction(self) -> None:
        """Contract is constructible with kind and optional authority_pin."""
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind

        kind = Kind(name="email.address")
        contract = Contract(kind=kind)
        assert contract.kind == kind
        assert contract.authority_pin is None

    def test_with_authority_pin(self) -> None:
        """Contract optionally carries an AuthorityPin."""
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind

        pin = AuthorityPin(authority="iana", edition="2024a")
        contract = Contract(kind=Kind(name="email.address"), authority_pin=pin)
        assert contract.authority_pin == pin

    def test_immutable(self) -> None:
        """Contract is frozen."""
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind

        contract = Contract(kind=Kind(name="email.address"))
        with pytest.raises(FrozenInstanceError):
            contract.kind = Kind(name="other")  # type: ignore[misc]

    def test_equality(self) -> None:
        """Contracts with the same kind and pin are equal."""
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind

        kind = Kind(name="email.address")
        a = Contract(kind=kind)
        b = Contract(kind=kind)
        assert a == b

    def test_hashable(self) -> None:
        """Contract instances can live in sets."""
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind

        kind = Kind(name="email.address")
        assert len({Contract(kind=kind), Contract(kind=kind)}) == 1


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
class TestVerdict:
    """Tests for the Verdict dataclass."""

    def test_construction(self) -> None:
        """Verdict stores canonical form and evidence."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        v = Verdict(canonical="foo@bar.com", evidence=evidence)
        assert v.canonical == "foo@bar.com"
        assert v.evidence == evidence

    def test_immutable(self) -> None:
        """Verdict is frozen."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        v = Verdict(canonical="foo@bar.com", evidence=evidence)
        with pytest.raises(FrozenInstanceError):
            v.canonical = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Verdicts with the same fields are equal."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        a = Verdict(canonical="foo@bar.com", evidence=evidence)
        b = Verdict(canonical="foo@bar.com", evidence=evidence)
        assert a == b

    def test_hashable(self) -> None:
        """Verdict instances can live in sets."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        v = Verdict(canonical="foo@bar.com", evidence=evidence)
        assert len({v, v}) == 1


# ---------------------------------------------------------------------------
# Refusal
# ---------------------------------------------------------------------------
class TestRefusal:
    """Tests for the Refusal dataclass."""

    def test_construction(self) -> None:
        """Refusal stores a reason string and kind."""
        from paxman.contracts.kind import Kind
        from paxman.contracts.refusal import Refusal

        kind = Kind(name="email.address")
        r = Refusal(reason="ambiguous input", kind=kind)
        assert r.reason == "ambiguous input"
        assert r.kind == kind

    def test_immutable(self) -> None:
        """Refusal is frozen."""
        from paxman.contracts.kind import Kind
        from paxman.contracts.refusal import Refusal

        kind = Kind(name="email.address")
        r = Refusal(reason="ambiguous input", kind=kind)
        with pytest.raises(FrozenInstanceError):
            r.reason = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Refusals with the same reason and kind are equal."""
        from paxman.contracts.kind import Kind
        from paxman.contracts.refusal import Refusal

        kind = Kind(name="email.address")
        a = Refusal(reason="ambiguous input", kind=kind)
        b = Refusal(reason="ambiguous input", kind=kind)
        assert a == b

    def test_hashable(self) -> None:
        """Refusal instances can live in sets."""
        from paxman.contracts.kind import Kind
        from paxman.contracts.refusal import Refusal

        kind = Kind(name="email.address")
        r = Refusal(reason="ambiguous input", kind=kind)
        assert len({r, r}) == 1


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------
class TestEvidence:
    """Tests for the Evidence dataclass."""

    def test_construction(self) -> None:
        """Evidence stores rules_fired, order, and authority."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin

        auth = AuthorityPin(authority="iana", edition="2024a")
        e = Evidence(rules_fired=("RFC 5322 §3.2", "Unicode 15.0"), order=2, authority=auth)
        assert e.rules_fired == ("RFC 5322 §3.2", "Unicode 15.0")
        assert e.order == 2
        assert e.authority == auth

    def test_immutable(self) -> None:
        """Evidence is frozen."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin

        auth = AuthorityPin(authority="iana", edition="2024a")
        e = Evidence(rules_fired=("RFC 5322 §3.2",), order=1, authority=auth)
        with pytest.raises(FrozenInstanceError):
            e.rules_fired = ("other",)  # type: ignore[misc]

    def test_equality(self) -> None:
        """Evidence with the same fields are equal."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin

        auth = AuthorityPin(authority="iana", edition="2024a")
        a = Evidence(rules_fired=("RFC 5322 §3.2",), order=1, authority=auth)
        b = Evidence(rules_fired=("RFC 5322 §3.2",), order=1, authority=auth)
        assert a == b

    def test_hashable(self) -> None:
        """Evidence instances can live in sets."""
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin

        auth = AuthorityPin(authority="iana", edition="2024a")
        e = Evidence(rules_fired=("RFC 5322 §3.2",), order=1, authority=auth)
        assert len({e, e}) == 1


# ---------------------------------------------------------------------------
# Artifact
# ---------------------------------------------------------------------------
class TestArtifact:
    """Tests for the Artifact dataclass."""

    def test_construction_with_verdict(self) -> None:
        """Artifact stores contract, verdict, and config_digest."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        contract = Contract(kind=Kind(name="email.address"))
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        artifact = Artifact(contract=contract, result=verdict, config_digest="abc123")
        assert artifact.contract == contract
        assert artifact.result == verdict
        assert artifact.config_digest == "abc123"

    def test_construction_with_refusal(self) -> None:
        """Artifact accepts Refusal as result (sum type)."""
        from paxman.artifacts.artifact import Artifact
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.refusal import Refusal

        kind = Kind(name="email.address")
        contract = Contract(kind=kind)
        refusal = Refusal(reason="ambiguous input", kind=kind)
        artifact = Artifact(contract=contract, result=refusal, config_digest="abc123")
        assert artifact.result == refusal

    def test_immutable(self) -> None:
        """Artifact is frozen."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        contract = Contract(kind=Kind(name="email.address"))
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        artifact = Artifact(contract=contract, result=verdict, config_digest="abc123")
        with pytest.raises(FrozenInstanceError):
            artifact.config_digest = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Artifacts with the same fields are equal."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        contract = Contract(kind=Kind(name="email.address"))
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        a = Artifact(contract=contract, result=verdict, config_digest="abc123")
        b = Artifact(contract=contract, result=verdict, config_digest="abc123")
        assert a == b

    def test_hashable(self) -> None:
        """Artifact instances can live in sets."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        contract = Contract(kind=Kind(name="email.address"))
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        a = Artifact(contract=contract, result=verdict, config_digest="abc123")
        assert len({a, a}) == 1

    def test_json_roundtrip_with_verdict(self) -> None:
        """Artifact JSON round-trip preserves all fields exactly."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        contract = Contract(kind=Kind(name="email.address"))
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        original = Artifact(contract=contract, result=verdict, config_digest="abc123")

        data = original.to_dict()
        restored = Artifact.from_dict(data)

        assert restored == original

    def test_json_roundtrip_with_refusal(self) -> None:
        """Artifact JSON round-trip with refusal result preserves all fields."""
        from paxman.artifacts.artifact import Artifact
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.refusal import Refusal

        kind = Kind(name="email.address")
        contract = Contract(kind=kind)
        refusal = Refusal(reason="ambiguous input", kind=kind)
        original = Artifact(contract=contract, result=refusal, config_digest="abc123")

        data = original.to_dict()
        restored = Artifact.from_dict(data)

        assert restored == original

    def test_json_deterministic_output(self) -> None:
        """Artifact to_dict produces deterministic JSON with sort_keys=True."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        pin = AuthorityPin(authority="iana", edition="2024a")
        contract = Contract(kind=Kind(name="email.address"), authority_pin=pin)
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        artifact = Artifact(contract=contract, result=verdict, config_digest="abc123")

        json_str = json.dumps(artifact.to_dict(), sort_keys=True, indent=2)
        # Should be parseable back
        data = json.loads(json_str)
        restored = Artifact.from_dict(data)
        assert restored == artifact

    def test_json_roundtrip_preserves_authority_pin(self) -> None:
        """JSON round-trip preserves authority_pin when present."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322",), order=1, authority=auth)
        pin = AuthorityPin(authority="iana", edition="2024a")
        contract = Contract(kind=Kind(name="email.address"), authority_pin=pin)
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        original = Artifact(contract=contract, result=verdict, config_digest="abc123")

        restored = Artifact.from_dict(original.to_dict())
        assert restored.contract.authority_pin == pin

    def test_json_roundtrip_preserves_evidence_fields(self) -> None:
        """JSON round-trip preserves Evidence rules_fired, order, and authority."""
        from paxman.artifacts.artifact import Artifact
        from paxman.artifacts.evidence import Evidence
        from paxman.contracts.authority_pin import AuthorityPin
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.verdict import Verdict

        auth = AuthorityPin(authority="iana", edition="2024a")
        evidence = Evidence(rules_fired=("RFC 5322 §3.2", "Unicode 15.0"), order=2, authority=auth)
        contract = Contract(kind=Kind(name="email.address"))
        verdict = Verdict(canonical="foo@bar.com", evidence=evidence)
        original = Artifact(contract=contract, result=verdict, config_digest="abc123")

        restored = Artifact.from_dict(original.to_dict())
        assert isinstance(restored.result, Verdict)
        assert restored.result.evidence.rules_fired == ("RFC 5322 §3.2", "Unicode 15.0")
        assert restored.result.evidence.order == 2
        assert restored.result.evidence.authority == auth

    def test_json_roundtrip_preserves_refusal_kind(self) -> None:
        """JSON round-trip preserves Refusal kind."""
        from paxman.artifacts.artifact import Artifact
        from paxman.contracts.contract import Contract
        from paxman.contracts.kind import Kind
        from paxman.contracts.refusal import Refusal

        kind = Kind(name="email.address")
        contract = Contract(kind=kind)
        refusal = Refusal(reason="ambiguous input", kind=kind)
        original = Artifact(contract=contract, result=refusal, config_digest="abc123")

        restored = Artifact.from_dict(original.to_dict())
        assert isinstance(restored.result, Refusal)
        assert restored.result.kind == kind
