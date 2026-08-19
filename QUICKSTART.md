# Quickstart

Get up and running with Paxman in two minutes.

---

## Install

```bash
pip install paxman
```

---

## Your First Canonicalization

```python
import paxman
from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.domain import Resolution

paxman.register_all_shipped()  # once, before first use

# Create a contract and canonicalize
contract = EmailCapability.create_contract()
result = paxman.canonicalize("Contact user@Example.com", contract)

# Check the result
if result.status == Resolution.SUCCESS:
    print(result.canonicalized_value)  # "user@example.com"
```

To register only what you need, call `paxman.register_capability(EmailCapability())` per capability.

Registration — single or bootstrap — must complete from a single thread before the first `canonicalize()` call; post-freeze reads are safe from any thread.

That's it. Paxman recognized the email in your text, validated it against RFC 5322, and returned the lowercase canonical form.

---

## What the Result Means

Every call to `canonicalize()` returns an `ExecutionResult` with a `status` field:

| Status | What happened |
|--------|---------------|
| `SUCCESS` | One canonical value found. Check `result.canonicalized_value`. |
| `MISSING` | Nothing matched. The input contained no recognizable patterns. |
| `INVALID` | Something was recognized, but no specification could validate it. |
| `AMBIGUOUS` | Multiple specifications validated the input but disagreed on the canonical value. |

When status is `MISSING`, `INVALID`, or `AMBIGUOUS`, `result.canonicalized_value` is `None`.

---

## Inspecting Provenance

Every resolved value carries provenance, the authoritative source that validates it:

```python
contract = EmailCapability.create_contract()
result = paxman.canonicalize("user@example.com", contract)

for candidate in result.candidates:
    for prov in candidate.provenance:
        print(f"{prov.authority}: {prov.specification_name}")
        # "IETF: RFC 5322"
```

---

## Tuning Behavior with Contracts

Contracts let you control which grammars run, which rules are excluded, and which year to pin to:

```python
# Enable obfuscated email recognition ("user at domain dot com")
contract = EmailCapability.create_contract(include_obfuscated=True)
result = paxman.canonicalize("Email me at user at example dot com", contract)

# Exclude specific validation rules
contract = EmailCapability.create_contract(excluded_rules=["Section 6.3-localhost"])
result = paxman.canonicalize("admin@localhost", contract)

# Pin to a specific year (excludes rules from newer specifications)
contract = EmailCapability.create_contract(year=2008)
result = paxman.canonicalize("user@example.com", contract)
```

---

## What's Next

For a deeper look at the architectural principles behind Paxman, including determinism, provenance, and the separation of recognition and validation, see [ARCHITECTURE.md](ARCHITECTURE.md).
