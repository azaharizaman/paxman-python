"""Tests for Country recognition grammars."""

from paxman.capabilities.Country.grammar.alpha2_recognition import Alpha2Grammar
from paxman.capabilities.Country.grammar.alpha3_recognition import Alpha3Grammar
from paxman.capabilities.Country.grammar.name_recognition import NameGrammar
from paxman.capabilities.Country.grammar.numeric_recognition import NumericGrammar


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


class TestNameGrammar:
    """Tests for NameGrammar (lookup-table-based recognition)."""

    def setup_method(self) -> None:
        self.grammar = NameGrammar()

    def test_recognizes_full_name(self) -> None:
        """Happy path: grammar resolves ISO English name to canonical form."""
        results = self.grammar.recognize("United States")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "United States"

    def test_recognizes_variant(self) -> None:
        """Variant names resolve to canonical ISO name."""
        results = self.grammar.recognize("USA")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "United States"

    def test_recognizes_alpha2_as_name(self) -> None:
        """Alpha-2-like name 'US' resolves to canonical 'United States'."""
        results = self.grammar.recognize("US")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "United States"

    def test_recognizes_lowercase(self) -> None:
        """Lowercase input still resolves correctly."""
        results = self.grammar.recognize("canada")
        assert len(results) == 1
        assert results[0].value == "Canada"

    def test_recognizes_mixed_case(self) -> None:
        """Mixed case input resolves correctly."""
        results = self.grammar.recognize("fRAnce")
        assert len(results) == 1
        assert results[0].value == "France"

    def test_recognizes_with_whitespace(self) -> None:
        """Whitespace is trimmed and collapsed."""
        results = self.grammar.recognize("  United   Kingdom  ")
        assert len(results) == 1
        assert results[0].value == "United Kingdom"

    def test_recognizes_with_accents(self) -> None:
        """Accented input is normalized and resolved."""
        results = self.grammar.recognize("Côte d'Ivoire")
        assert len(results) == 1
        assert results[0].value == "Côte d'Ivoire"

    def test_recognizes_chinese_name(self) -> None:
        """Chinese names resolve to ISO English name."""
        results = self.grammar.recognize("马来西亚")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "Malaysia"

    def test_recognizes_chinese_name_simple(self) -> None:
        """Chinese name '中国' resolves to 'China'."""
        results = self.grammar.recognize("中国")
        assert len(results) == 1
        assert results[0].value == "China"

    def test_recognizes_historical_name(self) -> None:
        """Historical name resolves to historical canonical form."""
        results = self.grammar.recognize("Burma")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "BURMA"

    def test_recognizes_historical_ussr(self) -> None:
        """Historical name 'USSR' resolves to 'USSR'."""
        results = self.grammar.recognize("USSR")
        assert len(results) == 1
        assert results[0].value == "USSR"

    def test_recognizes_synonym_via_english_table(self) -> None:
        """Synonym 'Holland' resolves to 'Netherlands' via English table."""
        results = self.grammar.recognize("Holland")
        assert len(results) == 1
        assert results[0].value == "Netherlands"

    def test_rejects_numeric(self) -> None:
        """Numeric input is not a name pattern."""
        results = self.grammar.recognize("840")
        assert len(results) == 0

    def test_rejects_unknown_name(self) -> None:
        """Unknown name returns empty list."""
        results = self.grammar.recognize("XYZ")
        assert len(results) == 0

    def test_rejects_gibberish(self) -> None:
        """Gibberish input returns empty list."""
        results = self.grammar.recognize("asdfghjkl")
        assert len(results) == 0

    def test_rejects_partial_name(self) -> None:
        """Partial name not in any table returns empty list."""
        results = self.grammar.recognize("United")
        assert len(results) == 0

    def test_rejects_empty_string(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_rejects_whitespace_only(self) -> None:
        """Whitespace-only input returns empty list."""
        results = self.grammar.recognize("   ")
        assert results == []

    def test_strips_punctuation(self) -> None:
        """Punctuation is stripped during normalization."""
        results = self.grammar.recognize("U.S.A.")
        assert len(results) == 1
        assert results[0].value == "United States"

    def test_strips_apostrophes(self) -> None:
        """Apostrophes are stripped during normalization."""
        results = self.grammar.recognize("Cote d'Ivoire")
        assert len(results) == 1
        assert results[0].value == "Côte d'Ivoire"

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "name_recognition"
