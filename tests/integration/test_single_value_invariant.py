"""Integration tests for the single-value invariant (ADR-0004).

A single canonicalize() call must resolve at most one canonical value. Input
containing more than one distinct entity (mention) that resolves to more than
one distinct value fails fast with ``MultipleMentionsError`` instead of
returning a misleading ``AMBIGUOUS`` status. Genuine single-mention ambiguity
(one span, multiple specs) stays ``AMBIGUOUS``, and coincidentally identical
multi-mention input still resolves to its single value (``SUCCESS``).
"""

import pytest

from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.core.errors import MultipleMentionsError
from paxman.engine.orchestrator import run_capability


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
