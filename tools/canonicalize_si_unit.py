"""Canonicalize a single SI Unit input with paxman.

Quick CLI helper for trying SI Unit expressions by hand. Edit INPUT below
(or pass it as an argument) and run:

    uv run python tools/canonicalize_si_unit.py
    uv run python tools/canonicalize_si_unit.py "N·m"
    uv run python tools/canonicalize_si_unit.py "metre per second" --year 2018

Prints status, canonical value, and the surviving candidates with provenance.
"""

from __future__ import annotations

import argparse

from paxman.api import canonicalize
from paxman.capabilities.SIUnit.capability import SIUnitCapability
from paxman.core.discovery import register_capability, reset_registry

# >>> EDIT ME: the default input used when no argument is given on the CLI <<<
INPUT = "kg·m²·s⁻²"
# Common contract params you can toggle (see SIUnitCapability.create_contract):
#   year: int | None  - temporal filter (only rules with publication_year <= year run)
YEAR: int | None = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonicalize an SI Unit input.")
    parser.add_argument("input", nargs="?", default=INPUT, help="the SI unit text to canonicalize")
    parser.add_argument("--year", type=int, default=YEAR, help="temporal filter year")
    args = parser.parse_args()

    reset_registry()
    register_capability(SIUnitCapability())
    contract = SIUnitCapability.create_contract(year=args.year)

    result = canonicalize(args.input, contract)

    print(f"input             : {args.input!r}")
    print(f"status            : {result.status.name}")
    print(f"canonical_value   : {result.canonicalized_value!r}")
    print(f"candidates ({len(result.candidates)}) :")
    for cand in result.candidates:
        provs = ", ".join(
            f"{p.authority}/{p.specification_name} ({p.version}, {p.publication_year})"
            for p in cand.provenance
        )
        print(f"  - {cand.value!r}  <- {provs or 'no provenance'}")


if __name__ == "__main__":
    main()
