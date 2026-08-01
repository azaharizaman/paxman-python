# Paxman

Paxman is a canonicalization authority resolver. It takes ambiguous human input and returns what authoritative specifications say that input means, with full provenance.

For a deeper understanding of the system, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Installation

```bash
pip install paxman
```

---

## Quick Start

```python
import paxman
from paxman.capabilities import Email
from paxman.core.discovery import register_capability
from paxman.core.domain import Resolution

# Register the Email capability (once, before first use)
register_capability(Email())

# Create a contract and canonicalize
contract = Email.create_contract()
result = paxman.canonicalize("Contact user@Example.com", contract)

# Check the result
if result.status == Resolution.SUCCESS:
    print(result.canonicalized_value)  # "user@example.com"
```

---

## What Happens

When you call `paxman.canonicalize()`, the system:

1. **Recognizes** — grammars scan your input text and find patterns that match known formats
2. **Validates** — rules check those patterns against authoritative specifications (like RFCs)
3. **Resolves** — if exactly one canonical value emerges, it is returned with full provenance

If multiple specifications disagree on the canonical value, the status is `AMBIGUOUS`. If nothing is recognized, the status is `MISSING`. If something is recognized but no specification validates it, the status is `INVALID`.

---

## Capabilities

Paxman ships with five built-in capabilities:

| Capability | Domain | Grammars | Rules | Description |
|------------|--------|----------|-------|-------------|
| **Email** | Email addresses | 3 (standard, obfuscated, localhost) | 2 | RFC 5322, RFC 6761 |
| **Date** | Dates | 3 (ISO, US, European) | 3 | ISO 8601, US federal, EN 50160 |
| **Country** | Country codes/names | 4 (alpha-2, alpha-3, numeric, name) | 6 | ISO 3166, CLDR |
| **IP** | IP addresses | 2 (IPv4, IPv6) | 2 | RFC 791, RFC 5952 |
| **Phone** | Phone numbers | 4 (E.164, tel-URI, 00-prefix, national) | 5 | ITU-T E.164, RFC 3966, NANP |

### Email Capability

Recognizes standard, obfuscated (`user at domain dot com`), and localhost email addresses.

```python
from paxman.capabilities import Email

register_capability(Email())

# Standard email
contract = Email.create_contract()
result = paxman.canonicalize("user@Example.COM", contract)
# → "user@example.com"

# Enable obfuscated recognition
contract = Email.create_contract(include_obfuscated=True)
result = paxman.canonicalize("Contact user at example dot com", contract)
# → "user@example.com"

# Exclude localhost validation
contract = Email.create_contract(excluded_rules=["Section 6.3-localhost"])
result = paxman.canonicalize("admin@localhost", contract)
```

### Date Capability

Recognizes dates in ISO 8601 (`YYYY-MM-DD`), US (`MM/DD/YYYY`), and European (`DD/MM/YYYY`) formats.

```python
from paxman.capabilities import Date

register_capability(Date())

# ISO format (unambiguous)
contract = Date.create_contract()
result = paxman.canonicalize("2026-01-15", contract)
# → "2026-01-15"

# US/European format (potentially ambiguous)
contract = Date.create_contract()
result = paxman.canonicalize("01/02/2026", contract)
# → Status: AMBIGUOUS (US: 2026-01-02, European: 2026-02-01)

# Pin to specific rules
contract = Date.create_contract(pinned_rules=["Section 4.3.1-calendar-date"])
result = paxman.canonicalize("2026-01-15", contract)
```

### Country Capability

Recognizes country representations as alpha-2, alpha-3, numeric codes, or country names.

```python
from paxman.capabilities import Country

register_capability(Country())

# Alpha-2 code
contract = Country.create_contract()
result = paxman.canonicalize("US", contract)
# → "US"

# Country name
contract = Country.create_contract()
result = paxman.canonicalize("United States", contract)
# → "US"

# Enable localized names (CLDR multilingual)
contract = Country.create_contract(include_localized=True)
result = paxman.canonicalize("Deutschland", contract)
# → "DE"

# Enable historical/deprecated names
contract = Country.create_contract(include_historical=True)
result = paxman.canonicalize("Burma", contract)
# → "MM"
```

### IP Capability

Recognizes IPv4 and IPv6 addresses with canonical normalization.

```python
from paxman.capabilities import IP

register_capability(IP())

# IPv4
contract = IP.create_contract()
result = paxman.canonicalize("192.168.1.1", contract)
# → "192.168.1.1"

# IPv6 (canonical form per RFC 5952)
contract = IP.create_contract()
result = paxman.canonicalize("2001:0db8:0000:0000:0000:0000:0000:0001", contract)
# → "2001:db8::1"

# Disable IPv6 recognition
contract = IP.create_contract(include_ipv6=False)
result = paxman.canonicalize("2001:db8::1", contract)
# → Status: MISSING
```

### Phone Capability

Recognizes international (E.164, 00-prefix), tel-URI, and NANP national phone numbers.

```python
from paxman.capabilities import Phone

register_capability(Phone())

# International number
contract = Phone.create_contract()
result = paxman.canonicalize("+1 555 123 4567", contract)
# → "+15551234567"

# National number (requires default_country)
contract = Phone.create_contract(default_country="US")
result = paxman.canonicalize("(555) 234-5678", contract)
# → "+15552345678"

# Output as RFC 3966 tel-URI
contract = Phone.create_contract(output_format="rfc3966")
result = paxman.canonicalize("+15551234567", contract)
# → "tel:+15551234567"
```

---

## Contract Configuration

Every capability provides a `create_contract()` factory method with common and capability-specific parameters.

### Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `excluded_rules` | `Sequence[str]` | Rule names to exclude from validation |
| `pinned_rules` | `Sequence[str]` | Pin to specific rules (overrides `excluded_rules`) |
| `year` | `int` | Temporal filter — only rules with `publication_year ≤ year` run |

### Capability-Specific Parameters

| Capability | Parameter | Type | Description |
|------------|-----------|------|-------------|
| Email | `include_obfuscated` | `bool` | Enable "user at domain dot com" recognition |
| Email | `include_localhost` | `bool` | Enable localhost email recognition (default: `True`) |
| Date | `output_format` | `str` | Output format (e.g., `"ISO"`, `"US"`) |
| Date | `two_digit_base_year` | `int` | Base year for 2-digit years (e.g., `2000` → `"26"` = `2026`) |
| Country | `include_localized` | `bool` | Enable CLDR multilingual name recognition |
| Country | `include_historical` | `bool` | Enable deprecated/historical country name recognition |
| IP | `include_ipv6` | `bool` | Enable IPv6 recognition (default: `True`) |
| Phone | `default_country` | `str` | ISO 3166-1 alpha-2 country code to resolve national numbers (e.g., `"US"`) |
| Phone | `output_format` | `str` | Output format (`"e164"` default, `"rfc3966"`, `"national"`) |

### Rule Pinning and Exclusion

```python
from paxman.capabilities import Email

# Pin to specific rules — only these run
contract = Email.create_contract(pinned_rules=["Section 3.4.1-addr-spec"])
result = paxman.canonicalize("user@example.com", contract)

# Pin + year filter — both apply
contract = Email.create_contract(
    pinned_rules=["Section 3.4.1-addr-spec", "Section 6.3-localhost"],
    year=2010
)

# Exclude specific rules
contract = Email.create_contract(excluded_rules=["Section 6.3-localhost"])
result = paxman.canonicalize("admin@localhost", contract)
```

### Temporal Filtering

```python
from paxman.capabilities import Date

# Only rules published on or before 2019
contract = Date.create_contract(year=2019)
result = paxman.canonicalize("2026-01-15", contract)
```

---

## Resolution Status

| Status | Meaning |
|--------|---------|
| `MISSING` | No patterns recognized in the input |
| `INVALID` | Recognized, but no specification validates it |
| `SUCCESS` | Single canonical value resolved |
| `AMBIGUOUS` | Multiple specifications disagree on the canonical value |

---

## Provenance

Every resolved value carries provenance — the authoritative specification that validates it:

```python
from paxman.capabilities import Email

contract = Email.create_contract()
result = paxman.canonicalize("user@example.com", contract)

for candidate in result.candidates:
    for prov in candidate.provenance:
        print(f"{prov.authority}: {prov.specification_name}")
        # "IETF: RFC 5322"
```

---

## Error Handling

Paxman raises typed exceptions for different failure modes:

```python
from paxman.core.errors import (
    CapabilityError,    # Unknown capability or registry frozen
    ContractError,      # Malformed contract configuration
    RecognitionError,   # Grammar failed during recognition
    ValidationError,    # Rule failed during validation
)

try:
    result = paxman.canonicalize("input", contract)
except CapabilityError as e:
    print(f"Capability error: {e}")
except ContractError as e:
    print(f"Contract error: {e}")
except RecognitionError as e:
    print(f"Recognition failed in {e.rule}: {e}")
except ValidationError as e:
    print(f"Validation failed in {e.rule}: {e}")
```

---

## Learn More

- [ARCHITECTURE.md](ARCHITECTURE.md) — architectural principles and design decisions
- [HOW_TO_ADD_NEW_CAPABILITY.md](HOW_TO_ADD_NEW_CAPABILITY.md) — guide to adding new domain capabilities
- [CONTRIBUTING.md](CONTRIBUTING.md) — development setup and contribution guidelines
