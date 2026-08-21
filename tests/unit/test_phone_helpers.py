"""Coverage for Phone grammar helper strip_separators (both branches)."""

from __future__ import annotations

import pytest

from paxman.capabilities.Phone.grammar._common import strip_separators
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

pytestmark = pytest.mark.unit


def test_strip_separators_plus_true() -> None:
    """PLUS branch strips plus and separators."""
    # All four grammars re-export the same shared helper — verify identity.
    assert e164_strip is strip_separators
    assert intl_strip is strip_separators
    assert national_strip is strip_separators
    assert tel_strip is strip_separators
    assert strip_separators("+1 (555) 123-4567", plus=True) == "15551234567"
    assert strip_separators("00 44 20 7946 0958", plus=True) == "00442079460958"
    assert strip_separators("tel:+1-201-555-0123", plus=True) == "tel:12015550123"


def test_strip_separators_plus_false() -> None:
    """Non-plus branch strips only separators, keeps plus."""
    # Directly exercises the fallback line `return value.translate(...)` in _common.py.
    assert strip_separators("a (b) - c", plus=False) == "abc"
    assert strip_separators("+1 (555) 123-4567", plus=False) == "+15551234567"
    assert strip_separators("00 44 20 7946 0958", plus=False) == "00442079460958"
    assert strip_separators("(555) 123-4567", plus=False) == "5551234567"
    assert strip_separators("tel:+1-201-555-0123", plus=False) == "tel:+12015550123"
