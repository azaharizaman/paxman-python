# Centralize Output Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply every capability's resolved `output_format` through one engine pipeline while keeping default canonical values unchanged and preserving capability-specific data such as RFC 3966 extensions.

**Architecture:** Validation rules will normalize recognized notation into their capability's default canonical representation only. The engine will call a non-abstract `Capability.format_value()` immediately after `Rule.normalize()` and before candidate deduplication, status calculation, and replay hashing. Date, Phone, and Country will implement format conversion; Email and IP will inherit the identity implementation because they offer no alternative formats.

**Tech Stack:** Python 3.11, `uv`, pytest, Hypothesis, Ruff, Pyright strict, import-linter.

---

## Behavioral Contract

- `CapabilityContract.__post_init__()` remains the only place that resolves `None`, `"default"`, and each capability's default format. No new omission flag or engine-side `None` handling is added.
- A rule's `normalize()` returns the default canonical form regardless of `contract.output_format`.
- The engine formats each validated value before `_dedup_candidates()` and `_determine_status()`. This preserves the current candidate/status/hash ordering and keeps formatting-dependent candidates distinct.
- `Candidate.provenance`, `recognition_rule`, and `validation_rule` remain unchanged. Formatting adds no provenance.
- Default output remains byte-for-byte unchanged.
- Every validation-rule module under `paxman/capabilities/*/rules/` is forbidden from referencing `output_format`; a CI test enforces that formatting is owned by `Capability.format_value()`.
- Explicit formats continue to work for current Date, Phone, and Country pipeline cases.
- RFC 3966 output retains `PhoneNotation.extension`; a value-only formatter is not sufficient.
- Intended behavior change: a pinned ISO Date rule with `output_format="US"` now returns `MM/DD/YYYY` instead of silently returning ISO.
- Localized Country names use the current alpha-2 conversion tables for `alpha3`, `numeric`, and `name` output while retaining CLDR/Unicode provenance; historical former codes with no current-code mapping pass through unchanged for those formats while retaining ISO 3166-3 provenance.
- Literal replay-hash snapshots for one default-format case per built-in capability are captured before Tasks 2–4 and must remain unchanged after the migration.
- No new output formats, contract fields, canonical defaults, dedup keys, status semantics, or replay-hash fields are introduced.

## Files And Responsibilities

- Modify `paxman/core/capability.py`: add the typed, default-identity `format_value()` seam.
- Modify `paxman/engine/orchestrator.py`: pass the capability into `_collect_candidates()` and apply formatting before `Candidate` creation.
- Modify `paxman/capabilities/Date/capability.py`: format ISO canonical dates as US dates when requested.
- Modify `paxman/capabilities/Phone/capability.py`: centrally format E.164 values as RFC 3966 or national values, including extensions.
- Modify `paxman/capabilities/Country/capability.py`: centrally format alpha-2 values as alpha-3, numeric, or name values.
- Modify Date, Phone, and Country rule files: remove output-format branches and emit default canonical values only.
- Modify adjacent rule and property tests: assert rules emit defaults; move presentation assertions to capability/pipeline seams.
- Add `tests/integration/test_format_value_seam.py`: prove the engine invokes the capability formatter at the correct stage.
- Add `tests/integration/test_default_replay_hashes.py`: capture literal default-format replay hashes before the formatting migration and guard byte-identical default behavior.
- Add `tests/unit/test_rule_output_format_purity.py`: fail CI if any validation-rule module references `output_format`.
- Modify `ARCHITECTURE.md` and `HOW_TO_ADD_NEW_CAPABILITY.md`: document the new validation-to-formatting pipeline.

## Task 1: Lock The Engine Seam With A Failing Integration Test

**Files:**
- Create: `tests/integration/test_format_value_seam.py`
- Create: `tests/integration/test_default_replay_hashes.py`
- Modify: `paxman/core/capability.py`
- Modify: `paxman/engine/orchestrator.py`

- [ ] **Step 1: Capture default-format replay hashes before changing production code.**

Create `tests/integration/test_default_replay_hashes.py` with a registry-reset fixture and a parametrized test that registers one fresh built-in capability per case, runs the listed input with that capability's no-argument contract, and compares `result.version_stamp.replay_hash` to these literal pre-migration values:

```python
DEFAULT_REPLAY_HASHES = {
    "date": "cb2e67023a8c74e5eb76913a00eb1756a7ed76c3a3c8bb553a588ac5d03c65b4",
    "country": "3489ca17221e11f98068a4c5e9306a0ebfb06b857bcbaa137fdd3f14a761a70b",
    "email": "dccb1dec8fbd851c360ecb5feb0ed321a00a2ee6931ed2ba6505c0f92f9ffa31",
    "ip": "6709b8b4ca35a7fec0ddc80bf13325af0dfbcf79d17577955a2a8ae41ad8c71a",
    "phone": "c5aec207bcfb3d061585b789ccb3d6cd98d394bffbe0f81c4fcd481132647f3d",
}

DEFAULT_CASES = (
    ("date", DateCapability, "2026-01-15"),
    ("country", CountryCapability, "DE"),
    ("email", EmailCapability, "user@example.com"),
    ("ip", IPCapability, "192.0.2.1"),
    ("phone", PhoneCapability, "+15551234567"),
)
```

The test must compare the literal hash, not a hash computed by a helper in the test. Run this snapshot test before any production changes in Tasks 2–4; a failure means the baseline has changed and must be investigated rather than updating the expected value.

- [ ] **Step 2: Add a capability fixture whose formatter changes a validated value.**

Create a minimal test-only capability with a grammar that recognizes one token, a rule whose `normalize()` returns `"default-value"`, and a `format_value()` implementation that returns `"formatted-value"`. Register it with the existing registry fixture and assert that `run_capability()` returns `Candidate.value == "formatted-value"` and `canonicalized_value == "formatted-value"`.

The test must also assert that the formatter receives the original notation and the contract's resolved output format. Use a literal contract format value, not a mock-derived expected value.

- [ ] **Step 3: Run the focused tests and verify only the new seam test fails.**

Run:

```bash
uv run pytest tests/integration/test_default_replay_hashes.py tests/integration/test_format_value_seam.py -q
```

Expected: the five baseline replay snapshots pass and the formatter-seam test fails because `Capability` has no formatter seam and `_collect_candidates()` currently stores the rule's raw normalized value.

- [ ] **Step 4: Add the default-identity capability interface.**

In `paxman/core/capability.py`, add a fully typed method:

```python
def format_value(
    self,
    value: str,
    output_format: str | None,
    notation: NotationT,
) -> str:
    """Render a default canonical value in the requested format."""
    return value
```

Keep it non-abstract so Email and IP retain identity behavior without no-op overrides. Do not add explicit `None` handling; built-in contracts already resolve omitted/default values before the engine runs.

- [ ] **Step 5: Route formatting before candidate construction.**

Change `_collect_candidates()` to accept `capability: Capability[Any]`. At the existing `rule.normalize()` call, immediately invoke:

```python
canonical = rule.normalize(recognition.notation, recognition.contract)
value = capability.format_value(
    canonical,
    recognition.contract.output_format,
    recognition.notation,
)
```

Construct `Candidate(value=value, ...)`. Update `run_capability()` to pass the selected capability. Do not move `_dedup_candidates()`, `_determine_status()`, `_extract_canonical_value()`, or `_build_version_stamp()`.

- [ ] **Step 6: Run the focused test, baseline snapshots, and static checks.**

Run:

```bash
uv run pytest tests/integration/test_default_replay_hashes.py tests/integration/test_format_value_seam.py -q
uv run ruff check paxman/core/capability.py paxman/engine/orchestrator.py tests/integration/test_format_value_seam.py
uv run pyright
```

Expected: the seam test and all five literal baseline snapshots pass, Ruff exits 0, and Pyright reports no new errors.

## Task 2: Move Date Formatting To `DateCapability`

**Files:**
- Modify: `paxman/capabilities/Date/capability.py`
- Modify: `paxman/capabilities/Date/rules/us_federal_rules_ed2023.py`
- Modify: `paxman/capabilities/Date/rules/en_50160_ed2010.py`
- Modify: `tests/capabilities/date/test_rules.py`
- Modify: `tests/capabilities/date/test_capability.py`
- Modify: `tests/integration/test_date_capability.py`
- Modify: `tests/property/test_rule_properties.py`

- [ ] **Step 1: Add the intended pinned-rule regression test.**

Add an integration test using `Date.create_contract(pinned_rules=["Section 4.3.1-calendar-date"], output_format="US")` and input `"2026-01-15"`. Assert `Resolution.SUCCESS`, `canonicalized_value == "01/15/2026"`, and that the candidate value is also `"01/15/2026"`.

Run the focused test and verify it fails because the ISO rule currently emits ISO unconditionally.

- [ ] **Step 2: Add `DateCapability.format_value()`.**

Implement the identity path for the default ISO format and the explicit US conversion from a validated `YYYY-MM-DD` value to `MM/DD/YYYY`. Use parsing or validated fixed-position fields rather than accepting arbitrary strings. Return the original value for the default path.

- [ ] **Step 3: Remove Date rule-level format branches.**

Change `Section1DateFormat.normalize()` and `Section4DateFormat.normalize()` so both always return `YYYY-MM-DD`. Leave their two-digit-year interpretation and validation logic unchanged. `Section431CalendarDate.normalize()` already emits ISO and should remain default-only.

- [ ] **Step 4: Rewrite rule tests and add formatter tests.**

Change rule tests that pass `output_format="US"` to assert the rule still returns ISO. Add capability-level tests for ISO identity and US formatting. Update the property test so `normalize()` always has ISO shape; add a property covering `DateCapability.format_value()` for valid ISO values.

- [ ] **Step 5: Run Date tests and verify existing ambiguity behavior.**

Run:

```bash
uv run pytest tests/capabilities/date tests/integration/test_date_capability.py tests/integration/test_pipeline.py -q
```

Expected: the pinned ISO test passes; default, US, and European formatting tests pass; Date ambiguity remains `AMBIGUOUS` with two distinct formatted values.

## Task 3: Move Phone Formatting To `PhoneCapability`

**Files:**
- Modify: `paxman/capabilities/Phone/capability.py`
- Modify: `paxman/capabilities/Phone/rules/e164_ed2010.py`
- Modify: `paxman/capabilities/Phone/rules/nanp_ed2024.py`
- Modify: `paxman/capabilities/Phone/rules/rfc_3966_ed2004.py`
- Modify: `tests/capabilities/phone/test_rules.py`
- Modify: `tests/capabilities/phone/test_capability.py`
- Modify: `tests/integration/test_phone_pipeline.py`

- [ ] **Step 1: Add formatter seam tests before migration.**

Add tests for `PhoneCapability.format_value()` covering:

```text
+15551234567, e164 -> +15551234567
+15551234567, rfc3966 -> tel:+15551234567
+15551234567, national -> 5551234567
+15551234567, rfc3966, extension=890 -> tel:+15551234567;ext=890
```

Add an integration regression test with two tel URIs differing only in extensions and `output_format="rfc3966"`; assert the result remains `AMBIGUOUS` and both extension-bearing candidate values remain present.

- [ ] **Step 2: Implement `PhoneCapability.format_value()`.**

Use the existing `split_country_code()` helper for national output. Use `PhoneNotation.extension` only for RFC 3966 output. Preserve the current defensive passthrough for an unassigned country-code prefix. The default E.164 path returns the rule's value unchanged.

- [ ] **Step 3: Remove Phone rule-level formatting.**

Delete `_canonical()` from `e164_ed2010.py` and `nanp_ed2024.py`. Make their rules return the default `+CCNSN` representation. In `rfc_3966_ed2004.py`, make `normalize()` return the default E.164 value without formatting or extension rendering. Keep validation and extension recognition unchanged.

- [ ] **Step 4: Rewrite rule tests and retain pipeline tests.**

Change rule tests for national and RFC 3966 formats to assert default E.164 output. Move presentation assertions to capability tests. Keep integration tests for RFC 3966, national output, and extension preservation as end-to-end protection.

- [ ] **Step 5: Run Phone tests and type checks.**

Run:

```bash
uv run pytest tests/capabilities/phone tests/integration/test_phone_pipeline.py -q
uv run ruff check paxman/capabilities/Phone
uv run pyright
```

Expected: all existing Phone behavior passes, including extension preservation and national output without a default country when the country code is embedded.

## Task 4: Move Country Formatting To `CountryCapability`

**Files:**
- Modify: `paxman/capabilities/Country/capability.py`
- Modify: `paxman/capabilities/Country/rules/iso_3166_ed2024.py`
- Modify: `tests/capabilities/country/test_rules.py`
- Modify: `tests/integration/test_country_pipeline.py`

- [ ] **Step 1: Add formatter tests for all Country alternatives and feature-owned inputs.**

Test default alpha-2 identity and conversion of `DE` to `DEU`, `276`, and `GERMANY`. Test that former codes such as `SU` pass through unchanged for alpha-3/numeric/name requests because they are not present in the current-code conversion tables.

Add integration coverage in `tests/integration/test_country_pipeline.py` with these exact cases:

```python
@pytest.mark.parametrize(
    ("output_format", "expected"),
    [("alpha3", "DEU"), ("numeric", "276"), ("name", "GERMANY")],
)
def test_localized_name_uses_current_format_mapping(
    output_format: str, expected: str
) -> None:
    register_capability(CountryCapability())
    contract = CountryCapability.create_contract(
        include_localized=True, output_format=output_format
    )
    result = run_capability("Alemania", contract)

    assert result.status == Resolution.SUCCESS
    assert result.canonicalized_value == expected
    assert {p.authority for c in result.candidates for p in c.provenance} == {
        "Unicode"
    }
```

Add a parametrized historical case for `"USSR"` with `include_historical=True` and each of `alpha3`, `numeric`, and `name`; assert `Resolution.SUCCESS`, `canonicalized_value == "SU"`, and ISO 3166-3 provenance for every format. This explicitly locks historical passthrough while proving localized names use the centralized current-code formatter.

- [ ] **Step 2: Implement `CountryCapability.format_value()`.**

Reuse the existing ISO 3166-1 data mappings rather than copying tables into the capability. Convert from the rule-produced alpha-2 value for `alpha3`, `numeric`, and `name`; return the value unchanged when the mapping has no entry. Keep alpha-2 as identity.

- [ ] **Step 3: Remove current-format branches from ISO rules.**

Update the four current ISO rule normalizers in `iso_3166_ed2024.py` to return alpha-2 only. Do not alter historical or CLDR rule ownership, provenance, feature gating, or their alpha-2 outputs.

- [ ] **Step 4: Rewrite rule tests and run Country integration tests.**

Change rule tests that currently expect alpha-3/numeric/name output from `normalize()` to expect alpha-2. Keep integration tests asserting requested output formats and historical passthrough.

Run:

```bash
uv run pytest tests/capabilities/country tests/integration/test_country_pipeline.py -q
uv run ruff check paxman/capabilities/Country
uv run pyright
```

Expected: current-code conversions, localized alternate formats, historical passthrough for every requested alternative, localized/historical provenance, and former-code behavior all remain correct.

## Task 5: Add Cross-Capability Contract And Replay Coverage

**Files:**
- Modify: `tests/unit/test_capability_surface.py`
- Create: `tests/unit/test_rule_output_format_purity.py`
- Modify: `tests/integration/test_format_value_seam.py`
- Modify: `tests/integration/test_default_replay_hashes.py`
- Modify: `tests/integration/test_pipeline.py`
- Add or modify: `tests/property/test_format_value_properties.py`

- [ ] **Step 1: Add identity and offered-format surface assertions.**

Assert that every capability with non-empty `OFFERED_OUTPUT_FORMATS` has a formatter that handles each offered format, while Email and IP retain identity behavior. Assert that each capability's formatter default agrees with its contract default.

- [ ] **Step 2: Add a CI-enforced rule-purity test.**

Create `tests/unit/test_rule_output_format_purity.py` that scans every `*.py` file matching `paxman/capabilities/*/rules/*.py` and fails with the relative file paths of any modules containing the token `output_format`. The scan must be source-based and must not whitelist comments, docstrings, `getattr()` calls, or alternate spellings: after this migration, rule modules must have no reference to the presentation contract field at all. Run it with:

```bash
uv run pytest tests/unit/test_rule_output_format_purity.py -q
```

Expected: PASS only when all Date, Phone, Country, Email, and IP rule modules delegate presentation to the capability seam; this is the CI enforcement for the rule-purity invariant, not a manual review instruction.

- [ ] **Step 3: Add replay and candidate-order regressions.**

For a fixed Date ambiguity, Phone RFC 3966 extension, Country conversion, and default Email/IP case, run the same input and contract twice and assert equal `status`, `canonicalized_value`, `candidates`, and `version_stamp.replay_hash`. Keep the literal pre-migration snapshots from Task 1 as a separate compatibility assertion; do not replace them with within-run determinism checks. Assert formatting occurs before deduplication using the two-extension Phone case. Update the existing Date ambiguity test names and docstrings in `tests/integration/test_pipeline.py` so they describe formatting before status/deduplication and assert only the intended invariant: status remains `AMBIGUOUS` because the formatted candidate values remain two distinct values.

- [ ] **Step 4: Add property tests.**

Using known valid canonical samples, assert:

```python
format_value(value, default_format, notation) == value
```

For Date, assert valid ISO values produce valid US values. For Country, assert each current alpha-2 value maps consistently to alpha-3, numeric, and name. Add localized and historical notation samples to assert that localized values use the current mapping while former Country codes pass through unchanged. Do not require former Country codes to map through current-code tables; assert passthrough instead.

- [ ] **Step 5: Run the complete test suite.**

Run:

```bash
uv run pytest -q
```

Expected: all tests pass, including existing pipeline tests that observe formatted output.

## Task 6: Update Architecture Documentation

**Files:**
- Modify: `ARCHITECTURE.md` at the rule/output-format description
- Modify: `HOW_TO_ADD_NEW_CAPABILITY.md` at the presentational-only invariant
- Modify: `capability_homogeneity_audit.md` F4 and addendum wording

- [ ] **Step 1: Document the pipeline.**

Describe the order as recognition → validation → default normalization → capability formatting → candidate deduplication → status → replay hash. State that rules must not inspect `output_format` to decide validation or presentation.
Document that CI rejects any `output_format` reference in validation-rule modules, that localized Country names are formatted through current alpha-2 mappings while preserving CLDR/Unicode provenance, and that historical former codes pass through when no current mapping exists.

- [ ] **Step 2: Correct F4 historical wording.**

Remove the withdrawn claim that Date generally ignores `output_format`. Record that the remaining implementation work is centralization of formatting and removal of duplicated Phone/Country/Date rule-level presentation branches.

- [ ] **Step 3: Run documentation-facing static checks.**

Search for stale rule-level guidance:

```bash
rg "normalize.*output_format|rules.*output_format|format_value" ARCHITECTURE.md HOW_TO_ADD_NEW_CAPABILITY.md capability_homogeneity_audit.md
```

Expected: documentation consistently identifies `Capability.format_value()` as the presentation seam.

## Task 7: Final Verification And Review

**Files:** all files changed by Tasks 1-6.

- [ ] **Step 1: Run formatting and lint gates.**

```bash
uv run ruff format --check .
uv run ruff check .
```

Expected: both commands exit 0.

- [ ] **Step 2: Run strict type and import-boundary gates.**

```bash
uv run pyright
uv run lint-imports
```

Expected: no new type errors and all import-linter contracts pass.

- [ ] **Step 3: Run the full suite once more.**

```bash
uv run pytest -q
```

Expected: full suite passes with no deleted or weakened tests.

- [ ] **Step 4: Run the explicit homogeneity and compatibility gates.**

Run:

```bash
uv run pytest tests/unit/test_rule_output_format_purity.py tests/integration/test_default_replay_hashes.py -q
```

Expected: the rule-purity gate passes with no rule-level `output_format` references, and all five literal default replay hashes remain byte-identical to the pre-migration baseline.

- [ ] **Step 5: Review the diff against the behavioral contract.**

Confirm that no rule still branches on `contract.output_format`, no default canonical form changed, RFC 3966 extensions remain preserved, Country former-code passthrough remains intact, provenance is unchanged, and formatting occurs before deduplication/status/hash.

- [ ] **Step 6: Commit the completed implementation in atomic slices.**

Use separate commits for the engine seam, Date migration, Phone migration, Country migration, and documentation/tests. Stage only intended files and use concise messages such as:

```bash
git add paxman/core/capability.py paxman/engine/orchestrator.py tests/integration/test_format_value_seam.py
git commit -m "refactor: centralize capability output formatting"
```
