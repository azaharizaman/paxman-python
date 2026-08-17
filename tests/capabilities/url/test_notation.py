"""Tests for URL notation."""

import dataclasses

import pytest

from paxman.capabilities.URL.notation import URLNotation

pytestmark = [pytest.mark.capability, pytest.mark.url]


def test_fields() -> None:
    """URLNotation stores the single text field."""
    assert URLNotation(text="https://example.com").text == "https://example.com"


def test_frozen() -> None:
    """Assigning a field raises FrozenInstanceError."""
    notation = URLNotation(text="https://example.com")
    with pytest.raises(dataclasses.FrozenInstanceError):
        notation.text = "https://other.example"  # type: ignore[misc]


def test_slots() -> None:
    """Slots enforced: no per-instance __dict__ (Traps §4.3)."""
    assert not hasattr(URLNotation(text="x"), "__dict__")


def test_empty_text_valid() -> None:
    """Shape-only notation accepts empty text; validity is the rule's job (D7)."""
    assert URLNotation(text="").text == ""
