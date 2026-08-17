"""Phone notation — intermediate representation for phone number recognition."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PhoneNotation:
    """Intermediate representation for phone number recognition.

    Attributes:
        shape: Discriminator set by grammar ("e164", "national", "rfc3966").
            - "e164": value is the E.164 number digits WITHOUT the leading "+"
              or the international prefix "00" (e.g., "15551234567").
            - "national": value is the domestic dialing digits, optional
              leading trunk "1" preserved (e.g., "15551234567" or "5551234567").
            - "rfc3966": value is the tel-URI number digits WITHOUT "tel:"
              prefix or "+" (e.g., "15551234567").
        value: Digit-only string (no "+", no separators, no "tel:" prefix).
        extension: Digits of the ";ext=" parameter (RFC 3966 only); "" when
            no extension is present.
    """

    shape: str
    value: str
    extension: str = ""
