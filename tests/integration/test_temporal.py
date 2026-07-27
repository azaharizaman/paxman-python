"""Tests for temporal (year-based) rule filtering."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry() -> Generator[None, None, None]:
    reset_registry()
    yield
    reset_registry()


class TestTemporalFiltering:
    @pytest.mark.integration
    def test_year_filters_out_future_rules(self) -> None:
        """Year=2007 excludes RFC 5322 (2008) and RFC 6761 (2012)."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(year=2007)
        result = run_capability("user@example.com", contract)

        # "user@example.com" IS recognized by standard grammar, but both rules
        # (RFC 5322 published 2008, RFC 6761 published 2012) are excluded by year=2007.
        # This means: recognized but no provenance validates → INVALID
        assert result.status == Resolution.INVALID
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_year_includes_matching_rules(self) -> None:
        """Year=2010 includes RFC 5322 (2008) but excludes RFC 6761 (2012)."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(year=2010)
        result = run_capability("user@example.com", contract)

        # RFC 5322 active, RFC 6761 excluded
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.integration
    def test_year_none_includes_all_rules(self) -> None:
        """No year pin → all rules active."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(year=None)
        result = run_capability("admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"
