"""Tests for capability exports."""

from __future__ import annotations

import pytest

from paxman.capabilities import Email


class TestCapabilityExports:
    @pytest.mark.unit
    def test_email_capability_importable(self) -> None:
        """Email capability is importable from paxman.capabilities."""
        assert Email is not None

    @pytest.mark.unit
    def test_email_capability_name(self) -> None:
        """Email capability has correct name."""
        assert Email.name == "email"
