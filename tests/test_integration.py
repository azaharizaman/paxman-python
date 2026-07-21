"""Integration verification tests.

End-to-end tests with a real capability stub, Hypothesis property tests
encoding invariants, and source boundary verification.
"""

from __future__ import annotations

import ast
import pathlib
import subprocess

from hypothesis import given, settings
from hypothesis import strategies as st

from paxman._engine.engine import Engine, EngineConfig
from paxman._registry.registry import Registry
from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict

from tests._stubs import StubCapability


# ---------------------------------------------------------------------------
# End-to-end test
# ---------------------------------------------------------------------------
class TestEndToEnd:
    """End-to-end: Registry -> Engine -> canonicalize -> verify -> replay -> verify."""

    def test_full_lifecycle(self) -> None:
        """Complete lifecycle: construct, canonicalize, verify, replay."""
        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)

        # Verify artifact
        assert isinstance(artifact.result, Verdict)
        assert artifact.result.canonical == "foo@bar.com"
        assert artifact.contract == contract
        assert artifact.config_digest == config.digest()

        # Replay and verify identical
        replayed = engine.replay(artifact)
        assert replayed is artifact
        assert replayed == artifact

    def test_full_lifecycle_refusal(self) -> None:
        """Complete lifecycle with no-owner refusal."""
        kind = Kind(name="email.address")
        cap = StubCapability(owned_kinds=frozenset({Kind(name="date.iso")}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize("FOO@BAR.COM", contract)

        assert isinstance(artifact.result, Refusal)
        replayed = engine.replay(artifact)
        assert replayed is artifact


# ---------------------------------------------------------------------------
# Hypothesis property tests
# ---------------------------------------------------------------------------
class TestInvariants:
    """Hypothesis property tests encoding the invariants."""

    @given(
        raw=st.text(min_size=1, max_size=100),
        kind_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="/")),
    )
    @settings(max_examples=50, deadline=200)
    def test_determinism_invariant(self, raw: str, kind_name: str) -> None:
        """Invariant 2: same input + same config + same capabilities -> same artifact."""
        kind = Kind(name=kind_name)
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        a1 = engine.canonicalize(raw, contract)
        a2 = engine.canonicalize(raw, contract)

        assert a1 == a2

    @given(
        raw=st.text(min_size=1, max_size=100),
        kind_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="/")),
    )
    @settings(max_examples=50, deadline=200)
    def test_replay_invariant(self, raw: str, kind_name: str) -> None:
        """Invariant 3: canonicalize -> replay -> identical artifact."""
        kind = Kind(name=kind_name)
        cap = StubCapability(owned_kinds=frozenset({kind}))
        registry = Registry(capabilities=[cap])
        config = EngineConfig(authorities={})
        engine = Engine(registry=registry, config=config)

        contract = Contract(kind=kind)
        artifact = engine.canonicalize(raw, contract)
        replayed = engine.replay(artifact)

        assert artifact == replayed
        assert artifact.contract == replayed.contract
        assert artifact.result == replayed.result
        assert artifact.config_digest == replayed.config_digest


# ---------------------------------------------------------------------------
# Source boundary test
# ---------------------------------------------------------------------------
class TestSourceBoundary:
    """Verify no file inside src/ imports from outside src/."""

    SRC_ROOT = pathlib.Path(__file__).resolve().parent.parent / "src"

    def test_no_src_imports_from_outside(self) -> None:
        """No file inside src/ imports third-party or local packages from outside src/.

        Standard library imports (__future__, dataclasses, typing, hashlib, etc.)
        are excluded — they are always available and don't create a verification gap.
        """
        import sys

        violations: list[str] = []
        stdlib_modules = set(sys.stdlib_module_names)

        for py_file in self.SRC_ROOT.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top_level = alias.name.split(".")[0]
                        if top_level not in stdlib_modules and not self._is_internal_import(alias.name):
                            violations.append(
                                f"{py_file.relative_to(self.SRC_ROOT)}:{node.lineno} "
                                f"imports '{alias.name}' from outside src/"
                            )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    top_level = node.module.split(".")[0]
                    if top_level not in stdlib_modules and not self._is_internal_import(node.module):
                        violations.append(
                            f"{py_file.relative_to(self.SRC_ROOT)}:{node.lineno} "
                            f"from-imports '{node.module}' from outside src/"
                        )

        assert not violations, "Source boundary violations:\n" + "\n".join(violations)

    def _is_internal_import(self, module_path: str) -> bool:
        """Check if an import path refers to an internal module."""
        top_level = module_path.split(".")[0]
        # Standard library and third-party modules are not internal
        internal_tops = {"paxman"}
        return top_level in internal_tops


# ---------------------------------------------------------------------------
# Guardrail verification (run as integration checks)
# ---------------------------------------------------------------------------
class TestGuardrails:
    """Verify all guardrails pass: lint-imports, mypy --strict, ruff."""

    def test_import_linter(self) -> None:
        """PYTHONPATH=src lint-imports passes all 5 contracts."""
        result = subprocess.run(
            ["lint-imports"],
            cwd=pathlib.Path(__file__).resolve().parent.parent,
            env={"PYTHONPATH": "src", "PATH": str(pathlib.Path(".venv/bin"))},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"lint-imports failed:\n{result.stdout}\n{result.stderr}"

    def test_mypy_strict(self) -> None:
        """mypy --strict passes on entire src/."""
        result = subprocess.run(
            ["uv", "run", "mypy", "--strict", "src/paxman"],
            cwd=pathlib.Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"mypy --strict failed:\n{result.stdout}\n{result.stderr}"

    def test_ruff_check(self) -> None:
        """ruff check src passes."""
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "src"],
            cwd=pathlib.Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"ruff check failed:\n{result.stdout}\n{result.stderr}"

    def test_ruff_format(self) -> None:
        """ruff format --check src passes."""
        result = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", "src"],
            cwd=pathlib.Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"ruff format --check failed:\n{result.stdout}\n{result.stderr}"
