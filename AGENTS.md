# PROJECT KNOWLEDGE BASE

**Generated:** 2026-08-06
**Commit:** 7a4017c
**Branch:** feature/CURRENCY-capability

## OVERVIEW
Paxman is a Python 3.11+ canonicalization library: takes ambiguous human input, returns what authoritative specs say it means, with full provenance. Deterministic, provenance-first. 10 capabilities (Country, Currency, Date, Email, IP, ISBN, Money, Phone, SI Unit, URL). Toolchain: uv + hatchling, ruff, strict pyright, import-linter, pytest at 95% coverage.

## STRUCTURE
```text
paxman/
├── api/            # canonicalize() — sole public entry
├── engine/         # run_capability() pipeline orchestrator
├── core/           # domain objects, Contract protocol, registry, errors
└── capabilities/   # 10 self-contained capability packages
tests/              # unit / capabilities/<cap> / integration / property / e2e
tools/              # regenerate_isbn_range_data.py, regenerate_si_prefix_data.py, regenerate_idna_uts46_data.py
docs/               # adr/, report/, research/, superpowers/plans+specs
```

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Trace pipeline flow | `paxman/engine/orchestrator.py` → `run_capability()` |
| Domain vocabulary (Rule, Provenance, Candidate…) | `paxman/core/domain.py` |
| Contract protocol | `paxman/core/contract.py`, `paxman/core/capability_contract.py` |
| Capability registration | `paxman/core/discovery.py` (explicit, never auto) |
| Error hierarchy | `paxman/core/errors.py` |
| Add a capability | `HOW_TO_ADD_NEW_CAPABILITY.md` (62KB spec — read first). Scaffold first with `tools/new_capability.py` (see HOW_TO_ADD_NEW_CAPABILITY.md Step 0); then fill in the domain. |
| Recognition (per cap) | `paxman/capabilities/<Name>/grammar/` |
| Validation (per cap) | `paxman/capabilities/<Name>/rules/` |
| Presentation seam | `paxman/capabilities/<Name>/capability.py` → `format_value()` |
| Regenerate generated data | `tools/regenerate_isbn_range_data.py` (ISBN range), `tools/regenerate_si_prefix_data.py` (SIUnit prefixed units), `tools/regenerate_idna_uts46_data.py` (URL IDNA mapping) |
| Merge-blocking commands | `.github/workflows/ci.yml` (authoritative) |
| Past implementation plans | `docs/superpowers/plans/` |

## CODE MAP
| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `canonicalize()` | function | `paxman/api/canonicalize.py` | Sole user entry point → `run_capability()` |
| `register_capability()` | function | `paxman/core/discovery.py` | Registry add; freezes on first run |
| `run_capability()` | function | `paxman/engine/orchestrator.py` | Full pipeline (recognize→validate→resolve→hash) |
| `ExecutionResult` | dataclass | `paxman/engine/orchestrator.py` | Return type of `canonicalize()` |
| `Capability` | ABC | `paxman/core/capability.py` | `get_grammars`/`get_rules`/`format_value` |
| `CapabilityContract` | dataclass | `paxman/core/capability_contract.py` | Frozen contract base (no slots) |
| `Contract` | Protocol | `paxman/core/contract.py` | Structural contract interface |
| `Rule` / `Grammar` | ABCs | `paxman/core/domain.py` | Validation / recognition units |
| `Resolution`, `Provenance`, `Candidate`, `RecognizedRep`, `VersionStamp` | dataclasses | `paxman/core/domain.py` | Pipeline value objects |

## CONVENTIONS
- **uv only** — no Makefile/tox/nox. Every command via `uv run`.
- Per-capability layout: `notation.py`, `contract.py`, `capability.py`, `grammar/`, `rules/`.
- Rule file = ONE publication (`rfc_5322_ed2008.py`); class = one section; rule `name` = `"Section 3.4.1-addr-spec"`.
- Grammars recognize only: span-bearing `RecognitionMatch`, never bare notation, never validate/dedup/order.
- Rules never read `output_format` (CI source-scan enforced), never raise, never gate on `include_*` (declared as `requires_features`).
- `format_value()` is the ONLY presentation seam; `output_format` resolved in `CapabilityContract.__post_init__`.
- Domain objects: `@dataclass(frozen=True, slots=True)`. Contracts: `@dataclass(frozen=True)` **without** slots.
- Test doubles local to the test file/conftest — no shared mock libraries.
- Registry is module-level and freezes per pipeline run; tests use autouse `_clean_registry` fixture (integration/e2e).
- TDD: failing test first. No skipped tests without justification.

## ANTI-PATTERNS (THIS PROJECT)
- **No `# type: ignore` / `# noqa` / `# pyright: ignore` in `paxman/` source** — fix root cause or use scoped ruff `per-file-ignores` (sanctioned pattern in pyproject). Tests may use `# type: ignore[misc]` for immutability checks.
- Deterministic by construction: given the same input, the same contract, and the same library snapshot (fixed library version, registry contents, and rule-data tables), the pipeline always yields the same canonical output — no world-knowledge, no clock, no environment-dependent ordering, no fuzzy logic, no network inference across recognition, validation, and canonicalization.
- No cross-capability imports; capabilities import only from `paxman.core`; `paxman.core` imports nothing from `paxman.*`.
- Grammars must not map tokens to canonical values or import rule-layer data.
- Rules never contain the token `output_format` (code, comments, or docstrings).
- No `as any`, no broad exception suppression.

## COMMANDS
```bash
uv sync --all-extras                                   # install
uv run ruff check paxman/ tests/                      # lint
uv run ruff format --check paxman/ tests/             # format check
uv run pyright                                        # strict typecheck
uv run import-linter lint                             # layer boundaries
uv run pytest                                         # all tests
uv run pytest -m "unit or capability or integration or e2e"      # by marker (also: property, country, currency, isbn, money, url, si_unit)
uv run pytest --cov=paxman --cov-report=term-missing --tb=short -q
uv run coverage report --include="paxman/core/*,paxman/capabilities/*,paxman/engine/*,paxman/api/*" --fail-under=95
uv run python tools/regenerate_isbn_range_data.py     # regenerate ISBN range message module
uv run python tools/regenerate_si_prefix_data.py      # regenerate SIUnit prefixed-unit modules
uv run python tools/regenerate_idna_uts46_data.py     # regenerate URL IDNA UTS #46 mapping
```
Full pre-PR gate: `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run import-linter lint && uv run pytest`

## NOTES
- `paxman/capabilities/__init__.py` exports all ten shipped capabilities (Country, Currency, Date, Email, IP, ISBN, Money, Phone, SI Unit, URL); export completeness is enforced by `tests/unit/test_capability_exports.py`.
- CONTEXT.md is the domain glossary for the full shipped set (ten capabilities). It is kept in sync with the code; when adding a capability, update its Notation/table entries there too.
- No `pyrightconfig.json` — pyright config is inline `[tool.pyright]` in pyproject.toml. No `.editorconfig`.
- Data modules live under `rules/data/` (Country, Currency, ISBN, Money, Phone, SI Unit, URL) and `grammar/data/` (Country, Currency, Money, SI Unit) — plain module-level tables separating data from logic, maintained in place. Only the ISBN range message, the URL IDNA UTS #46 mapping, and the SIUnit prefixed-unit and grammar token tables are generated (each via its `tools/regenerate_*_data.py` script); unmarked data files are edited directly.
- Library only — no CLI, no `__main__.py`, no `[project.scripts]`. Version 0.2.0.
- Coverage: global `fail_under = 95` + per-package 95% gates in CI.
