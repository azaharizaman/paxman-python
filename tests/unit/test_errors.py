import pytest

from paxman.core.errors import (
    CapabilityError,
    ContractError,
    PaxmanError,
    RecognitionError,
    ValidationError,
)


class TestExceptionHierarchy:
    @pytest.mark.unit
    def test_paxman_error_is_base(self):
        assert issubclass(ContractError, PaxmanError)
        assert issubclass(CapabilityError, PaxmanError)
        assert issubclass(RecognitionError, PaxmanError)
        assert issubclass(ValidationError, PaxmanError)

    @pytest.mark.unit
    def test_paxman_error_is_exception(self):
        assert issubclass(PaxmanError, Exception)

    @pytest.mark.unit
    def test_recognition_error_stores_rule(self):
        original = ValueError("bad regex")
        err = RecognitionError(
            rule="standard_recognition",
            message="invalid pattern",
            original_error=original,
        )
        assert err.rule == "standard_recognition"
        assert err.original_error is original
        assert "standard_recognition" in str(err)

    @pytest.mark.unit
    def test_validation_error_stores_rule(self):
        original = KeyError("missing")
        err = ValidationError(
            rule="rfc_5322",
            message="lookup failed",
            original_error=original,
        )
        assert err.rule == "rfc_5322"
        assert err.original_error is original
        assert "rfc_5322" in str(err)

    @pytest.mark.unit
    def test_contract_error_message(self):
        err = ContractError("missing required field")
        assert "missing required field" in str(err)

    @pytest.mark.unit
    def test_capability_error_message(self):
        err = CapabilityError("unknown capability: foo")
        assert "unknown capability: foo" in str(err)
