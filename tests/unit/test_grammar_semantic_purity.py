"""Grammars and rules must not import from each other.

Recognition grammars perform syntax-level extraction and normalization;
validation rules own every semantic decision with provenance. A grammar that
imports a rule (or vice versa) would let semantics leak across the
pipeline's separation boundary, so it is forbidden structurally.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PAXMAN = Path(__file__).resolve().parents[2] / "paxman"
GRAMMAR_FILES = sorted((PAXMAN / "capabilities").glob("*/grammar/*.py"))
RULE_FILES = sorted((PAXMAN / "capabilities").glob("*/rules/*.py"))


def _package_of(path: Path) -> list[str]:
    """Dotted components of the package containing a module file."""
    rel = path.relative_to(PAXMAN)
    return ["paxman", *rel.parts[:-1]]


def _forbidden_imports(path: Path, forbidden: str) -> list[str]:
    """Return import statements referencing the forbidden package.

    Handles absolute imports (``import paxman.capabilities.rules.X`` and
    ``from paxman.capabilities import rules``), dotted import-from
    (``from paxman.capabilities.rules import X``), and relative imports
    resolved against the importing module's package
    (``from .rules import X``, ``from . import rules``).
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = _package_of(path)
    violations: list[str] = []

    def record(components: list[str], display: str) -> None:
        if forbidden in components and "paxman" in components:
            violations.append(f"{path.name}: {display}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                record(alias.name.split("."), ast.unparse(node))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                parts = node.module.split(".")
                record(parts, ast.unparse(node))
                # "from paxman.capabilities import rules" imports the subpackage.
                for alias in node.names:
                    record([*parts, alias.name], ast.unparse(node))
            if node.level:
                base = package[: len(package) - node.level + 1]
                for alias in node.names:
                    if alias.name != "*":
                        record([*base, alias.name], ast.unparse(node))
                if node.module:
                    # Split on dots like the absolute branch above, so a
                    # dotted relative import ("from ..rules.email_rule import
                    # Rule") records "rules" as its own component and the
                    # forbidden-package check fires.
                    record([*base, *node.module.split(".")], ast.unparse(node))
    return violations


@pytest.mark.unit
@pytest.mark.parametrize("grammar_file", GRAMMAR_FILES, ids=lambda p: p.name)
def test_grammars_do_not_import_rules(grammar_file: Path) -> None:
    assert _forbidden_imports(grammar_file, "rules") == []


@pytest.mark.unit
@pytest.mark.parametrize("rule_file", RULE_FILES, ids=lambda p: p.name)
def test_rules_do_not_import_grammars(rule_file: Path) -> None:
    assert _forbidden_imports(rule_file, "grammar") == []
