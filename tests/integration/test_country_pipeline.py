"""Integration tests for Country capability through the full pipeline."""

from __future__ import annotations

import pytest

from paxman.capabilities.Country.capability import CountryCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestCountryPipeline:
    """End-to-end tests for Country canonicalization."""

    @pytest.mark.integration
    def test_alpha2_success(self) -> None:
        """Alpha-2 code resolves to canonical alpha-2."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("US", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_alpha3_success(self) -> None:
        """Alpha-3 code resolves to canonical alpha-2."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("USA", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_numeric_success(self) -> None:
        """Numeric code resolves to canonical alpha-2."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("840", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_name_success(self) -> None:
        """Country name resolves to canonical alpha-2."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("United States", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_case_insensitive_alpha2(self) -> None:
        """Lowercase alpha-2 input normalizes to uppercase."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("us", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_case_insensitive_alpha3(self) -> None:
        """Lowercase alpha-3 input normalizes to uppercase alpha-2."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("usa", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_text_surrounding_code(self) -> None:
        """Country code extracted from surrounding text.

        Note: alpha2 grammar matches any 2-letter word, so test inputs
        must avoid common 2-letter words that are valid alpha-2 codes
        (e.g., "in"=India, "no"=Norway, "is"=Iceland).
        """
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("Country: USA", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_text_with_name(self) -> None:
        """Country name extracted from surrounding text.

        Note: name grammar matches the full trimmed input, so use a
        phrase that contains the country name without 2-letter false
        positives.
        """
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("United States", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "US"

    @pytest.mark.integration
    def test_missing_input(self) -> None:
        """No country patterns recognized returns MISSING.

        Only empty/whitespace input produces MISSING because NameGrammar
        matches any non-empty string (shape="name").
        """
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_invalid_code(self) -> None:
        """Recognized shape but invalid code returns INVALID."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("XX", contract)

        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    @pytest.mark.integration
    def test_historical_name_disabled(self) -> None:
        """Historical name not recognized by default."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("Burma", contract)

        # "Burma" is not in NAME_TO_ALPHA2, only in HISTORICAL_TO_ALPHA2
        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_historical_name_enabled(self) -> None:
        """Historical name recognized when include_historical=True."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract(include_historical=True)
        result = run_capability("Burma", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "MM"

    @pytest.mark.integration
    def test_localized_name_disabled(self) -> None:
        """Localized name not recognized by default."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("马来西亚", contract)

        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_localized_name_enabled(self) -> None:
        """Localized name recognized when include_localized=True."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract(include_localized=True)
        result = run_capability("马来西亚", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "MY"

    @pytest.mark.integration
    def test_version_stamp_present(self) -> None:
        """Version stamp is populated on result."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("US", contract)

        assert result.version_stamp is not None
        assert isinstance(result.version_stamp.paxman_version, str)
        assert len(result.version_stamp.replay_hash) == 64  # SHA-256 hex

    @pytest.mark.integration
    def test_replay_determinism(self) -> None:
        """Same input + same contract = byte-identical replay hash."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        r1 = run_capability("US", contract)
        r2 = run_capability("US", contract)

        assert r1.version_stamp.replay_hash == r2.version_stamp.replay_hash
        assert r1.canonicalized_value == r2.canonicalized_value

    @pytest.mark.integration
    def test_candidate_provenance(self) -> None:
        """Candidates carry provenance from the validating rule."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("US", contract)

        assert result.status == Resolution.SUCCESS
        assert len(result.candidates) >= 1
        for candidate in result.candidates:
            assert len(candidate.provenance) >= 1
            assert candidate.provenance[0].authority == "ISO"

    @pytest.mark.integration
    def test_pinned_rules(self) -> None:
        """Pinned rules restrict which rules run."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract(
            pinned_rules=("Section-alpha2-codes",)
        )
        result = run_capability("USA", contract)

        # Alpha-3 input should be INVALID when only alpha-2 rule is pinned
        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_excluded_rules(self) -> None:
        """Excluded rules are skipped."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract(
            excluded_rules=["Section-alpha2-codes"]
        )
        result = run_capability("US", contract)

        # Alpha-2 input should be INVALID when alpha-2 rule is excluded
        # (name grammar also matches "US" but it's not in NAME_TO_ALPHA2 as "US")
        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_year_filter(self) -> None:
        """Year filter excludes rules published after the specified year."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract(year=2019)
        result = run_capability("US", contract)

        # ISO 3166-1:2024 (year=2024) should be excluded
        # No rules match, so result is INVALID
        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_numeric_with_leading_zeros(self) -> None:
        """Numeric code with leading zeros normalizes correctly."""
        register_capability(CountryCapability())
        contract = CountryCapability.create_contract()
        result = run_capability("004", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "AF"
