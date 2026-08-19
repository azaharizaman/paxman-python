"""Item 5 — contract surface unification: CapabilityContract is the single source of truth.

These tests drive Task 3: they will FAIL until the engine removes getattr probes
and Contract is demoted from public exports.
"""

from __future__ import annotations

import importlib


def test_contract_not_exported_from_core_public_api() -> None:
    """After unification, `Contract` must NOT be exported from `paxman.core`."""
    import paxman.core as core

    assert not hasattr(core, "Contract") or core.Contract.__module__.endswith(
        "_engine_contract"
    ), "Contract must not be publicly re-exported from paxman.core"


def test_capability_contract_is_only_public_base() -> None:
    """Every shipped contract must inherit CapabilityContract (homogeneity mandate)."""
    from paxman.capabilities.Country.contract import CountryContract
    from paxman.capabilities.Currency.contract import CurrencyContract
    from paxman.capabilities.Date.contract import DateContract
    from paxman.capabilities.Email.contract import EmailContract
    from paxman.capabilities.IP.contract import IPContract
    from paxman.capabilities.ISBN.contract import ISBNContract
    from paxman.capabilities.Money.contract import MoneyContract
    from paxman.capabilities.Phone.contract import PhoneContract
    from paxman.capabilities.SIUnit.contract import SIUnitContract
    from paxman.capabilities.URL.contract import URLCapabilityContract as URLContract
    from paxman.core.capability_contract import CapabilityContract

    for cls in [
        CountryContract,
        CurrencyContract,
        DateContract,
        EmailContract,
        IPContract,
        ISBNContract,
        MoneyContract,
        PhoneContract,
        SIUnitContract,
        URLContract,
    ]:
        assert issubclass(cls, CapabilityContract), f"{cls.__name__} must inherit CapabilityContract"


def test_engine_requires_extra_grammars_attribute() -> None:
    """Engine must access contract.extra_grammars directly (no getattr fallback)."""
    from dataclasses import dataclass

    from paxman.engine.orchestrator import _recognize  # type: ignore[attr-defined]

    # Build a minimal contract-like object WITHOUT extra_grammars — should fail fast
    # (after fix, engine does NOT use getattr(... , ()); it accesses directly)
    @dataclass(frozen=True)
    class _BadContract:
        capability_name: str = "email"
        active_grammars = None
        excluded_rules: tuple[str, ...] = ()
        pinned_rules: tuple[str, ...] | None = None
        year: int | None = None
        output_format: str | None = None
        # NOTE: no extra_grammars attribute at all

    # The engine should not silently succeed via getattr fallback
    import inspect

    src = inspect.getsource(_recognize)
    assert 'getattr(contract, "extra_grammars"' not in src, "getattr probe must be removed from _recognize"

    src2 = inspect.getsource(importlib.import_module("paxman.engine.orchestrator"))
    assert 'getattr(contract, "extra_grammars"' not in src2, "all getattr probes for extra_grammars must be removed"


def test_contract_factory_docstring_mentions_ten() -> None:
    """ContractFactory docstring must say ten, not five."""
    from paxman.core.capability import ContractFactory

    assert ContractFactory.__doc__ is not None
    assert "five" not in ContractFactory.__doc__.lower(), "stale 'five' must be fixed"
