"""Resolution status is computed only in ``_determine_status``.

ADR-0002 decision #5 fixes the layered contract: resolution status is a
pipeline output computed exactly once, by the engine orchestrator's
``_determine_status``. No other orchestrator function may construct or
assign a ``Resolution``; ``_extract_canonical_value`` may only *read* the
status it receives (``status == Resolution.SUCCESS``).

This test AST-scans ``paxman/engine/orchestrator.py`` and asserts that
every ``Resolution.`` member access lives inside one of those two
functions. A companion assertion locks the return side: ``_determine_status``
is the sole function declaring a ``Resolution`` return annotation. Any
future code path that tries to build or assign a ``Resolution`` elsewhere
fails CI as architectural drift.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_ORCHESTRATOR_PATH = (
    Path(__file__).resolve().parents[2] / "paxman" / "engine" / "orchestrator.py"
)

# Functions allowed to touch Resolution members: _determine_status computes
# the status; _extract_canonical_value only reads it.
_ALLOWED_FUNCTIONS = frozenset({"_determine_status", "_extract_canonical_value"})


def _resolve_member_accesses(tree: ast.Module) -> list[tuple[int, str, str]]:
    """Return ``(lineno, function, member)`` for every ``Resolution.X`` access.

    Accesses are attributed to the top-level function whose body contains
    them; module-level accesses are attributed to ``"<module>"``.
    """
    accesses: list[tuple[int, str, str]] = []

    def scan_stmts(body: list[ast.stmt], function: str) -> None:
        for stmt in body:
            for node in ast.walk(stmt):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "Resolution"
                ):
                    accesses.append((node.lineno, function, node.attr))

    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scan_stmts(stmt.body, stmt.name)
        else:
            scan_stmts([stmt], "<module>")

    return accesses


def _functions_returning_resolution(tree: ast.Module) -> list[str]:
    """Names of functions whose return annotation names ``Resolution``."""
    names: list[str] = []
    for stmt in tree.body:
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if stmt.returns is None:
            continue
        if any(
            isinstance(node, ast.Name) and node.id == "Resolution"
            for node in ast.walk(stmt.returns)
        ):
            names.append(stmt.name)
    return names


@pytest.mark.unit
def test_status_computed_only_in_determine_status() -> None:
    """Every ``Resolution.`` access lives in an allowed function."""
    tree = ast.parse(_ORCHESTRATOR_PATH.read_text(encoding="utf-8"))
    violations = [
        (lineno, function, member)
        for lineno, function, member in _resolve_member_accesses(tree)
        if function not in _ALLOWED_FUNCTIONS
    ]
    assert violations == [], (
        "Resolution members may only be accessed inside _determine_status "
        "(computes status) or _extract_canonical_value (reads it). Found: "
        + ", ".join(
            f"{function}() line {lineno}: Resolution.{member}"
            for lineno, function, member in violations
        )
    )


@pytest.mark.unit
def test_only_determine_status_declares_resolution_return() -> None:
    """``_determine_status`` is the sole function returning a ``Resolution``."""
    tree = ast.parse(_ORCHESTRATOR_PATH.read_text(encoding="utf-8"))
    assert _functions_returning_resolution(tree) == ["_determine_status"]
