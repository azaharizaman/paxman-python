# TESTS KNOWLEDGE BASE

## OVERVIEW
Tests are layered by scope; each layer maps to a pytest marker defined in pyproject `[tool.pytest.ini_options]`. The directory IS the marker: a test's location decides which `-m` flag runs it, CI runs the union. 5 layers, 6 capability packages.

## STRUCTURE
```
tests/
├── conftest.py       # loads hypothesis "ci" profile
├── unit/             # -m unit        core domain, registry, contracts, purity scans
├── capabilities/     # -m capability  per-capability, lowercase dirs (country, date, email, ip, isbn, phone)
├── integration/      # -m integration pipeline, ambiguity, temporal, replay hashes, feature gating, format_value seam
├── property/         # -m property    hypothesis property tests
└── e2e/              # -m e2e         canonicalize() end-to-end
```
tests/ root has NO `__init__.py` (only `conftest.py`); every subdirectory IS a package (`__init__.py`).

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Core domain objects (Resolution, Provenance, Candidate…) | `tests/unit/test_<object>.py` |
| Registry register/freeze/reset | `tests/unit/test_discovery.py` |
| Contracts (defaults, serialization, feature flags) | `tests/unit/test_contract.py`, `test_capability_contract.py` |
| Grammar behavior, per capability | `tests/capabilities/<cap>/test_grammar.py` |
| Rule validation, per capability | `tests/capabilities/<cap>/test_rules.py` |
| Capability surface (`format_value`, grammars/rules wiring) | `tests/capabilities/<cap>/test_capability.py` |
| Generated `rules/data/` modules | `test_data.py` / `test_data_consistency.py` per cap (`isbn/test_data.py`, `country/test_data_consistency.py`, `phone/test_data.py`) |
| Purity scans (bans `output_format` in rules, grammar↔rules imports) | `tests/unit/test_rule_output_format_purity.py`, `test_grammar_semantic_purity.py` |
| Rule modules importable + metadata | `tests/unit/test_rule_metadata.py` |
| Packaging / capability exports | `tests/unit/test_package_install.py`, `test_capability_exports.py`, `test_capability_surface.py` |
| Baseline replay hashes (do not edit literals) | `tests/integration/test_default_replay_hashes.py` |
| Full pipeline end-to-end | `tests/e2e/test_canonicalize.py` |

## CONVENTIONS
- One layer per directory. New test placement: `unit/` for core-only behavior, `capabilities/<cap>/` for one capability's grammar/rules/capability, `integration/` for pipeline + cross-capability flows, `property/` for hypothesis, `e2e/` for full `canonicalize()`.
- Capability dirs are lowercase (`isbn`, not `ISBN`). Each holds `test_grammar.py`, `test_rules.py`, `test_capability.py`, plus `test_notation.py` / `test_contract.py` where the capability has them, plus `test_data.py` for generated data.
- Run one capability's suite directly: `uv run pytest tests/capabilities/isbn` (marker `-m isbn` also exists for country/isbn).
- `tests/conftest.py` loads the hypothesis "ci" profile: `max_examples=100`, `deadline=None`, `too_slow` suppressed. Property tests assume this profile; don't override per test.
- Registry hygiene: integration + e2e suites use an autouse `_clean_registry` fixture calling `reset_registry()`; `test_discovery.py` resets it per test. Property tests never touch the registry (they drive grammars/rules/`format_value` directly).
- TDD: failing test first; no skipped tests without justification.

## ANTI-PATTERNS
- No test may depend on registry state left by another test — reset via fixture, never by execution order.
- No new test in the purity-scan family outside `tests/unit/`; scans are a unit-layer concern.
- Property tests must stay off the registry and the frozen pipeline; keep them on grammar/rule/`format_value` inputs.
- Don't weaken the hypothesis "ci" profile inside a single test.
- `# type: ignore[misc]` only for frozen-dataclass immutability assertions, in any layer — nothing else (see root AGENTS.md for the source ban).
