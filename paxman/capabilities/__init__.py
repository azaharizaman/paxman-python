"""Paxman capabilities."""

from paxman.capabilities.Country.capability import CountryCapability as Country
from paxman.capabilities.Date.capability import DateCapability as Date
from paxman.capabilities.Email.capability import EmailCapability as Email
from paxman.capabilities.ISBN.capability import ISBNCapability as ISBN
from paxman.capabilities.Phone.capability import PhoneCapability as Phone

__all__ = ["Country", "Date", "Email", "ISBN", "Phone"]
