"""End-to-end tests for the public canonicalize() API."""

from __future__ import annotations

import pytest

from paxman.api import canonicalize
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.Phone.capability import PhoneCapability
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

            @property
            def output_format(self) -> str | None:
                return None

            def as_dict(self) -> dict:
                return {"capability_name": "nonexistent"}

        with pytest.raises(CapabilityError, match="Unknown capability"):
            canonicalize("test", FakeContract())


class TestDateCapabilityE2E:
    """End-to-end tests for Date capability via public API."""

    @pytest.mark.e2e
    def test_iso_date(self) -> None:
        """ISO date canonicalization via public API."""
        register_capability(DateCapability())
        contract = DateCapability.create_contract()
        result = canonicalize("2026-01-15", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-01-15"

    @pytest.mark.e2e
    def test_date_ambiguity(self) -> None:
        """Ambiguous date returns AMBIGUOUS status."""
        register_capability(DateCapability())
        contract = DateCapability.create_contract()
        result = canonicalize("07/02/2026", contract)
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None


class TestCanonicalizePhone:
    """End-to-end tests for the Phone capability through paxman.canonicalize."""

    @pytest.mark.e2e
    def test_canonicalize_phone_success(self) -> None:
        """Full happy path through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("+44 20 7946 0958", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+442079460958"

    @pytest.mark.e2e
    def test_canonicalize_phone_national(self) -> None:
        """National number with default_country through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(default_country="US")
        result = canonicalize("(555) 234-5678", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+15552345678"

    @pytest.mark.e2e
    def test_canonicalize_phone_missing(self) -> None:
        """No phone pattern recognized."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("no phone number here", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_canonicalize_phone_invalid(self) -> None:
        """Unassigned country code is invalid."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("+999123456789", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.e2e
    def test_canonicalize_phone_with_options(self) -> None:
        """output_format option through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(output_format="rfc3966")
        result = canonicalize("+15551234567", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "tel:+15551234567"
