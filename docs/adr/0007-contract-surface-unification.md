# ADR-0007: Contract Surface Unification — CapabilityContract as Single Source of Truth

## Status

Accepted

## Context

`paxman/core/contract.py` defines `Contract` as a `@runtime_checkable` Protocol (intended for duck-typed user contracts). `paxman/core/capability_contract.py` defines `CapabilityContract` as a frozen dataclass ABC that every shipped contract MUST inherit (homogeneity mandate, `capabilities/AGENTS.md`). The 2026-08-17 architecture review (W1) found drift:

- `Contract` omits `extra_grammars`; engine probes via `getattr(contract, "extra_grammars", ())` in `orchestrator._recognize` and `_activated_rules`. A duck-typed `Contract` silently loses the extension seam.
- `Contract.output_format: str | None` vs `CapabilityContract.__post_init__` always resolves to concrete `str`.
- `ContractFactory` docstring says "five capability classes" — there are ten.

Dual truth is a compat hazard; the ABC has won in practice (all 10 shipped contracts inherit it).

## Decision

- `CapabilityContract` is the **only sanctioned public contract base**. Shipped and community contracts MUST inherit it.
- `Contract` Protocol is demoted to **engine-internal** (`paxman/core/_engine_contract.py` or retained as private re-export, not exported from `paxman.core.__init__` or `paxman.__init__`). It exists only for internal structural typing of the engine boundary.
- Engine removes all `getattr(contract, "extra_grammars", ())` probes; accesses `contract.extra_grammars` directly (fail-fast `AttributeError` → `ContractError` wrapping if violated).
- `ContractFactory` docstring corrected to ten; `capability_name` contract field typed as concrete `str` post-`__post_init__`.
- Breaking change is budgeted at 0.x per M12; provide a one-minor deprecation shim if needed (`Contract = CapabilityContract` alias with DeprecationWarning gated by env var, removed at 0.3.0).

## Alternatives Considered

1. **Fix Protocol to match ABC** (add `extra_grammars`, fix `output_format: str`): keeps two definitions in sync forever — drift will recur, no user value (no shipped duck-typed contract exists).
2. **Keep Protocol as public, ABC as convenience**: same dual-sync cost plus weaker homogeneity enforcement (`__init_subclass__` checks bypassed for duck types).

## Consequences

- One source of truth; drift eliminated; `getattr` probes deleted.
- Engine type hints narrow to `CapabilityContract`; `pyright` strict passes without `getattr` fallback.
- Third-party duck-typed contracts without inheritance fail fast with actionable `ContractError` instead of silent extension-seam loss.
- `import-linter` layers unchanged; no new dependencies.

## References

- `docs/reports/2026-08-17-architecture-review.md` W1, §9 item 5, M9
- `paxman/core/capability_contract.py`, `paxman/core/contract.py`, `paxman/engine/orchestrator.py`
