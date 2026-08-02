"""Tests for the installed package contract (pyproject [build-system])."""

from __future__ import annotations

from importlib import metadata

import pytest


class TestPackageInstall:
    @pytest.mark.unit
    def test_package_importable(self) -> None:
        import paxman

        assert paxman.__file__ is not None

    @pytest.mark.unit
    def test_package_metadata_present(self) -> None:
        assert metadata.version("paxman")

    @pytest.mark.unit
    def test_package_metadata_matches_pyproject(self) -> None:
        assert metadata.version("paxman") == "0.1.0"
