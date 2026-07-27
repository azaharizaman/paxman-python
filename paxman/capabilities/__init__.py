"""Paxman capabilities."""

from paxman.capabilities.Country.capability import CountryCapability as Country
from paxman.capabilities.Date.capability import DateCapability as Date
from paxman.capabilities.Email.capability import EmailCapability as Email

__all__ = ["Country", "Date", "Email"]
