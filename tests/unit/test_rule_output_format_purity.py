"""CI-enforced purity of validation-rule modules.

Validation rules must not reference the presentation contract field
``output_format``. Since the centralize-output-format migration, formatting is
owned solely by ``Capability.format_value()``: a rule's ``normalize()`` always
emits the capability's default canonical representation regardless of the
requested format.

This test scans the *source text* of every module matching
``paxman/capabilities/*/rules/*.py`` and fails when the exact token
``output_format`` appears — in code, comments, or docstrings. The scan is a
plain substring check on raw text, so there is no whitelist for comments,
docstrings, ``getattr()`` calls, or alternate spellings: a rule module must
have no reference to the presentation field at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RULES_GLOB = "*/rules/*.py"
_CAPABILITIES_DIR = _REPO_ROOT / "paxman" / "capabilities"


def _rule_modules() -> list[Path]:
    """Return every validation-rule module under the capability layout."""
    return sorted(_CAPABILITIES_DIR.glob(_RULES_GLOB))


@pytest.mark.unit
def test_no_rule_module_references_output_format() -> None:
    """No validation-rule module may contain the token ``output_format``.

    Formatting is the capability's responsibility. Any reference to
    ``output_format`` in a rule module — code, comment, or docstring — is a
    regression of the rule-purity invariant and must fail CI with the
    offending module's path relative to the repository root.
    """
    offenders = [
        module.relative_to(_REPO_ROOT).as_posix()
        for module in _rule_modules()
        if "output_format" in module.read_text(encoding="utf-8")
    ]
    assert offenders == [], (
        "Rule modules must not reference output_format; formatting is owned by "
        f"Capability.format_value(). Offending modules: {sorted(offenders)}"
    )
