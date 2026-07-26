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

When status is `MISSING` or `INVALID`, `result.canonicalized_value` is `None`.

---

## Inspecting Provenance

Every resolved value carries provenance, the authoritative source that validates it:

```python
contract = Email.create_contract()
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

## What's Next

For a deeper look at the architectural principles behind Paxman, including determinism, provenance, and the separation of recognition and validation, see [ARCHITECTURE.md](ARCHITECTURE.md).
