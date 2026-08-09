"""Paxman capabilities."""

from paxman.capabilities.Country.capability import CountryCapability as Country
from paxman.capabilities.Currency.capability import CurrencyCapability as Currency
from paxman.capabilities.Date.capability import DateCapability as Date
from paxman.capabilities.Email.capability import EmailCapability as Email
from paxman.capabilities.IP.capability import IPCapability as IP
from paxman.capabilities.ISBN.capability import ISBNCapability as ISBN
from paxman.capabilities.Money.capability import MoneyCapability as Money
from paxman.capabilities.Phone.capability import PhoneCapability as Phone
from paxman.capabilities.URL.capability import URLCapability as URL

__all__ = [
    "Country",
    "Currency",
    "Date",
    "Email",
    "IP",
    "ISBN",
    "Money",
    "Phone",
    "URL",
]
