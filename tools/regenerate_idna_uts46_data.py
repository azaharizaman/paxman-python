"""Regenerate paxman/capabilities/URL/rules/data/idna_uts46_mapping.py.

Usage:
    uv run python tools/regenerate_idna_uts46_data.py

Reads the committed UTS #46 IdnaMappingTable snapshot and emits the data
module. Run manually when the snapshot is refreshed. Standard library only.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = _REPO_ROOT / "paxman/capabilities/URL/rules/data/idna_uts46_mapping.txt"
OUTPUT = _REPO_ROOT / "paxman/capabilities/URL/rules/data/idna_uts46_mapping.py"
LINE_LENGTH = 88  # must match ruff's line-length in pyproject.toml
IDNA_VERSION = "15.1.0"  # pinned UTS #46 version

_MAPPED_STATUSES = frozenset({"mapped", "deviation"})


def _parse_snapshot() -> tuple[dict[str, str], dict[str, str]]:
    """Return (statuses, mappings) parsed from the committed snapshot.

    statuses maps every range token (single code point or ``start..end``)
    to its UTS #46 status. mappings maps only the rows whose status is
    ``mapped`` or ``deviation`` to their target sequence (space-separated
    uppercase hex, as written). A mapped/deviation row that lacks a
    mapping field is recorded in statuses only.
    """
    statuses: dict[str, str] = {}
    mappings: dict[str, str] = {}
    for line in SNAPSHOT.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = [f.partition("#")[0].strip() for f in stripped.split(";")]
        range_token, status = fields[0], fields[1]
        statuses[range_token] = status
        if status in _MAPPED_STATUSES and len(fields) > 2 and fields[2]:
            mappings[range_token] = fields[2]
    return statuses, mappings


def _emit_str_table(entries: dict[str, str]) -> str:
    """Emit a dict literal with ruff-format-compliant line lengths.

    Single-line when the whole table fits within 88 columns; otherwise
    multiline (one entry per line, magic trailing comma).
    """

    one_line = (
        "{" + ", ".join(f'"{key}": "{value}"' for key, value in entries.items()) + "}"
    )
    if len(one_line) <= LINE_LENGTH:
        return one_line
    blocks = [f'    "{key}": "{value}",' for key, value in entries.items()]
    return "{\n" + "\n".join(blocks) + "\n}"


def _build_module(statuses: dict[str, str], mappings: dict[str, str]) -> str:
    """Assemble the generated module text for the parsed snapshot tables."""

    doc = (
        '"""UTS #46 IdnaMappingTable data — GENERATED, do not edit by hand.\n'
        "\n"
        "Source: https://www.unicode.org/Public/idna/15.1.0/IdnaMappingTable.txt\n"
        f"Version: {IDNA_VERSION}\n"
        "Regenerate with: uv run python tools/regenerate_idna_uts46_data.py\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n\n"
        f'IDNA_VERSION = "{IDNA_VERSION}"\n\n'
        "IDNA_STATUS: dict[str, str] = " + _emit_str_table(statuses) + "\n\n"
        "IDNA_MAPPED: dict[str, str] = " + _emit_str_table(mappings) + "\n"
    )
    if "output_format" in doc:  # purity guard — see test_no_output_format_token
        raise RuntimeError("generated module must not contain 'output_format'")
    return doc


def render() -> str:
    """Return the generated module text (pure — does not touch OUTPUT)."""

    statuses, mappings = _parse_snapshot()
    return _build_module(statuses, mappings)


def main() -> None:
    statuses, mappings = _parse_snapshot()
    OUTPUT.write_text(_build_module(statuses, mappings), encoding="utf-8")
    print(f"wrote {OUTPUT}: {len(statuses)} statuses, {len(mappings)} mappings")


if __name__ == "__main__":
    main()
