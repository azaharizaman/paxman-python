"""Integration tests for the engine orchestrator pipeline."""

from __future__ import annotations

import pytest

from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestRunCapability:
    @pytest.mark.integration
    def test_standard_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("Contact user@example.com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"
        assert len(result.candidates) >= 1

    @pytest.mark.integration
    def test_obfuscated_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(include_obfuscated=True)
        result = run_capability("Email user at example dot com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.integration
    def test_localhost_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.integration
    def test_missing_input(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("no email here", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_version_stamp_present(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("user@example.com", contract)

        assert result.version_stamp is not None
        assert result.version_stamp.paxman_version == "0.1.0"
        assert len(result.version_stamp.replay_hash) == 64  # SHA-256 hex

    @pytest.mark.integration
    def test_replay_determinism(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        r1 = run_capability("user@example.com", contract)
        r2 = run_capability("user@example.com", contract)

        assert r1.version_stamp.replay_hash == r2.version_stamp.replay_hash
        assert r1.canonicalized_value == r2.canonicalized_value
