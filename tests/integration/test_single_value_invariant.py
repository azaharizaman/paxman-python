"""Integration tests for the single-value invariant (ADR-0004).

A single canonicalize() call must resolve at most one canonical value. Input
containing more than one distinct entity (mention) that resolves to more than
one distinct value fails fast with ``MultipleMentionsError`` instead of
returning a misleading ``AMBIGUOUS`` status. Genuine single-mention ambiguity
(one span, multiple specs) stays ``AMBIGUOUS``, and coincidentally identical
multi-mention input still resolves to its single value (``SUCCESS``).
"""

import pytest

from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import (
    Candidate,
    GrammarRule,
    RecognizedRep,
    Resolution,
)
from paxman.core.errors import MultipleMentionsError
from paxman.engine.orchestrator import _enforce_single_value_invariant, run_capability


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Reset the capability registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


class TestSingleValueInvariant:
    """Pipeline enforcement of one entity per call."""

    @pytest.mark.integration
    def test_multi_mention_divergent_raises(self) -> None:
        """Two distinct numbers in one call fail fast, not AMBIGUOUS."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        with pytest.raises(MultipleMentionsError) as exc_info:
            run_capability("+60164041945 and +60164041946", contract)
        assert "split" in str(exc_info.value)
        assert "+60164041945" in str(exc_info.value)
        assert "+60164041946" in str(exc_info.value)

    @pytest.mark.integration
    def test_single_mention_ambiguity_preserved(self) -> None:
        """One span with conflicting specs stays AMBIGUOUS (genuine)."""
        register_capability(DateCapability())
        contract = DateCapability.create_contract()
        result = run_capability("01/02/2026", contract)
        assert result.status == Resolution.AMBIGUOUS

    @pytest.mark.integration
    def test_duplicate_mention_same_value_succeeds(self) -> None:
        """Two copies of the same number still resolve to one value."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("+60164041945 and +60164041945", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+60164041945"

    @pytest.mark.integration
    def test_single_valid_input_unaffected(self) -> None:
        """A single entity resolves normally."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("+60164041945", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+60164041945"

    @pytest.mark.integration
    def test_overlapping_span_bridges_separate_clusters(self) -> None:
        """A span overlapping two clusters must merge them (connected component).

        Spans A=(0,5) and B=(10,15) are separate; C=(3,12) overlaps both. The
        three form one connected mention, so divergent values across them must
        NOT raise. The naive "first matching cluster only" loop would split
        them and falsely raise ``MultipleMentionsError``.
        """
        contract = CountryCapability.create_contract()

        def _make(grammar_name: str, start: int, end: int, value: str):
            rep = RecognizedRep(
                notation=grammar_name,
                contract=contract,
                grammar=GrammarRule(
                    capability_name="country", grammar_name=grammar_name
                ),
                start=start,
                end=end,
                raw_text="x" * (end - start),
            )
            cand = Candidate(
                value=value,
                recognition_rule=grammar_name,
                validation_rule="r",
                provenance=[],
                span=(start, end),
            )
            return (cand, rep)

        collected = [
            _make("alpha2_recognition", 0, 5, "US"),
            _make("alpha2_recognition", 10, 15, "GB"),
            _make("alpha2_recognition", 3, 12, "US"),
        ]
        _enforce_single_value_invariant(collected, {"alpha2_recognition": True})
