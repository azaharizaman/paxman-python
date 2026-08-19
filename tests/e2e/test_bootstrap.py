from __future__ import annotations

import pytest

import paxman
from paxman.capabilities import Email
from paxman.core.discovery import reset_registry
from paxman.core.domain import Resolution


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_registry()
    yield
    reset_registry()


@pytest.mark.e2e
def test_bootstrap_then_canonicalize_round_trip() -> None:
    """register_all_shipped() is a complete bootstrap: pipeline resolves."""
    paxman.register_all_shipped()
    contract = Email.create_contract()
    result = paxman.canonicalize("user@Example.COM", contract)
    assert result.status is Resolution.SUCCESS
    assert result.canonicalized_value == "user@example.com"
