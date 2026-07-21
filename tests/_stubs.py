"""Shared test stubs — reusable capability mocks for the test suite.

Consolidates the duplicated _StubCapability that previously existed in 4 test files.
"""

from __future__ import annotations

from dataclasses import dataclass

from paxman.artifacts.evidence import Evidence
from paxman.contracts.authority_pin import AuthorityPin
from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict


_STUB_AUTHORITY = AuthorityPin(authority="stub", edition="0.0")


def _make_stub_evidence() -> Evidence:
    """Create a minimal Evidence for stub verdicts."""
    return Evidence(rules_fired=("stub",), order=1, authority=_STUB_AUTHORITY)


@dataclass(frozen=True, slots=True)
class StubCapability:
    """Minimal capability that renders input lowercased."""

    owned_kinds: frozenset[Kind]

    def render(self, raw: str, contract: Contract) -> Verdict | Refusal:
        """Return a deterministic verdict."""
        return Verdict(canonical=raw.lower(), evidence=_make_stub_evidence())


@dataclass(frozen=True, slots=True)
class CountingStubCapability:
    """Capability that tracks render() calls via an external mutable counter.

    The dataclass itself is frozen (satisfies Capability protocol), but the
    ``_render_count`` list is mutable so the test can observe call counts
    without breaking immutability.
    """

    owned_kinds: frozenset[Kind]
    _render_count: list[int]

    def render(self, raw: str, contract: Contract) -> Verdict | Refusal:
        """Increment the counter and return a deterministic verdict."""
        self._render_count[0] += 1
        return Verdict(canonical=raw.lower(), evidence=_make_stub_evidence())
