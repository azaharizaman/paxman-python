"""Tests for the built distribution (wheel) package contract."""

from __future__ import annotations

import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


class TestPackageInstall:
    @pytest.mark.unit
    def test_package_importable_from_wheel(self, tmp_path: Path) -> None:
        """Build the wheel, install it into a fresh venv, import from there.

        Validates the built distribution rather than the repository
        checkout: the wheel must actually contain the
        ``paxman.capabilities.Phone`` subpackage and be importable in
        isolation (no dev environment or source tree on sys.path).
        """
        venv_dir = tmp_path / "venv"
        wheel_dir = tmp_path / "dist"
        wheel_dir.mkdir()

        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        bin_dir = "Scripts" if os.name == "nt" else "bin"
        python_name = "python.exe" if os.name == "nt" else "python"
        venv_python = venv_dir / bin_dir / python_name

        # Build the wheel (build isolation fetches hatchling; paxman has no
        # runtime dependencies, so --no-deps is safe).
        subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "-w",
                str(wheel_dir),
                str(_REPO_ROOT),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        wheels = list(wheel_dir.glob("paxman-*.whl"))
        assert len(wheels) == 1

        # Install offline into the fresh environment and import from it.
        subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(wheels[0]),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            [
                str(venv_python),
                "-c",
                "import paxman, paxman.capabilities.Phone; print(paxman.__file__)",
            ],
            # A neutral cwd keeps the repository source tree off sys.path,
            # so the import must resolve from the installed wheel.
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
            text=True,
        )
        assert "site-packages" in result.stdout

    @pytest.mark.unit
    def test_package_metadata_present(self) -> None:
        assert metadata.version("paxman")

    @pytest.mark.unit
    def test_package_metadata_matches_pyproject(self) -> None:
        """Installed version must match the version declared in pyproject.toml."""
        pyproject = _REPO_ROOT / "pyproject.toml"
        declared = next(
            line.split("=")[1].strip().strip('"')
            for line in pyproject.read_text().splitlines()
            if line.strip().startswith("version =")
        )
        assert metadata.version("paxman") == declared
