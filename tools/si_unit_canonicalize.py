"""Canonicalize an SI Unit input and print only the result.

Usage:
    uv run python tools/si_unit_canonicalize.py "kg"
    uv run python tools/si_unit_canonicalize.py "metre per second"

Output: the canonical value on SUCCESS, otherwise one word:
INVALID / AMBIGUOUS / MISSING.
"""

from __future__ import annotations

import sys

from paxman.api import canonicalize
from paxman.capabilities.SIUnit.capability import SIUnitCapability
from paxman.core.discovery import register_capability, reset_registry

if len(sys.argv) < 2:
    print("usage: si_unit_canonicalize.py <input>", file=sys.stderr)
    sys.exit(2)

reset_registry()
register_capability(SIUnitCapability())
contract = SIUnitCapability.create_contract()

result = canonicalize(sys.argv[1], contract)

if result.status.name == "SUCCESS":
    print(result.canonicalized_value)
else:
    print(result.status.name)
