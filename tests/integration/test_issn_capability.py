"""Integration tests for ISSN capability — resolution map + pipeline (Task 7)."""

from __future__ import annotations

import pytest

import paxman
from paxman.capabilities.ISSN.capability import ISSNCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.core.errors import MultipleMentionsError


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestISSNResolutionMap:
    """Resolution map for ISSN per Task 7 table."""

    @pytest.mark.integration
    def test_bare_hyphenated_success(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("0317-8471", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "0317-8471"
        assert len(result.candidates) == 1
        assert result.candidates[0].value == "0317-8471"
        assert result.candidates[0].recognition_rule == "issn_recognition"
        assert result.candidates[0].validation_rule == "Section 4-issn-check-digit"
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"
        assert result.span == (0, 9)
        assert result.candidates[0].span == (0, 9)

    @pytest.mark.integration
    def test_compact_success(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("03178471", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "0317-8471"
        assert len(result.candidates) == 1
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"

    @pytest.mark.integration
    def test_label_success(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("ISSN 0317-8471", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "0317-8471"
        assert len(result.candidates) == 1
        assert result.candidates[0].recognition_rule == "issn_recognition"
        assert result.candidates[0].validation_rule == "Section 4-issn-check-digit"
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"
        # Span includes the label.
        assert result.span == (0, 14)
        assert result.candidates[0].span == (0, 14)
        # raw_text would be "ISSN 0317-8471" as per grammar — verify span length.
        assert result.span is not None
        assert result.span[1] - result.span[0] == len("ISSN 0317-8471")

    @pytest.mark.integration
    def test_x_fold_success(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("1050-124x", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "1050-124X"
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"

    @pytest.mark.integration
    def test_leading_zeros_success(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("0000-0019", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "0000-0019"
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"

    @pytest.mark.integration
    def test_compact_output(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract(output_format="compact")
        result = paxman.canonicalize("0317-8471", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "03178471"
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"

    @pytest.mark.integration
    def test_urn_output(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract(output_format="urn")
        result = paxman.canonicalize("0317-8471", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "urn:issn:0317-8471"
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"

    @pytest.mark.integration
    def test_invalid_check(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("0378-5954", contract)

        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0
        assert result.span is None

    @pytest.mark.integration
    def test_mid_x_invalid(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("12X4-5679", contract)

        # Grammar rejects mid X (strict pattern), so MISSING; INVALID also
        # acceptable per plan — assert not SUCCESS.
        assert result.status in (Resolution.INVALID, Resolution.MISSING)
        assert result.canonicalized_value is None

    @pytest.mark.integration
    def test_wrong_hyphen_missing(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("12-345679", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_no_digits_missing(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        result = paxman.canonicalize("call me at noon", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0
        assert result.span is None

    @pytest.mark.integration
    def test_two_distinct_ambiguous(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract()
        try:
            result = paxman.canonicalize("0317-8471 / 0378-5955", contract)
        except MultipleMentionsError:
            # single_value=True grammar raises fast — acceptable per plan.
            return
        # If engine returns AMBIGUOUS instead of raising.
        assert result.status == Resolution.AMBIGUOUS
        assert len(result.candidates) == 2
        assert {c.value for c in result.candidates} == {"0317-8471", "0378-5955"}

    @pytest.mark.integration
    def test_pinned_rule(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract(
            pinned_rules=["Section 4-issn-check-digit"]
        )
        result = paxman.canonicalize("0317-8471", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "0317-8471"
        assert result.candidates[0].provenance[0].specification_name == "ISO 3297:2022"

    @pytest.mark.integration
    def test_year_filter(self) -> None:
        register_capability(ISSNCapability())
        contract_2022 = ISSNCapability.create_contract(year=2022)
        result_2022 = paxman.canonicalize("0317-8471", contract_2022)

        assert result_2022.status == Resolution.SUCCESS
        assert result_2022.canonicalized_value == "0317-8471"

        # Need fresh registry after first freeze — fixture resets only between tests,
        # so reset manually for the second call within same test.
        reset_registry()
        register_capability(ISSNCapability())
        contract_2021 = ISSNCapability.create_contract(year=2021)
        result_2021 = paxman.canonicalize("0317-8471", contract_2021)

        assert result_2021.status == Resolution.INVALID
        assert result_2021.canonicalized_value is None
        assert len(result_2021.candidates) == 0

    @pytest.mark.integration
    def test_excluded_rule(self) -> None:
        register_capability(ISSNCapability())
        contract = ISSNCapability.create_contract(
            excluded_rules=["Section 4-issn-check-digit"]
        )
        result = paxman.canonicalize("0317-8471", contract)

        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0
        assert result.span is None
