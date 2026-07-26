"""Integration tests for ambiguity detection in the engine orchestrator."""

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


class TestAmbiguityDetection:
    """Verify SUCCESS vs AMBIGUOUS resolution based on candidate agreement."""

    @pytest.mark.integration
    def test_localhost_and_rfc5322_same_value(self):
        """localhost@localhost → both rules agree → SUCCESS."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("admin@localhost", contract)

        # Standard grammar requires a TLD (dot-separated), so it won't
        # recognise admin@localhost.  The localhost grammar matches, and
        # Section 63 (RFC 6761) validates it.  Only one candidate value.
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.integration
    def test_multiple_emails_produce_multiple_candidates(self):
        """Two different emails → multiple candidates with different values → AMBIGUOUS."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("a@b.com and c@d.org", contract)

        # Two different canonical values from two recognitions
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None
        assert len(result.candidates) >= 2
