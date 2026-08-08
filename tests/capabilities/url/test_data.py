"""Tests for the generated UTS #46 IDNA mapping data module."""

from pathlib import Path

import pytest

from paxman.capabilities.URL.rules.data.idna_uts46_mapping import (
    IDNA_MAPPED,
    IDNA_STATUS,
    IDNA_VERSION,
)

pytestmark = [pytest.mark.capability, pytest.mark.url]

_MODULE_PATH = (
    Path(__file__).parents[3]
    / "paxman"
    / "capabilities"
    / "URL"
    / "rules"
    / "data"
    / "idna_uts46_mapping.py"
)


def test_version_constant() -> None:
    """IDNA_VERSION is pinned to UTS #46 15.1.0."""
    assert IDNA_VERSION == "15.1.0"


def test_key_rows() -> None:
    """Spot-check the vendored tables against UTS #46 15.1.0."""
    # ASCII uppercase case-folds: A is mapped to a, not valid.
    assert IDNA_STATUS["0041"] == "mapped"
    assert IDNA_MAPPED["0041"] == "0061"
    # ß is a UTS #46 deviation; it maps to ss.
    assert IDNA_STATUS["00DF"] == "deviation"
    assert IDNA_MAPPED["00DF"] == "0073 0073"
    # Control characters are disallowed under STD3 processing.
    assert IDNA_STATUS["0000..002C"] == "disallowed_STD3_valid"
    # A reserved code point is plainly disallowed.
    assert IDNA_STATUS["04C0"] == "disallowed"
    # ü (U+00FC) is valid and stays: münchen punycodes to xn--mnchen-3ya.
    assert IDNA_STATUS["00F8..00FF"] == "valid"
    assert IDNA_STATUS["00B7"] == "valid"  # MIDDLE DOT


def test_module_docstring_records_regeneration() -> None:
    """The docstring records the regeneration command (D13 auditable)."""
    assert (
        "uv run python tools/regenerate_idna_uts46_data.py"
        in _MODULE_PATH.read_text(encoding="utf-8")
    )


def test_no_output_format_token() -> None:
    """The generated data module must not contain the output_format token."""
    assert "output_format" not in _MODULE_PATH.read_text(encoding="utf-8")
