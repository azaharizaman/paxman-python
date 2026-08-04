# F3 Recognition/Validation Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Country name grammars recognize meaning-neutral representations while provenance-backed rules alone assign canonical country values.

**Architecture:** Keep Country recognition key sets separate from ISO, CLDR, and ISO 3166-3 rule mappings. Share one syntax normalizer between grammar membership checks and rule lookups, return the trimmed input token from `NameGrammar`, and preserve F2 rule-gating semantics so disabled localized names are `INVALID` rather than falsely ISO-backed successes.

**Tech Stack:** Python 3.11, frozen dataclass notation, pytest, Hypothesis-compatible pytest layout, `uv`, Ruff, Pyright strict mode, import-linter.

**Design reference:** `docs/superpowers/specs/2026-08-03-f3-recognition-validation-boundary-design.md`

---

## File Map

**Create**

- `paxman/capabilities/Country/name_normalization.py` — shared syntax-only normalization for Country name recognition and rule lookups.
- `tests/capabilities/country/test_data_consistency.py` — verifies every shipped name recognition key is covered by rule data.

**Modify**

- `paxman/capabilities/Country/grammar/data/english_names.py` — replace canonical-valued dictionary with normalized recognition keys.
- `paxman/capabilities/Country/grammar/data/historical_names.py` — replace canonical-valued dictionary with normalized recognition keys.
- `paxman/capabilities/Country/grammar/data/chinese_names.py` — replace canonical-valued dictionary with normalized recognition keys.
- `paxman/capabilities/Country/grammar/name_recognition.py` — return the recognized token, never a canonical name.
- `paxman/capabilities/Country/rules/data/iso_3166_ed2024.py` — add current English grammar aliases to ISO synonym data.
- `paxman/capabilities/Country/rules/data/iso_3166_ed2020_part3.py` — add historical aliases currently rescued by grammar-side canonicalization.
- `paxman/capabilities/Country/rules/iso_3166_ed2024.py` — normalize ISO name/synonym lookups.
- `paxman/capabilities/Country/rules/iso_3166_historical_ed2020.py` — normalize historical-name lookups.
- `paxman/capabilities/Country/rules/cldr_localized_ed2025.py` — normalize localized-name lookups.
- `tests/capabilities/country/test_grammar.py` — change name grammar assertions from canonical output to raw-token output.
- `tests/capabilities/country/test_rules.py` — cover rule-owned alias, localized, historical, and normalization behavior.
- `tests/integration/test_country_pipeline.py` — lock status, candidate, and provenance behavior through the real pipeline.
- `HOW_TO_ADD_NEW_CAPABILITY.md` — state that grammars cannot assign semantic meaning.
- `README.md` — correct the localized Country example and feature flag.
- `capability_homogeneity_audit.md` — add the completed F3 findings and behavior matrix.

**Do not modify**

- `paxman/engine/orchestrator.py` — F1 affinity and F2 feature gating already provide the required pipeline seam.
- `paxman/core/domain.py` — `CountryNotation` already carries the representation needed by the rules.
- Phone grammars — separator stripping is syntax/presentation normalization and is explicitly accepted by F3.

---

## Task 1: Lock the Boundary With Failing Tests

**Files:**
- Modify: `tests/capabilities/country/test_grammar.py`
- Modify: `tests/integration/test_country_pipeline.py`

- [ ] **Step 1: Add the grammar red tests**

Replace the current canonicalization assertions in `TestNameGrammar` with tests that require the trimmed input token to survive recognition:

```python
def test_preserves_english_alias_token(self) -> None:
    results = self.grammar.recognize("USA")
    assert results == [CountryNotation(shape="name", value="USA")]

def test_preserves_localized_token(self) -> None:
    results = self.grammar.recognize("马来西亚")
    assert results == [CountryNotation(shape="name", value="马来西亚")]

def test_normalizes_only_for_membership(self) -> None:
    results = self.grammar.recognize("  Côte d'Ivoire  ")
    assert results == [CountryNotation(shape="name", value="Côte d'Ivoire")]
```

Retain the existing unknown, empty, and punctuation-recognition cases, changing only their expected notation values when the input is recognized.

- [ ] **Step 2: Add the provenance red tests**

Append integration tests that prove localized resolution is owned by CLDR and disabled localized input is not accepted by ISO:

```python
def test_localized_name_disabled_is_invalid_without_iso_provenance(self) -> None:
    register_capability(CountryCapability())
    result = run_capability("马来西亚", CountryCapability.create_contract())

    assert result.status == Resolution.INVALID
    assert result.candidates == ()

def test_localized_name_enabled_uses_unicode_provenance(self) -> None:
    register_capability(CountryCapability())
    contract = CountryCapability.create_contract(include_localized=True)
    result = run_capability("马来西亚", contract)

    assert result.status == Resolution.SUCCESS
    assert result.canonicalized_value == "MY"
    assert {p.authority for c in result.candidates for p in c.provenance} == {
        "Unicode"
    }
```

Use the existing autouse registry fixture. The first test intentionally locks the selected F2 behavior: recognized localized notation plus filtered authority rule means `INVALID`.

- [ ] **Step 3: Run the focused red suite**

Run:

```bash
uv run pytest tests/capabilities/country/test_grammar.py tests/integration/test_country_pipeline.py -q
```

Expected: FAIL because `NameGrammar` still substitutes canonical names and Chinese input still reaches the ISO name rule.

---

## Task 2: Add Shared Syntax Normalization and Recognition Keys

**Files:**
- Create: `paxman/capabilities/Country/name_normalization.py`
- Modify: `paxman/capabilities/Country/grammar/data/english_names.py`
- Modify: `paxman/capabilities/Country/grammar/data/historical_names.py`
- Modify: `paxman/capabilities/Country/grammar/data/chinese_names.py`
- Modify: `paxman/capabilities/Country/grammar/name_recognition.py`

- [ ] **Step 1: Add the shared normalizer test**

Add unit coverage in `tests/capabilities/country/test_grammar.py` for the shared normalizer:

```python
from paxman.capabilities.Country.name_normalization import normalize_name


def test_normalize_name_is_syntax_only() -> None:
    assert normalize_name("  Côte d'Ivoire  ") == "COTE DIVOIRE"
    assert normalize_name("马来西亚") == "马来西亚"
```

Run the test and verify it fails with an import or missing-symbol failure before creating the module.

- [ ] **Step 2: Implement `normalize_name()` minimally**

Move the existing NFKD, combining-mark removal, alphanumeric/whitespace filtering, whitespace collapsing, uppercasing, and trimming behavior from `name_recognition.py` into:

```python
def normalize_name(text: str) -> str:
    """Return a syntax-normalized Country name lookup key."""
```

Do not add transliteration, fuzzy matching, synonym resolution, or canonical-value lookup.

- [ ] **Step 3: Convert grammar data to key sets**

Preserve every existing dictionary key in the three grammar data files, but remove all canonical-value payloads. Export typed `frozenset[str]` constants named:

```python
ENGLISH_NAME_KEYS
HISTORICAL_NAME_KEYS
CHINESE_NAME_KEYS
```

Each key must be normalized with `normalize_name()` at module construction or stored in the already-normalized form used by the current tables. The data modules must contain no token-to-country mapping.

- [ ] **Step 4: Refactor `NameGrammar`**

Import the three key sets and `normalize_name()`. Build one private union of recognized keys. For non-empty input:

1. Trim outer whitespace into `trimmed`.
2. Compute `normalize_name(trimmed)` only for membership.
3. Return `CountryNotation(shape="name", value=trimmed)` when the key is known.
4. Return `[]` for unknown input.

Do not return an English name, alpha-2 code, alpha-3 code, historical code, or localized canonical value.

- [ ] **Step 5: Run the grammar green suite**

Run:

```bash
uv run pytest tests/capabilities/country/test_grammar.py -q
```

Expected: PASS, including the raw-token tests from Task 1. Existing rule and integration tests may still fail because rule lookups have not yet been migrated.

---

## Task 3: Move All Current Grammar-Rescued Meaning Into Rule Data

**Files:**
- Modify: `paxman/capabilities/Country/rules/data/iso_3166_ed2024.py`
- Modify: `paxman/capabilities/Country/rules/data/iso_3166_ed2020_part3.py`

- [ ] **Step 1: Add the missing ISO synonym mappings**

For every English grammar key whose value previously pointed to an official English name, add a normalized synonym mapping to `SYNONYM_TO_ALPHA2`. Resolve each target through the existing official `NAME_TO_ALPHA2` table; do not invent a code. This must cover the current grammar aliases, including `AMERICA`, `ENGLAND`, `GREAT BRITAIN`, `HOLLAND`, `CZECH REPUBLIC`, `IVORY COAST`, `UNITED STATES OF AMERICA`, Saint variants, and spaced abbreviations such as `U S A`.

Keep official ISO names in `NAME_TO_ALPHA2`; use `SYNONYM_TO_ALPHA2` for non-official representations.

- [ ] **Step 2: Add the missing historical mappings**

Extend `FORMER_NAME_TO_ALPHA2` for the grammar aliases that were previously converted to another historical name:

```python
"EAST GERMAN": "DD"
"GDR": "DD"
"METROPOLITAN FRANCE": "FX"
"USSR SOVIET SOCIALIST REPUBLICS": "SU"
"VIET CONG": "VD"
"PEOPLES DEMOCRATIC REPUBLIC OF YEMEN": "YD"
```

Use the existing ISO 3166-3 codes and provenance. Do not map historical names to successor-country alpha-2 codes.

- [ ] **Step 3: Preserve the localized authority table**

Do not move Chinese, Spanish, or French localized mappings into ISO data. `LOCALIZED_TO_ALPHA2` remains the CLDR-owned mapping and remains guarded by `requires_features = frozenset({"include_localized"})`.

- [ ] **Step 4: Add data-level regression tests**

In `tests/capabilities/country/test_rules.py`, add parameterized cases proving the moved mappings are rule-owned:

```python
@pytest.mark.parametrize(
    ("value", "expected"),
    [("USA", "US"), ("Holland", "NL"), ("Côte d'Ivoire", "CI")],
)
def test_iso_name_rule_validates_aliases(value: str, expected: str) -> None:
    notation = CountryNotation(shape="name", value=value)
    rule = SectionNames()
    assert rule.matches(notation, CountryCapability.create_contract())
    assert rule.normalize(notation, CountryCapability.create_contract()) == expected
```

Add equivalent raw-name cases for `SectionHistoricalNames` and `SectionLocalizedNames`, including `"VIET CONG" -> "VD"` and `"马来西亚" -> "MY"`.

- [ ] **Step 5: Run the rule red/green suite**

Run:

```bash
uv run pytest tests/capabilities/country/test_rules.py -q
```

Expected: the new tests pass only after the mappings are present; existing tests must remain green.

---

## Task 4: Normalize Provenance-Backed Rule Lookups

**Files:**
- Modify: `paxman/capabilities/Country/rules/iso_3166_ed2024.py`
- Modify: `paxman/capabilities/Country/rules/iso_3166_historical_ed2020.py`
- Modify: `paxman/capabilities/Country/rules/cldr_localized_ed2025.py`

- [ ] **Step 1: Build normalized lookup views**

For every name-based rule table, build a module-level normalized view with the same values and `normalize_name(key)` as the key. Apply this to:

- ISO `NAME_TO_ALPHA2` and `SYNONYM_TO_ALPHA2`.
- ISO 3166-3 `FORMER_NAME_TO_ALPHA2`.
- CLDR `LOCALIZED_TO_ALPHA2`.

Do not normalize alpha-2, alpha-3, or numeric code tables through the name normalizer.

- [ ] **Step 2: Change only name matching and normalization**

`matches()` must check the normalized notation value against the rule’s normalized name view. `normalize()` must retrieve the same normalized key and then apply the existing `output_format` behavior. Preserve all existing target grammars, feature metadata, provenance constants, and historical round-trip handling.

- [ ] **Step 3: Add punctuation/accent coverage**

Add tests for `Côte d'Ivoire`, `Cote d'Ivoire`, and whitespace variants. The grammar may preserve the input token, while the rule must resolve equivalent syntax forms through the shared normalizer.

- [ ] **Step 4: Run Country capability tests**

Run:

```bash
uv run pytest tests/capabilities/country -q
```

Expected: PASS with no rule method raising for a notation that `matches()` accepted.

---

## Task 5: Add Recognition-to-Rule Data Consistency Coverage

**Files:**
- Create: `tests/capabilities/country/test_data_consistency.py`

- [ ] **Step 1: Write the failing coverage test**

Import all three grammar key sets and all name-based rule maps. Normalize rule keys before comparison and assert:

```python
    grammar_keys = (
        ENGLISH_NAME_KEYS | HISTORICAL_NAME_KEYS | CHINESE_NAME_KEYS
    )
    rule_keys = (
        {normalize_name(key) for key in NAME_TO_ALPHA2}
        | {normalize_name(key) for key in SYNONYM_TO_ALPHA2}
        | {normalize_name(key) for key in FORMER_NAME_TO_ALPHA2}
        | {normalize_name(key) for key in LOCALIZED_TO_ALPHA2}
    )

    assert grammar_keys <= rule_keys
```

Run it before completing the data migration and confirm it identifies any omitted grammar representation.

- [ ] **Step 2: Make the coverage test pass**

Add the missing rule aliases or correct the recognition key catalog only when the representation is not intended to be recognized. Do not weaken the assertion and do not put canonical values back into grammar data.

- [ ] **Step 3: Verify the isolated consistency test**

Run:

```bash
uv run pytest tests/capabilities/country/test_data_consistency.py -q
```

Expected: PASS with zero uncovered recognition keys.

---

## Task 6: Lock Full-Pipeline Status and Provenance Semantics

**Files:**
- Modify: `tests/integration/test_country_pipeline.py`
- Modify: `tests/e2e/test_canonicalize.py` if the Country examples are located there.

- [ ] **Step 1: Rewrite localized tests**

Use these exact assertions:

```python
default = CountryCapability.create_contract()
localized = CountryCapability.create_contract(include_localized=True)

assert run_capability("中国", default).status == Resolution.INVALID
localized_result = run_capability("中国", localized)
assert localized_result.status == Resolution.SUCCESS
assert localized_result.canonicalized_value == "CN"
assert localized_result.candidates[0].provenance[0].authority == "Unicode"

assert run_capability("Alemania", default).status == Resolution.INVALID
assert run_capability("Alemania", localized).canonicalized_value == "DE"
```

These tests prove the grammar recognizes the representation while F2 controls whether the authority rule can produce a candidate.

- [ ] **Step 2: Preserve ISO and historical behavior**

Keep and strengthen tests for `United States -> US`, `USA -> US`, `Malaysia -> MY`, `Burma -> BU`, and `USSR -> SU`. Assert that ISO names use ISO provenance and historical names use ISO 3166-3 provenance.

- [ ] **Step 3: Verify ambiguity and output-format behavior**

Run the Country integration suite and confirm that changing `output_format` changes only the rendered candidate value, not whether recognition or validation occurs. Do not change F1 candidate routing or status computation.

- [ ] **Step 4: Run the pipeline suite**

Run:

```bash
uv run pytest tests/integration/test_country_pipeline.py tests/e2e/test_canonicalize.py -q
```

Expected: PASS, with localized candidates carrying `Unicode` provenance and no ISO candidate for localized-only input.

---

## Task 7: Update Documentation and Audit Evidence

**Files:**
- Modify: `HOW_TO_ADD_NEW_CAPABILITY.md`
- Modify: `README.md`
- Modify: `capability_homogeneity_audit.md`

- [ ] **Step 1: Document the grammar rule**

Add to the grammar guidance:

```text
Grammars may normalize syntax and use recognition-key sets, but they must not
map a token to a canonical value or import provenance-backed semantic tables.
Validation rules own every token-to-meaning decision and produce candidates
with provenance.
```

Clarify that a grammar lookup table may contain keys only, while a rule lookup table contains authority-backed mappings.

- [ ] **Step 2: Correct the README localized example**

Change the Country `Deutschland` example to construct:

```python
contract = Country.create_contract(include_localized=True)
```

Document that the result is validated by CLDR/Unicode, not ISO merely because the grammar recognized a localized token.

- [ ] **Step 3: Add an F3 addendum to the audit**

Record the old failure, the new raw-token behavior, the `INVALID`/`SUCCESS` localized matrix, the shared normalizer, the coverage test, and the intentional replay-hash/provenance change for affected inputs. State explicitly that Phone separator cleanup remains accepted syntax normalization.

- [ ] **Step 4: Review documentation for contradictions**

Run:

```bash
rg -n "canonical.*grammar|grammar.*canonical|Deutschland|include_localized|NameGrammar" HOW_TO_ADD_NEW_CAPABILITY.md README.md ARCHITECTURE.md capability_homogeneity_audit.md
```

Remove only statements that claim the grammar assigns canonical meaning or that the README example works without its feature flag.

---

## Task 8: Refactor, Verify, and Handoff

**Files:** All files changed in Tasks 1–7.

- [ ] **Step 1: Run formatting and static checks**

Run:

```bash
uv run ruff format paxman/capabilities/Country tests/capabilities/country tests/integration/test_country_pipeline.py
uv run ruff check paxman/ tests/
uv run pyright
import-linter lint
```

Fix only F3-caused failures. Do not add `# noqa`, `# type: ignore`, `as any`, or broad exception suppression.

- [ ] **Step 2: Run the complete test suite**

Run:

```bash
uv run pytest tests/ -q
```

Expected: all existing tests plus the new F3 tests pass. Any changed replay hash must be attributable to the documented localized provenance or route correction, not nondeterministic ordering.

- [ ] **Step 3: Perform the manual pipeline check**

Run a real Python driver through `run_capability`:

```bash
uv run python - <<'PY'
from paxman.capabilities.Country.capability import CountryCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.engine.orchestrator import run_capability

reset_registry()
register_capability(CountryCapability())

for text, contract in (
    ("Malaysia", CountryCapability.create_contract()),
    ("马来西亚", CountryCapability.create_contract()),
    ("马来西亚", CountryCapability.create_contract(include_localized=True)),
    ("Burma", CountryCapability.create_contract(include_historical=True)),
):
    result = run_capability(text, contract)
    print(text, result.status.value, result.canonicalized_value,
          [p.authority for c in result.candidates for p in c.provenance])
PY
```

Expected: Malaysia succeeds through ISO, disabled Chinese input is `invalid` with no candidates, enabled Chinese input succeeds through Unicode, and Burma succeeds through ISO 3166-3.

- [ ] **Step 4: Run diagnostics on every changed Python file**

Run `lsp_diagnostics` for every changed `.py` file and resolve all F3-caused errors before handoff.

- [ ] **Step 5: Record the implementation handoff**

Report the design file, plan file, exact verification commands and results, intentional status/provenance changes, and any pre-existing failures. Do not claim replay hashes are unchanged for inputs whose validating authority changes.

---

## Dependency Order

1. Task 1 establishes red behavior tests.
2. Task 2 creates the shared normalizer and raw-token grammar seam.
3. Task 3 migrates missing semantic mappings into provenance-backed data.
4. Task 4 updates rule lookups to consume raw tokens.
5. Task 5 prevents future recognition/rule data drift.
6. Task 6 verifies actual pipeline semantics and provenance.
7. Task 7 updates contributor and user-facing documentation.
8. Task 8 runs the full quality and manual verification gates.

Tasks 3 and 4 can be split between independent workers only after Task 2's
normalizer interface is fixed. Tasks 5 and 6 depend on the completed data and
rule migrations.
