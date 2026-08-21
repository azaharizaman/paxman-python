"""Coverage for Phone grammar helper strip_separators (both branches)."""

from __future__ import annotations

from paxman.capabilities.Phone.grammar.e164_recognition import (
    strip_separators as e164_strip,
)
from paxman.capabilities.Phone.grammar.international_00_recognition import (
    strip_separators as intl_strip,
)
from paxman.capabilities.Phone.grammar.national_recognition import (
    strip_separators as national_strip,
)
from paxman.capabilities.Phone.grammar.tel_uri_recognition import (
    strip_separators as tel_strip,
)


def test_strip_separators_plus_true() -> None:
    """PLUS branch strips plus and separators."""
    assert e164_strip("+1 (555) 123-4567", plus=True) == "15551234567"
    assert intl_strip("00 44 20 7946 0958", plus=True) == "00442079460958"
    assert tel_strip("tel:+1-201-555-0123", plus=True) == "tel:12015550123"


def test_strip_separators_plus_false() -> None:
    """Non-plus branch strips only separators, keeps plus."""
    # Directly exercises the fallback line `return value.translate(...)` in each file.
    assert e164_strip("a (b) - c", plus=False) == "abc"
    assert e164_strip("+1 (555) 123-4567", plus=False) == "+15551234567"
    assert intl_strip("00 44 20 7946 0958", plus=False) == "00442079460958"
    assert national_strip("(555) 123-4567", plus=False) == "5551234567"
    expected = "tel:+1-201-555-0123".translate(str.maketrans("", "", " ().-"))
    assert tel_strip("tel:+1-201-555-0123", plus=False) == expected
