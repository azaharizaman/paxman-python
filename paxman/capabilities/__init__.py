"""Paxman capabilities — PEP 562 lazy exports (Item 8, W4).

Importing `paxman.capabilities` does not import any capability package.
`from paxman.capabilities import Email` imports only `paxman.capabilities.Email`.
This keeps `register_capability(Email())` cheap when only one capability is used.
The committed 15K-line URL IDNA table is not loaded unless URL is imported.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = [
    "Country",
    "Currency",
    "Date",
    "Email",
    "IP",
    "ISBN",
    "Money",
    "Phone",
    "SIUnit",
    "URL",
]

_LAZY: dict[str, tuple[str, str]] = {
    "Country": ("paxman.capabilities.Country.capability", "CountryCapability"),
    "Currency": ("paxman.capabilities.Currency.capability", "CurrencyCapability"),
    "Date": ("paxman.capabilities.Date.capability", "DateCapability"),
    "Email": ("paxman.capabilities.Email.capability", "EmailCapability"),
    "IP": ("paxman.capabilities.IP.capability", "IPCapability"),
    "ISBN": ("paxman.capabilities.ISBN.capability", "ISBNCapability"),
    "Money": ("paxman.capabilities.Money.capability", "MoneyCapability"),
    "Phone": ("paxman.capabilities.Phone.capability", "PhoneCapability"),
    "SIUnit": ("paxman.capabilities.SIUnit.capability", "SIUnitCapability"),
    "URL": ("paxman.capabilities.URL.capability", "URLCapability"),
}

if TYPE_CHECKING:
    from paxman.capabilities.Country.capability import CountryCapability as Country
    from paxman.capabilities.Currency.capability import CurrencyCapability as Currency
    from paxman.capabilities.Date.capability import DateCapability as Date
    from paxman.capabilities.Email.capability import EmailCapability as Email
    from paxman.capabilities.IP.capability import IPCapability as IP
    from paxman.capabilities.ISBN.capability import ISBNCapability as ISBN
    from paxman.capabilities.Money.capability import MoneyCapability as Money
    from paxman.capabilities.Phone.capability import PhoneCapability as Phone
    from paxman.capabilities.SIUnit.capability import SIUnitCapability as SIUnit
    from paxman.capabilities.URL.capability import URLCapability as URL


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        import importlib

        mod_name, attr = _LAZY[name]
        mod = importlib.import_module(mod_name)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
