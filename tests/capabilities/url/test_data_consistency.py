"""Consistency checks for the generated UTS #46 IDNA mapping data module.

The generated module is a vendored snapshot of Unicode's
IdnaMappingTable.txt (UTS #46). These tests pin the module to the authority
it claims to ship:

- every mapping target must itself have a defined status (mapping closure —
  no dangling targets);
- every status value and every range token must be a shape UTS #46 emits;
- the committed snapshot header must record the same version as the module;
- regenerating from the snapshot must reproduce the module byte-for-byte.
"""

from __future__ import annotations

import bisect
import importlib.util
from pathlib import Path

import pytest

from paxman.capabilities.URL.rules.data.idna_uts46_mapping import (
    IDNA_MAPPED,
    IDNA_STATUS,
    IDNA_VERSION,
)

pytestmark = [pytest.mark.capability, pytest.mark.url]

_REPO_ROOT = Path(__file__).parents[3]
_DATA_DIR = _REPO_ROOT / "paxman" / "capabilities" / "URL" / "rules" / "data"

_VALID_STATUSES = frozenset(
    {
        "valid",
        "mapped",
        "deviation",
        "ignored",
        "disallowed",
        "disallowed_STD3_valid",
        "disallowed_STD3_mapped",
    }
)

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _interval(token: str) -> tuple[int, int]:
    """Return the inclusive [start, end] code point interval of a token."""
    if ".." in token:
        start, _, end = token.partition("..")
        return int(start, 16), int(end, 16)
    value = int(token, 16)
    return value, value


def test_every_mapping_target_is_a_known_codepoint() -> None:
    """Every hex target in IDNA_MAPPED has a defined status (closure)."""
    intervals = sorted((_interval(token), token) for token in IDNA_STATUS)
    starts = [interval[0][0] for interval in intervals]
    targets = sorted(
        {int(target, 16) for value in IDNA_MAPPED.values() for target in value.split()}
    )
    uncovered = [
        target for target in targets if not _covered(target, starts, intervals)
    ]
    assert not uncovered, (
        "mapping targets with no defined status: "
        f"{[f'{target:04X}' for target in uncovered]}"
    )


def _covered(
    code_point: int,
    starts: list[int],
    intervals: list[tuple[tuple[int, int], str]],
) -> bool:
    """Whether a code point falls inside any shipped status interval."""
    index = bisect.bisect_right(starts, code_point) - 1
    if index < 0:
        return False
    (start, end), _status = intervals[index]
    return code_point <= end


def test_statuses_are_valid_uts46() -> None:
    """Every key is a 4-6 hex digit token (or range) with a UTS #46 status."""
    for token, status in IDNA_STATUS.items():
        assert status in _VALID_STATUSES, f"{token!r} has status {status!r}"
        start_text, sep, end_text = token.partition("..")
        assert 4 <= len(start_text) <= 6, f"{token!r}: {start_text!r} is not 4-6 hex"
        assert all(char in _HEX_DIGITS for char in start_text), (
            f"{token!r}: {start_text!r} is not hex"
        )
        if sep:
            assert 4 <= len(end_text) <= 6, f"{token!r}: {end_text!r} is not 4-6 hex"
            assert all(char in _HEX_DIGITS for char in end_text), (
                f"{token!r}: {end_text!r} is not hex"
            )
            assert _interval(token)[0] <= _interval(token)[1]


def test_snapshot_matches_module() -> None:
    """The snapshot header records UTS #46 15.1.0, agreeing with the module."""
    snapshot = (_DATA_DIR / "idna_uts46_mapping.txt").read_text(encoding="utf-8")
    assert "UTS #46" in snapshot
    assert f"# Version: {IDNA_VERSION}" in snapshot


def test_regeneration_is_idempotent() -> None:
    """render() reproduces the committed module byte-for-byte."""
    spec = importlib.util.spec_from_file_location(
        "regenerate_idna_uts46_data",
        _REPO_ROOT / "tools" / "regenerate_idna_uts46_data.py",
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    committed = (_DATA_DIR / "idna_uts46_mapping.py").read_text(encoding="utf-8")
    assert generator.render() == committed
