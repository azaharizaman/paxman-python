"""Span exposure: the public result should surface recognition spans.

The recognition pipeline is span-aware internally (``RecognitionMatch`` /
``RecognizedRep`` carry half-open ``[start, end)`` character ranges), but the
public ``ExecutionResult`` and ``Candidate`` previously dropped that
information. These tests pin the span-exposure contract end to end.
"""

from __future__ import annotations

import pytest

from paxman.api import canonicalize
from paxman.capabilities import Country, Date
from paxman.core.discovery import register_capability, reset_registry


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    reset_registry()
    yield
    reset_registry()


@pytest.mark.integration
def test_candidate_carries_recognition_span() -> None:
    """The winning candidate exposes the span the grammar matched."""
    register_capability(Date())
    contract = Date.create_contract()
    result = canonicalize("2026-01-15", contract)
    assert result.status.name == "SUCCESS"
    assert len(result.candidates) == 1
    assert result.candidates[0].span == (0, 10)


@pytest.mark.integration
def test_execution_result_span_is_winning_candidate_span() -> None:
    """ExecutionResult.span mirrors the (single) resolved candidate's span."""
    register_capability(Country())
    contract = Country.create_contract()
    result = canonicalize("US", contract)
    assert result.status.name == "SUCCESS"
    assert result.span == (0, 2)
    assert result.span == result.candidates[0].span


@pytest.mark.integration
def test_ambiguous_result_span_is_populated() -> None:
    """Even on AMBIGUOUS the result span is the first candidate's span."""
    register_capability(Date())
    contract = Date.create_contract()
    result = canonicalize("01/02/2026", contract)
    assert result.status.name == "AMBIGUOUS"
    assert result.span is not None
    assert result.span == result.candidates[0].span
