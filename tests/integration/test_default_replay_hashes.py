"""Integration tests locking default-format replay hashes.

These literal snapshots are captured at the pre-migration baseline (Task 1 of
the centralize-output-format plan). They prove that routing canonical values
through ``Capability.format_value()`` leaves default output byte-for-byte
unchanged: any deviation from these hashes means the default behavior moved
and must be investigated rather than updating the expected value.
"""

from __future__ import annotations

from typing import Any, Protocol

import pytest

from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.IP.capability import IPCapability
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability


class _CapabilityFactory(Protocol):
    """Structural type for a capability class usable in the snapshot table."""

    def __call__(self) -> Capability[Any]:
        """Instantiate the capability."""
        ...

    @staticmethod
    def create_contract() -> Contract:
        """Create a no-argument contract for the capability."""
        ...

DEFAULT_REPLAY_HASHES = {
    "date": "cb2e67023a8c74e5eb76913a00eb1756a7ed76c3a3c8bb553a588ac5d03c65b4",
    "country": "3489ca17221e11f98068a4c5e9306a0ebfb06b857bcbaa137fdd3f14a761a70b",
    "email": "dccb1dec8fbd851c360ecb5feb0ed321a00a2ee6931ed2ba6505c0f92f9ffa31",
    "ip": "6709b8b4ca35a7fec0ddc80bf13325af0dfbcf79d17577955a2a8ae41ad8c71a",
    "phone": "c5aec207bcfb3d061585b789ccb3d6cd98d394bffbe0f81c4fcd481132647f3d",
}

DEFAULT_CASES = (
    ("date", DateCapability, "2026-01-15"),
    ("country", CountryCapability, "DE"),
    ("email", EmailCapability, "user@example.com"),
    ("ip", IPCapability, "192.0.2.1"),
    ("phone", PhoneCapability, "+15551234567"),
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("name", "capability_cls", "input_text"),
    DEFAULT_CASES,
    ids=[case[0] for case in DEFAULT_CASES],
)
def test_default_replay_hash_unchanged(
    name: str, capability_cls: _CapabilityFactory, input_text: str
) -> None:
    """A default-format run must reproduce the literal pre-migration hash."""
    register_capability(capability_cls())
    contract = capability_cls.create_contract()
    result = run_capability(input_text, contract)

    assert result.status == Resolution.SUCCESS
    assert result.version_stamp.replay_hash == DEFAULT_REPLAY_HASHES[name]
