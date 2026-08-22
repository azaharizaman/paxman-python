"""Tests for IBAN recognition grammar (scaffold)."""

import pytest

from paxman.capabilities.IBAN.grammar.iban_recognition import (
    IBANRecognition,
)
from paxman.core.domain import Grammar


@pytest.mark.capability
class TestIBANRecognition:
    """Grammar: iban_recognition."""

    def setup_method(self) -> None:
        self.grammar: Grammar = IBANRecognition()

    def test_semantics(self) -> None:
        assert self.grammar.semantics == "iban_recognition"

    def test_single_value_false(self) -> None:
        assert self.grammar.single_value is False

    def test_recognize_returns_empty(self) -> None:
        assert self.grammar.recognize("anything") == []
