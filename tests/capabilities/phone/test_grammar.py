"""Tests for Phone recognition grammars."""

from paxman.capabilities.Phone.grammar.e164_recognition import E164Grammar
from paxman.capabilities.Phone.grammar.international_00_recognition import (
    International00Grammar,
)
from paxman.capabilities.Phone.grammar.national_recognition import NationalGrammar
from paxman.capabilities.Phone.grammar.tel_uri_recognition import TelUriGrammar


class TestE164Grammar:
    """Tests for E164Grammar."""

    def setup_method(self) -> None:
        self.grammar = E164Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds e164 pattern."""
        results = self.grammar.recognize("+15551234567")
        assert len(results) == 1
        assert results[0].shape == "e164"
        assert results[0].value == "15551234567"

    def test_recognizes_with_spaces(self) -> None:
        """Edge case: spaces between digit groups."""
        results = self.grammar.recognize("+1 555 123 4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_with_dashes(self) -> None:
        """Edge case: dashes between digit groups."""
        results = self.grammar.recognize("+44-20-7946-0958")
        assert len(results) == 1
        assert results[0].value == "442079460958"

    def test_recognizes_with_dots(self) -> None:
        """Edge case: dots between digit groups."""
        results = self.grammar.recognize("+1.555.123.4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_with_parens(self) -> None:
        """Edge case: parentheses around area code."""
        results = self.grammar.recognize("+1 (555) 123-4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_in_text(self) -> None:
        """Input contains e164 number within surrounding text."""
        results = self.grammar.recognize("Call me at +15551234567 today")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_multiple(self) -> None:
        """Input contains multiple e164 matches."""
        results = self.grammar.recognize("+15551234567 or +442079460958")
        assert len(results) == 2

    def test_ignores_number_without_plus(self) -> None:
        """Grammar does not match numbers without the + prefix."""
        results = self.grammar.recognize("15551234567")
        assert len(results) == 0

    def test_ignores_national_format(self) -> None:
        """Grammar does not match national (no +) formatting."""
        results = self.grammar.recognize("(555) 123-4567")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "e164_recognition"


class TestTelUriGrammar:
    """Tests for TelUriGrammar."""

    def setup_method(self) -> None:
        self.grammar = TelUriGrammar()

    def test_recognizes_global_number(self) -> None:
        """Happy path: tel: URI with global number."""
        results = self.grammar.recognize("tel:+15551234567")
        assert len(results) == 1
        assert results[0].shape == "rfc3966"
        assert results[0].value == "15551234567"

    def test_recognizes_with_dashes(self) -> None:
        """Edge case: dashes in URI number."""
        results = self.grammar.recognize("tel:+1-201-555-0123")
        assert len(results) == 1
        assert results[0].value == "12015550123"

    def test_recognizes_with_extension(self) -> None:
        """Edge case: ;ext= parameter."""
        results = self.grammar.recognize("tel:+15551234567;ext=890")
        assert len(results) == 1
        assert results[0].value == "15551234567"
        assert results[0].extension == "890"

    def test_recognizes_in_text(self) -> None:
        """Input contains tel: URI within surrounding text."""
        results = self.grammar.recognize("Reach me at tel:+15551234567 now")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_uppercase_scheme(self) -> None:
        """Edge case: uppercase TEL: scheme."""
        results = self.grammar.recognize("TEL:+15551234567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_ignores_plain_number(self) -> None:
        """Grammar does not match numbers without tel: scheme."""
        results = self.grammar.recognize("+15551234567")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "tel_uri_recognition"


class TestInternational00Grammar:
    """Tests for International00Grammar."""

    def setup_method(self) -> None:
        self.grammar = International00Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: 00-prefixed international number."""
        results = self.grammar.recognize("00 44 20 7946 0958")
        assert len(results) == 1
        assert results[0].shape == "e164"
        assert results[0].value == "442079460958"

    def test_recognizes_compact(self) -> None:
        """Edge case: compact digits."""
        results = self.grammar.recognize("00442079460958")
        assert len(results) == 1
        assert results[0].value == "442079460958"

    def test_recognizes_in_text(self) -> None:
        """Input contains 00 number within surrounding text."""
        results = self.grammar.recognize("Dial 00 44 20 7946 0958 from abroad")
        assert len(results) == 1
        assert results[0].value == "442079460958"

    def test_ignores_number_with_plus(self) -> None:
        """Grammar does not match +-prefixed numbers."""
        results = self.grammar.recognize("+442079460958")
        assert len(results) == 0

    def test_ignores_single_zero(self) -> None:
        """Grammar does not match a single leading zero."""
        results = self.grammar.recognize("0 44 20 7946 0958")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "international_00_recognition"


class TestNationalGrammar:
    """Tests for NationalGrammar."""

    def setup_method(self) -> None:
        self.grammar = NationalGrammar()

    def test_recognizes_parenthesized(self) -> None:
        """Happy path: (NPA) NXX-XXXX format."""
        results = self.grammar.recognize("(555) 123-4567")
        assert len(results) == 1
        assert results[0].shape == "national"
        assert results[0].value == "5551234567"

    def test_recognizes_dashes(self) -> None:
        """Edge case: NPA-NXX-XXXX format."""
        results = self.grammar.recognize("555-123-4567")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_recognizes_dots(self) -> None:
        """Edge case: NPA.NXX.XXXX format."""
        results = self.grammar.recognize("555.123.4567")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_recognizes_spaces(self) -> None:
        """Edge case: space-separated format."""
        results = self.grammar.recognize("555 123 4567")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_recognizes_with_trunk(self) -> None:
        """Edge case: leading trunk 1 preserved."""
        results = self.grammar.recognize("1-555-123-4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_trunk_with_parens(self) -> None:
        """Edge case: trunk with parenthesized NPA."""
        results = self.grammar.recognize("1 (555) 123-4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_in_text(self) -> None:
        """Input contains national number within surrounding text."""
        results = self.grammar.recognize("Call (555) 123-4567 today")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_ignores_international(self) -> None:
        """Grammar does not match +-prefixed numbers."""
        results = self.grammar.recognize("+15551234567")
        assert len(results) == 0

    def test_ignores_short_number(self) -> None:
        """Grammar does not match 7-digit local-only numbers."""
        results = self.grammar.recognize("555-1234")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "national_recognition"
