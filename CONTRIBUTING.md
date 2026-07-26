# Contributing to Paxman

Thanks for your interest in contributing to Paxman. This guide covers the development setup, code style expectations, and pull request process.

---

## What is Paxman?

Paxman is a canonicalization authority resolver. Given ambiguous human input, it returns what authoritative specifications say that input means, with full provenance. It separates the act of recognizing values in text (grammars) from the act of validating them against specifications (rules), and it never guesses. For a full description of the architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Development Environment

Paxman requires Python 3.11 or later. To set up a local development environment:

```bash
# Clone the repository
git clone <repository-url>
cd paxman-alternative

# Create and activate a virtual environment using uv
uv venv
source .venv/bin/activate

# Install the package in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Install the dependency-group dev tools (import-linter)
uv pip install -e ".[dev]" --group dev
```

All dev dependencies are listed in `pyproject.toml` under `[project.optional-dependencies] dev` and include pytest, hypothesis, ruff, pyright, and import-linter.

---

## Running Tests

Tests live in the `tests/` directory and are organized by scope:

| Directory | Marker | What it covers |
|-----------|--------|----------------|
| `tests/unit/` | `@pytest.mark.unit` | Domain object immutability, protocol compliance, enums |
| `tests/capabilities/` | `@pytest.mark.capability` | Grammar recognition and rule normalization per capability |
| `tests/integration/` | `@pytest.mark.integration` | Full pipeline flow, ambiguity detection, temporal filtering, replay hash |
| `tests/e2e/` | `@pytest.mark.e2e` | End-to-end scenarios through the public `canonicalize()` API |

Run all tests:

```bash
pytest
```

Run a specific marker:

```bash
pytest -m unit
pytest -m capability
pytest -m integration
pytest -m e2e
```

The project also uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing of domain object contracts like immutability, equality, and hashability.

---

## Linting and Type Checking

Paxman enforces strict quality gates through three tools. All of them should pass before you submit a pull request.

### Ruff (linting and formatting)

```bash
ruff check .
ruff format .
```

Ruff is configured in `pyproject.toml` with rules for pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, flake8-bugbear, and flake8-simplify. The line length is 88 characters.

### Pyright (static type checking)

```bash
pyright
```

Pyright runs in **strict mode** with `pythonVersion = "3.11"`. It checks only the `paxman/` source directory (not tests or docs). All source code must pass strict type checking with no `# type: ignore` annotations.

### Import Linter (architectural boundary enforcement)

```bash
import-lint
```

Import-linter enforces the four-layer dependency structure described in ARCHITECTURE.md. Dependencies flow inward only:

1. `paxman.api` can import from everything
2. `paxman.engine` can import from `paxman.core` and `paxman.capabilities`
3. `paxman.capabilities` can import from `paxman.core`
4. `paxman.core` cannot import from any other `paxman.*` package

A capability cannot import from another capability. The core layer has no knowledge of specific capabilities. These boundaries are checked automatically and will block a build if violated.

---

## Code Style

A few conventions that go beyond what the linters enforce:

- **No `# type: ignore` or `# noqa` in source code.** If a linter or type checker flags something, address the underlying issue rather than suppressing the warning.
- **Type annotations on all public interfaces.** Function signatures, return types, and class attributes should be fully annotated.
- **Immutability for domain objects.** Domain objects in `paxman/core` use `__slots__` and override `__setattr__` to prevent mutation after construction.
- **One capability per domain.** Each capability (Email, Date, Country, etc.) lives in its own subdirectory under `paxman/capabilities/` and is completely self-contained.
- **Test doubles stay local.** When writing tests, define any stubs, mocks, or fakes within the test file or a `conftest.py` in the same directory. Do not create shared mock libraries across test directories.

---

## Pull Request Process

1. **Create a feature branch** from the main branch.
2. **Write tests first** where applicable. The project follows TDD principles: write a failing test, make it pass, then refactor.
3. **Run the full quality suite** before pushing:
   ```bash
   ruff check . && ruff format --check . && pyright && import-lint && pytest
   ```
4. **Push your branch** and open a pull request.
5. **Describe what changed and why.** Reference any related issues.
6. **Respond to review feedback.** Push additional commits to address comments rather than force-pushing over reviewed code.

All CI checks (ruff, pyright, import-linter, pytest) must pass before a pull request can be merged.

---

## Architecture at a Glance

If you're new to the codebase, the key structural rule is that Paxman has four layers with strict one-directional dependencies:

- **`paxman.core`** defines the shared vocabulary: domain objects, abstract base classes, the Contract protocol, and the capability registry.
- **`paxman.capabilities`** contains self-contained domain modules (Email, Date, Country, etc.) that each provide their own grammars, rules, and notation types.
- **`paxman.engine`** orchestrates the recognition-validation pipeline without knowing what any specific capability does.
- **`paxman.api`** exposes the public `canonicalize()` function.

For a deeper look at the design decisions behind this structure, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Questions?

Open an issue or start a discussion in the repository. Thanks for contributing.
