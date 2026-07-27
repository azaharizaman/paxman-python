"""Tests for VersionStamp dataclass."""

from __future__ import annotations

import pytest

from paxman.core.domain import VersionStamp


class TestVersionStamp:
    @pytest.mark.unit
    def test_immutable(self) -> None:
        vs = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        with pytest.raises(AttributeError):
            vs.paxman_version = "0.2.0"

    @pytest.mark.unit
    def test_equality(self) -> None:
        a = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        b = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        assert a == b

    @pytest.mark.unit
    def test_inequality(self) -> None:
        a = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        b = VersionStamp(paxman_version="0.1.0", replay_hash="def456")
        assert a != b

    @pytest.mark.unit
    def test_hashable(self) -> None:
        vs = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        assert hash(vs) is not None
