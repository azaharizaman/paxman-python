# CAPABILITIES KNOWLEDGE BASE

## OVERVIEW
The deepest directory in the repo (87 py files): 6 self-contained capability packages (Country, Date, Email, IP, ISBN, Phone), each an independent recognize→validate→resolve mini-system wired into the shared pipeline via `paxman.core`. Most work landing here is: add a capability, tweak recognition/validation for one, or regenerate data.

## STRUCTURE
```
paxman/capabilities/
├── __init__.py          # registration imports + __all__ (see NOTES)
├── <Name>/              # one per capability (Country, Date, Email, IP, ISBN, Phone)
│   ├── notation.py      # frozen slots dataclass — the token type
│   ├── contract.py      # frozen CapabilityContract subclass (no slots)
│   ├── capability.py    # Capability[NotationT] subclass — wiring
│   ├── grammar/         # recognizers (one file per grammar)
│   ├── rules/           # validators (one file per publication)
│   └── rules/data/      # generated/frozen data (Country, Phone, ISBN)
└── one-offs             # Country/name_normalization.py, Phone/grammar/common.py
```

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Add a new capability | root `HOW_TO_ADD_NEW_CAPABILITY.md` (54KB spec — read first) |
| Wire grammars+rules | `<Name>/capability.py` → `get_grammars()`, `get_rules()`, static `create_contract()`, optional `format_value()` |
| Feature flags / active grammars | `<Name>/contract.py` → `include_*` fields + `active_grammars` property |
| Token shape | `<Name>/notation.py` |
| Recognition | `<Name>/grammar/` |
| Validation | `<Name>/rules/` |
| Generated data | `<Name>/rules/data/` (ISBN: regenerate via `tools/regenerate_isbn_range_data.py`) |
| Register a capability | `paxman/capabilities/__init__.py` (import + `__all__`) → `paxman/core/discovery.py` |

## CONVENTIONS
- Capability class: `Capability[NotationT]` subclass; `name` lowercase ("email", "isbn"); `version` "1.0.0"; static `create_contract()` factory forwarding all kwargs; `format_value()` only where presentation varies (Date, Phone, ISBN).
- Contracts: `@dataclass(frozen=True)` extending `CapabilityContract`, NO slots. Feature flags as `include_*` kwargs (include_isbn10, include_range_validation, include_ipv6, include_obfuscated, include_localized, include_historical) plus plain config (default_country, two_digit_base_year). `active_grammars` derives from the flags; `_extra_dict_fields()` feeds the replay hash.
- Notation: `@dataclass(frozen=True, slots=True)` — the sole type parameter of the capability's `Grammar[NotationT]` / `Rule[NotationT]`.
- Grammar: one file = one recognizer, unique snake_case name (`isbn13_recognition.py`); returns span-bearing `RecognitionMatch`; never validates, dedups, orders, or maps tokens to canonical values.
- Rule: one file = one publication (`iso_2108_ed2017.py`); class = one spec section; declares `name` ("Section 5.3-isbn13-check-digit"), `strategy`, `provenance`, `citation`, `target_grammars`, `requires_features`.
- Generated data (`rules/data/`): typed tuples/dicts only, zero logic, produced from a source snapshot (ISBN XML → `range_message.py`) or frozen vendor data (`iso_3166_ed2024.py`, `e164_country_codes.py`).
- Grammar-layer name data lives in `grammar/data/` (Country: english/chinese/localized/historical names) — data modules, not behavior.

## ANTI-PATTERNS (THIS DIRECTORY)
- Don't imitate the one-offs: `Country/name_normalization.py` and `Phone/grammar/common.py` are legacy exceptions, not patterns to copy.
- Don't hand-edit generated `rules/data/` modules — change the source snapshot and regenerate, or the module drifts from its authority.
- Don't add `Section6_1`-style rule class names outside Phone: the N801 per-file-ignore in pyproject is scoped to `Phone/rules/*.py` (and its tests) only.
- No cross-capability imports — a capability package imports only from `paxman.core`, never from a sibling `paxman.capabilities.*`.
- No presentation logic in rules/grammars — `format_value()` is the only seam (ISBN hyphenation lives in `capability.py`, not a rule).
- No additions to `__init__.py` without matching `__all__` — the export list is the registration surface.

## NOTES
- **Known drift**: `__init__.py` exports Country, Date, Email, ISBN, Phone — **IP is missing**; import from `paxman.capabilities.IP.capability` directly. Not test-enforced.
- `__init__.py` acronym aliases (`ISBNCapability as ISBN`) trip N814; covered by the scoped per-file-ignore in pyproject — don't add inline `# noqa`.
- Root AGENTS.md is authoritative for pipeline flow, domain objects, and quality gates; this file adds only capability-package specifics.
