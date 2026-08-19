"""Tests for tools/new_capability.py — the capability scaffolder.

These tests run the scaffolder in-process against the REAL tree (import-linter
/ package semantics require the real location) with strict cleanup discipline:
a function-scoped autouse fixture snapshots ``paxman/capabilities/__init__.py``
bytes, then in teardown restores them byte-for-byte, removes the generated
package and test directories, purges any generated modules from
``sys.modules``, and resets the capability registry. Generated modules are
imported by direct path — never by reloading ``paxman.capabilities``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Iterator
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

# `tests/unit/__init__.py` is present, so pytest prepends `tests/` (not the
# repo root) to sys.path. The scaffolder lives in `tools/` at the repo root,
# so ensure the repo root is importable for `from tools import new_capability`.
_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_PKG = _REPO / "paxman" / "capabilities" / "Widget"
_TESTS = _REPO / "tests" / "capabilities" / "widget"
_INIT = _REPO / "paxman" / "capabilities" / "__init__.py"
_SURFACE = _REPO / "tests" / "unit" / "test_capability_surface.py"

_ARGS = (
    "--name",
    "widget",
    "--authority",
    "Acme",
    "--spec-name",
    "Acme Widget Standard",
    "--spec-url",
    "https://example.com/widget",
    "--publication-year",
    "2026",
)


@pytest.fixture(autouse=True)
def scaffolded() -> Iterator[None]:
    """Run the scaffolder; restore the tree byte-for-byte afterwards."""
    saved_init = _INIT.read_bytes()
    saved_surface = _SURFACE.read_bytes()
    try:
        yield
    finally:
        if _PKG.exists():
            shutil.rmtree(_PKG)
        if _TESTS.exists():
            shutil.rmtree(_TESTS)
        _INIT.write_bytes(saved_init)
        _SURFACE.write_bytes(saved_surface)
        # Purge cached generated modules so later tests / the main suite
        # re-read the restored (un-wired) __init__.py. Match the exact
        # Widget package (and its submodules) — not WidgetTest/WidgetFoo etc.
        for name in list(sys.modules):
            if name == "paxman.capabilities.Widget" or name.startswith(
                "paxman.capabilities.Widget."
            ):
                del sys.modules[name]
            if name in (
                "paxman.capabilities",
                "tests.unit.test_capability_surface",
            ):
                del sys.modules[name]
        from paxman.core.discovery import reset_registry

        reset_registry()


def _run(*args: str) -> None:
    from tools import new_capability

    new_capability.main(["Widget", *args])


@pytest.mark.unit
def test_rejects_existing_package() -> None:
    """Refuse to overwrite an existing capability package (exit 2)."""
    _PKG.mkdir(parents=True)
    try:
        with pytest.raises(SystemExit) as exc:
            _run(*_ARGS)
        assert exc.value.code == 2
    finally:
        shutil.rmtree(_PKG)


@pytest.mark.unit
def test_rejects_invalid_package_name() -> None:
    """Refuse a non-CapWords package name (exit 2)."""
    from tools import new_capability

    with pytest.raises(SystemExit) as exc:
        new_capability.main(["widget", *_ARGS])
    assert exc.value.code == 2


@pytest.mark.unit
def test_rejects_non_snake_registry_name() -> None:
    """Refuse a non-snake_case registry name (exit 2)."""
    from tools import new_capability

    with pytest.raises(SystemExit) as exc:
        new_capability.main(
            [
                "Widget",
                "--name",
                "Widget",
                "--authority",
                "Acme",
                "--spec-name",
                "Acme Widget Standard",
                "--spec-url",
                "https://example.com/widget",
                "--publication-year",
                "2026",
            ]
        )
    assert exc.value.code == 2


@pytest.mark.unit
def test_generates_full_inventory() -> None:
    """Generate the full 13-file inventory + edit __init__.py."""
    _run(*_ARGS)

    generated = [
        _PKG / "__init__.py",
        _PKG / "notation.py",
        _PKG / "contract.py",
        _PKG / "capability.py",
        _PKG / "grammar" / "__init__.py",
        _PKG / "grammar" / "widget_recognition.py",
        _PKG / "rules" / "__init__.py",
        _PKG / "rules" / "acme_ed2026.py",
        _TESTS / "__init__.py",
        _TESTS / "test_notation.py",
        _TESTS / "test_grammar.py",
        _TESTS / "test_rules.py",
        _TESTS / "test_capability.py",
    ]
    for path in generated:
        assert path.exists(), f"missing generated file: {path}"
    # The edited __init__.py must also be present (and now wired).
    assert _INIT.exists()
    text = _INIT.read_text(encoding="utf-8")
    assert (
        "from paxman.capabilities.Widget.capability import WidgetCapability as Widget"
        in text
    )
    assert '"Widget",' in text


@pytest.mark.unit
def test_templates_satisfy_enforced_surface() -> None:
    """Generated code satisfies every import-time enforcement."""
    _run(*_ARGS)

    cap_path = _PKG / "capability.py"
    grammar_path = _PKG / "grammar" / "widget_recognition.py"
    rule_path = _PKG / "rules" / "acme_ed2026.py"
    contract_path = _PKG / "contract.py"

    cap_mod = module_from_spec(
        spec_from_file_location("paxman.capabilities.Widget.capability", cap_path)
    )
    grammar_mod = module_from_spec(
        spec_from_file_location(
            "paxman.capabilities.Widget.grammar.widget_recognition", grammar_path
        )
    )
    rule_mod = module_from_spec(
        spec_from_file_location(
            "paxman.capabilities.Widget.rules.acme_ed2026", rule_path
        )
    )
    contract_mod = module_from_spec(
        spec_from_file_location("paxman.capabilities.Widget.contract", contract_path)
    )
    for mod in (cap_mod, grammar_mod, rule_mod, contract_mod):
        mod.__loader__.exec_module(mod)  # type: ignore[union-attr]

    # Grammar: mandatory non-empty semantics.
    assert isinstance(grammar_mod.WidgetRecognition.semantics, str)
    assert grammar_mod.WidgetRecognition.semantics

    # Rule: the six enforced metadata fields.
    rule = rule_mod.WidgetRule
    assert isinstance(rule.name, str) and rule.name
    assert rule.strategy is not None
    assert rule.provenance is not None
    assert isinstance(rule.citation, str) and rule.citation
    assert isinstance(rule.target_semantics, frozenset)
    assert rule.target_semantics  # non-empty
    assert all(isinstance(s, str) for s in rule.target_semantics)
    assert isinstance(rule.requires_features, frozenset)
    assert all(isinstance(s, str) for s in rule.requires_features)

    # Contract resolves output_format via the base __post_init__.
    contract = contract_mod.WidgetContract()
    assert contract.output_format == "canonical"

    # Capability wires non-empty grammar/rule lists.
    capability = cap_mod.WidgetCapability()
    assert capability.get_grammars()
    assert capability.get_rules()

    # End-to-end: never-matching grammar => MISSING.
    from paxman.api import canonicalize
    from paxman.core.discovery import register_capability, reset_registry
    from paxman.core.domain import Resolution

    reset_registry()
    register_capability(capability)
    result = canonicalize("scaffold probe", capability.create_contract())
    assert result.status is Resolution.MISSING


@pytest.mark.unit
def test_wires_capabilities_init() -> None:
    """The import line + __all__ entry appear in alphabetical position."""
    _run(*_ARGS)
    text = _INIT.read_text(encoding="utf-8")

    import_line = (
        "from paxman.capabilities.Widget.capability import WidgetCapability as Widget"
    )
    assert import_line in text

    # Parse __all__ and confirm Widget is present and the list stays sorted.
    import ast

    tree = ast.parse(text)
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
        ):
            entries = [e.value for e in node.value.elts]  # type: ignore[attr-defined]
            assert "Widget" in entries
            assert entries == sorted(entries)
            break
    else:  # pragma: no cover
        raise AssertionError("__all__ not found in capabilities/__init__.py")


@pytest.mark.unit
def test_skeleton_passes_the_full_gate(tmp_path: Path) -> None:
    """Generated skeleton + test stubs pass a subprocess pytest run."""
    _run(*_ARGS)

    log = tmp_path / "widget_gate.log"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(_TESTS), "-q"],
        capture_output=True,
        text=True,
    )
    log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    assert proc.returncode == 0, log.read_text(encoding="utf-8")
