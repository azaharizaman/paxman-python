"""Drift guard for Currency/Money generated tables (Item 6, M8)."""

from __future__ import annotations

import subprocess
import sys


def test_currency_data_not_drifted() -> None:
    proc = subprocess.run(
        [sys.executable, "tools/regenerate_currency_data.py", "--check"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"DRIFT: {proc.stderr or proc.stdout}\n"
        "Run: uv run python tools/regenerate_currency_data.py"
    )
