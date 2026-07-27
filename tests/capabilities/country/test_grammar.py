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


from paxman.capabilities.Country.grammar.numeric_recognition import NumericGrammar


class TestNumericGrammar:
    """Tests for NumericGrammar."""

    def setup_method(self) -> None:
        self.grammar = NumericGrammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds numeric pattern."""
        results = self.grammar.recognize("840")
        assert len(results) == 1
        assert results[0].shape == "numeric"
        assert results[0].value == "840"

    def test_recognizes_single_digit(self) -> None:
        """Edge case: single digit."""
        results = self.grammar.recognize("4")
        assert len(results) == 1
        assert results[0].value == "4"

    def test_recognizes_two_digits(self) -> None:
        """Edge case: two digits."""
        results = self.grammar.recognize("82")
        assert len(results) == 1
        assert results[0].value == "82"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  840  ")
        assert len(results) == 1
        assert results[0].value == "840"

    def test_preserves_leading_zeros(self) -> None:
        """Edge case: leading zeros are preserved."""
        results = self.grammar.recognize("004")
        assert len(results) == 1
        assert results[0].value == "004"

    def test_rejects_four_digits(self) -> None:
        """Grammar does not match 4+ digits."""
        results = self.grammar.recognize("1234")
        assert len(results) == 0

    def test_rejects_letters(self) -> None:
        """Grammar does not match letters."""
        results = self.grammar.recognize("abc")
        assert len(results) == 0

    def test_rejects_alphanumeric(self) -> None:
        """Grammar does not match alphanumeric."""
        results = self.grammar.recognize("12a")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "numeric_recognition"


from paxman.capabilities.Country.grammar.name_recognition import NameGrammar


class TestNameGrammar:
    """Tests for NameGrammar."""

    def setup_method(self) -> None:
        self.grammar = NameGrammar()

    def test_recognizes_full_name(self) -> None:
        """Happy path: grammar finds name pattern."""
        results = self.grammar.recognize("United States")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "United States"

    def test_recognizes_unicode(self) -> None:
        """Edge case: Unicode input."""
        results = self.grammar.recognize("马来西亚")
        assert len(results) == 1
        assert results[0].value == "马来西亚"

    def test_recognizes_alpha2(self) -> None:
        """Design note: name grammar also matches alpha2 shapes."""
        results = self.grammar.recognize("US")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "US"

    def test_recognizes_alpha3(self) -> None:
        """Design note: name grammar also matches alpha3 shapes."""
        results = self.grammar.recognize("USA")
        assert len(results) == 1
        assert results[0].shape == "name"

    def test_recognizes_numeric(self) -> None:
        """Design note: name grammar also matches numeric shapes."""
        results = self.grammar.recognize("840")
        assert len(results) == 1
        assert results[0].shape == "name"

    def test_preserves_case(self) -> None:
        """Edge case: original case is preserved."""
        results = self.grammar.recognize("united states")
        assert len(results) == 1
        assert results[0].value == "united states"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  Burma  ")
        assert len(results) == 1
        assert results[0].value == "Burma"

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "name_recognition"
