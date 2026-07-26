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
from paxman.core.domain import Resolution

# Register the Email capability (once, before first use)
paxman.register_capability(Email())

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

## Contract Configuration

You can configure behavior through the contract:

```python
from paxman.capabilities import Email

# Enable obfuscated email recognition ("user at domain dot com")
contract = Email.create_contract(include_obfuscated=True)
result = paxman.canonicalize("Email me at user at example dot com", contract)

# Exclude specific validation rules
contract = Email.create_contract(excluded_rules=["Section 6.3-localhost"])
result = paxman.canonicalize("admin@localhost", contract)

# Pin to a specific year (excludes rules from newer specifications)
contract = Email.create_contract(year=2008)
result = paxman.canonicalize("user@example.com", contract)
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
contract = Email.create_contract()
result = paxman.canonicalize("user@example.com", contract)

for candidate in result.candidates:
    for prov in candidate.provenance:
        print(f"{prov.authority}: {prov.specification_name}")
        # "IETF: RFC 5322"
```

---

## Learn More

- [ARCHITECTURE.md](ARCHITECTURE.md) — architectural principles and design decisions
- [HOW_TO_ADD_NEW_CAPABILITY.md](HOW_TO_ADD_NEW_CAPABILITY.md) — guide to adding new domain capabilities
