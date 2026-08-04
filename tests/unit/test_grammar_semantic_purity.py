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


def _forbidden_imports(path: Path, forbidden: str) -> list[str]:
    """Return import-from statements referencing the forbidden package."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if forbidden in parts and "paxman" in parts:
                violations.append(f"{path.name}: {ast.unparse(node)}")
    return violations


@pytest.mark.unit
@pytest.mark.parametrize("grammar_file", GRAMMAR_FILES, ids=lambda p: p.name)
def test_grammars_do_not_import_rules(grammar_file: Path) -> None:
    assert _forbidden_imports(grammar_file, "rules") == []


@pytest.mark.unit
@pytest.mark.parametrize("rule_file", RULE_FILES, ids=lambda p: p.name)
def test_rules_do_not_import_grammars(rule_file: Path) -> None:
    assert _forbidden_imports(rule_file, "grammar") == []
