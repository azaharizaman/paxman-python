"""Guards for removed legacy surfaces (architecture-review Near-Term 3).

Each test locks a removal: the surface must not reappear in source.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import paxman.core.domain

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_generic_notation_alias_removed() -> None:
    """`Notation = list[str]` alias is gone from core and its export."""
    assert not hasattr(paxman.core.domain, "Notation")
    assert not hasattr(paxman.core, "Notation")


@pytest.mark.unit
def test_no_as_list_bridging_in_source() -> None:
    """No paxman source module defines as_list() bridging."""
    offenders = [
        p.as_posix()
        for p in (_REPO_ROOT / "paxman").rglob("*.py")
        if re.search(r"\bdef as_list\b", p.read_text(encoding="utf-8"))
    ]
    assert offenders == [], f"as_list bridging found in: {offenders}"


@pytest.mark.unit
def test_capability_abc_has_no_version_surface() -> None:
    """`Capability.version` is removed from the ABC in both declaration forms."""
    from paxman.core.capability import Capability

    assert "version" not in Capability.__annotations__
    assert "version" not in vars(Capability)


@pytest.mark.unit
def test_shipped_capabilities_do_not_declare_version() -> None:
    """No shipped capability class carries a dead version attribute."""
    from paxman.capabilities import (
        IP,
        ISBN,
        URL,
        Country,
        Currency,
        Date,
        Email,
        Money,
        Phone,
        SIUnit,
    )

    for cls in (Country, Currency, Date, Email, IP, ISBN, Money, Phone, SIUnit, URL):
        assert "version" not in vars(cls), cls.__name__
