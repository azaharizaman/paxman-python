# Shared Vocabulary Snapshot — Currency / Money

Source of truth for CLDR currency data and ISO 4217 list-one.

- Authority: Unicode CLDR v47 (en + es) and ISO 4217 (2015 list-one snapshot).
- Canonical file: `currency_snapshot.json` (JSON, UTF-8, sorted keys).
- Generated outputs: `paxman/capabilities/Currency/{grammar,rules}/data/*` and `paxman/capabilities/Money/{grammar,rules}/data/*` via `tools/regenerate_currency_data.py`.
- Edit workflow: update snapshot JSON (with citation), then `uv run python tools/regenerate_currency_data.py` and `--check` in CI.

Mandate M8: Sibling imports remain banned. Shared vocabularies regenerate into per-capability tables, never imported across capabilities.
