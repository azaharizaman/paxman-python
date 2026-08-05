"""Tests for capability exports."""

from __future__ import annotations

import pytest

from paxman.capabilities import ISBN, Email, Phone


class TestCapabilityExports:
    @pytest.mark.unit
    def test_email_capability_importable(self) -> None:
        """Email capability is importable from paxman.capabilities."""
        assert Email is not None

    @pytest.mark.unit
    def test_email_capability_name(self) -> None:
        """Email capability has correct name."""
        assert Email.name == "email"


class TestPhoneCapabilityExports:
    @pytest.mark.unit
    def test_phone_capability_importable(self) -> None:
        """Phone capability is importable from paxman.capabilities."""
        assert Phone is not None

    @pytest.mark.unit
    def test_phone_capability_name(self) -> None:
        """Phone capability has correct name."""
        assert Phone.name == "phone"


class TestISBNCapabilityExports:
    @pytest.mark.unit
    def test_isbn_capability_importable(self) -> None:
        """ISBN capability is importable from paxman.capabilities."""
        assert ISBN is not None

    @pytest.mark.unit
    def test_isbn_capability_name(self) -> None:
        """ISBN capability has correct name."""
        assert ISBN.name == "isbn"
