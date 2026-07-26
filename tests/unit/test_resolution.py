"""Tests for Resolution enum."""

from __future__ import annotations

import pytest

from paxman.core.domain import Resolution


class TestResolution:
    @pytest.mark.unit
    def test_has_missing(self) -> None:
        assert Resolution.MISSING.value == "missing"

    @pytest.mark.unit
    def test_has_invalid(self) -> None:
        assert Resolution.INVALID.value == "invalid"

    @pytest.mark.unit
    def test_has_success(self) -> None:
        assert Resolution.SUCCESS.value == "success"

    @pytest.mark.unit
    def test_has_ambiguous(self) -> None:
        assert Resolution.AMBIGUOUS.value == "ambiguous"

    @pytest.mark.unit
    def test_all_statuses(self) -> None:
        assert len(Resolution) == 4
