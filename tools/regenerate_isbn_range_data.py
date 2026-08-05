"""Regenerate paxman/capabilities/ISBN/rules/data/range_message.py.

Usage:
    uv run python tools/regenerate_isbn_range_data.py

Reads the committed Range Message snapshot XML and emits the data module.
Run manually when the snapshot is refreshed. Standard library only.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = (
    _REPO_ROOT / "paxman/capabilities/ISBN/rules/data/range_message_2026-08-05.xml"
)
OUTPUT = _REPO_ROOT / "paxman/capabilities/ISBN/rules/data/range_message.py"
LINE_LENGTH = 88  # must match ruff's line-length in pyproject.toml


def _collect_rules(parent: ET.Element) -> list[tuple[str, str, int]]:
    """Return [(range_start, range_end, length), ...], skipping Length 0."""
    rules: list[tuple[str, str, int]] = []
    for rule in parent.findall("Rules/Rule"):
        length = int(rule.findtext("Length", "0") or "0")
        if length == 0:
            continue  # "range not allocated" — never emitted
        range_text = rule.findtext("Range", "") or ""
        if "-" not in range_text:
            raise ValueError(f"malformed Range {range_text!r} in {parent.tag}")
        start, _, end = range_text.partition("-")
        rules.append((start, end, length))
    return rules


def _emit_rule_table(entries: list[tuple[str, list[tuple[str, str, int]]]]) -> str:
    """Emit a dict literal with ruff-format-compliant line lengths.

    Single-line when the whole entry fits within 88 columns;
    otherwise multiline (one element per line, magic trailing comma).
    """

    blocks: list[str] = []
    for key, rules in entries:
        if not rules:
            blocks.append(f'    "{key}": (),')
            continue
        elements = ", ".join(
            f'("{start}", "{end}", {length})' for start, end, length in rules
        )
        if len(rules) == 1:
            # Keep the outer parens a real 1-tuple of tuples, matching the
            # magic-trailing-comma form ruff itself would emit on collapse.
            elements += ","
        one_line = f'    "{key}": ({elements}),'
        if len(one_line) <= LINE_LENGTH:
            blocks.append(one_line)
            continue
        tuples = ",\n        ".join(
            f'("{start}", "{end}", {length})' for start, end, length in rules
        )
        blocks.append(f'    "{key}": (\n        {tuples},\n    ),')
    return "{\n" + "\n".join(blocks) + "\n}"


def main() -> None:
    root = ET.parse(SNAPSHOT).getroot()
    serial = root.findtext("MessageSerialNumber", "")
    message_date = root.findtext("MessageDate", "")

    prefixes = [
        (e.findtext("Prefix", ""), _collect_rules(e))
        for e in root.findall("EAN.UCCPrefixes/EAN.UCC")
    ]
    groups = [
        (g.findtext("Prefix", ""), _collect_rules(g))
        for g in root.findall("RegistrationGroups/Group")
    ]

    doc = (
        '"""ISBN Range Message snapshot data — GENERATED, do not edit by hand.\n'
        "\nSource: https://www.isbn-international.org/export_rangemessage.xml\n"
        f"MessageSerialNumber: {serial}\n"
        f"MessageDate: {message_date}\n"
        "Regenerate with: uv run python tools/regenerate_isbn_range_data.py\n"
        '"""\n'
        "\nfrom __future__ import annotations\n\n"
        f'MESSAGE_SERIAL = "{serial}"\n'
        f'MESSAGE_DATE = "{message_date}"\n\n'
        "EAN_PREFIX_RULES: dict[str, tuple[tuple[str, str, int], ...]] = "
        + _emit_rule_table(prefixes)
        + "\n\nGROUP_RULES: dict[str, tuple[tuple[str, str, int], ...]] = "
        + _emit_rule_table(groups)
        + "\n"
    )
    if "output_format" in doc:  # purity guard — see test_no_output_format_token
        raise RuntimeError("generated module must not contain 'output_format'")
    OUTPUT.write_text(doc, encoding="utf-8")
    emitted = sum(len(r) for _, r in prefixes) + sum(len(r) for _, r in groups)
    print(f"wrote {OUTPUT}: {emitted} rules")


if __name__ == "__main__":
    main()
