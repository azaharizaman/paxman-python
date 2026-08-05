"""Regenerate paxman/capabilities/ISBN/rules/data/range_message.py.

Usage:
    uv run python tools/regenerate_isbn_range_data.py

Reads the committed Range Message snapshot XML and emits the data module.
Run manually when the snapshot is refreshed. Standard library only.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

SNAPSHOT = Path("paxman/capabilities/ISBN/rules/data/range_message_2026-08-05.xml")
OUTPUT = Path("paxman/capabilities/ISBN/rules/data/range_message.py")


def _collect_rules(parent: ET.Element) -> list[tuple[str, str, int]]:
    """Return [(range_start, range_end, length), ...], skipping Length 0."""
    rules: list[tuple[str, str, int]] = []
    for rule in parent.findall("Rules/Rule"):
        length = int(rule.findtext("Length", "0") or "0")
        if length == 0:
            continue  # "range not allocated" — never emitted
        start, _, end = (rule.findtext("Range", "") or "").partition("-")
        rules.append((start, end, length))
    return rules


def _emit_rule_table(entries: list[tuple[str, list[tuple[str, str, int]]]]) -> str:
    blocks: list[str] = []
    for key, rules in entries:
        if not rules:
            blocks.append(f'    "{key}": (),')
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
    assert "output_format" not in doc  # purity guard — see test_no_output_format_token
    OUTPUT.write_text(doc)
    emitted = sum(len(r) for _, r in prefixes) + sum(len(r) for _, r in groups)
    print(f"wrote {OUTPUT}: {emitted} rules")


if __name__ == "__main__":
    main()
