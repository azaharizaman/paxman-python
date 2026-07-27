"""Tests for Country recognition grammars."""

import pytest
from paxman.capabilities.Country.grammar.alpha2_recognition import Alpha2Grammar


class TestAlpha2Grammar:
    """Tests for Alpha2Grammar."""

    def setup_method(self) -> None:
        self.grammar = Alpha2Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds alpha2 pattern."""
        results = self.grammar.recognize("US")
        assert len(results) == 1
        assert results[0].shape == "alpha2"
        assert results[0].value == "US"

    def test_recognizes_lowercase(self) -> None:
        """Edge case: lowercase input is uppercased."""
        results = self.grammar.recognize("gb")
        assert len(results) == 1
        assert results[0].value == "GB"

    def test_recognizes_mixed_case(self) -> None:
        """Edge case: mixed case input is uppercased."""
        results = self.grammar.recognize("Us")
        assert len(results) == 1
        assert results[0].value == "US"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  US  ")
        assert len(results) == 1
        assert results[0].value == "US"

    def test_recognizes_multiple(self) -> None:
        """Input contains multiple alpha2 matches."""
        results = self.grammar.recognize("US and GB")
        assert len(results) == 2

    def test_rejects_alpha3(self) -> None:
        """Grammar does not match 3-letter codes."""
        results = self.grammar.recognize("USA")
        assert len(results) == 0

    def test_rejects_numeric(self) -> None:
        """Grammar does not match digits."""
        results = self.grammar.recognize("12")
        assert len(results) == 0

    def test_rejects_single_letter(self) -> None:
        """Grammar does not match single letter."""
        results = self.grammar.recognize("U")
        assert len(results) == 0

    def test_rejects_long_string(self) -> None:
        """Grammar does not match strings > 2 chars."""
        results = self.grammar.recognize("United")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "alpha2_recognition"


from paxman.capabilities.Country.grammar.alpha3_recognition import Alpha3Grammar


class TestAlpha3Grammar:
    """Tests for Alpha3Grammar."""

    def setup_method(self) -> None:
        self.grammar = Alpha3Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds alpha3 pattern."""
        results = self.grammar.recognize("USA")
        assert len(results) == 1
        assert results[0].shape == "alpha3"
        assert results[0].value == "USA"

    def test_recognizes_lowercase(self) -> None:
        """Edge case: lowercase input is uppercased."""
        results = self.grammar.recognize("gbr")
        assert len(results) == 1
        assert results[0].value == "GBR"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  USA  ")
        assert len(results) == 1
        assert results[0].value == "USA"

    def test_recognizes_multiple(self) -> None:
        """Input contains multiple alpha3 matches."""
        results = self.grammar.recognize("USA GBR")
        assert len(results) == 2

    def test_rejects_alpha2(self) -> None:
        """Grammar does not match 2-letter codes."""
        results = self.grammar.recognize("US")
        assert len(results) == 0

    def test_rejects_numeric(self) -> None:
        """Grammar does not match digits."""
        results = self.grammar.recognize("123")
        assert len(results) == 0

    def test_rejects_long_string(self) -> None:
        """Grammar does not match strings > 3 chars."""
        results = self.grammar.recognize("United")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "alpha3_recognition"
