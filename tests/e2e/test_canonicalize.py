"""End-to-end tests for the public canonicalize() API."""

from __future__ import annotations

import pytest

from paxman.api import canonicalize
from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.core.errors import CapabilityError


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


class TestCanonicalize:
    @pytest.mark.e2e
    def test_standard_email(self):
        """Standard email canonicalization via public API."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract()
        result = canonicalize("user@example.com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.e2e
    def test_obfuscated_email(self):
        """Obfuscated email canonicalization via public API."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract(include_obfuscated=True)
        result = canonicalize("user at example dot com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.e2e
    def test_localhost_email(self):
        """Localhost email canonicalization via public API."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract()
        result = canonicalize("admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.e2e
    def test_no_match_returns_missing(self):
        """Input with no email patterns returns MISSING."""
        register_capability(EmailCapability())

        contract = EmailCapability.create_contract()
        result = canonicalize("hello world", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None

    @pytest.mark.e2e
    def test_unknown_capability_raises_error(self):
        """Unknown capability name raises CapabilityError."""

        class FakeContract:
            @property
            def capability_name(self) -> str:
                return "nonexistent"

            @property
            def active_grammars(self) -> list[str]:
                return []

            @property
            def excluded_rules(self) -> list[str]:
                return []

            @property
            def year(self) -> int | None:
                return None

            def as_dict(self) -> dict:
                return {"capability_name": "nonexistent"}

        with pytest.raises(CapabilityError, match="Unknown capability"):
            canonicalize("test", FakeContract())
