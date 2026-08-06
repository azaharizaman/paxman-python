# URL Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the eighth Paxman capability — `URL` — canonicalizing absolute URIs/IRIs embedded in prose to the WHATWG URL Standard's deterministic serialization, with full provenance. Design authority: `docs/research/2026-08-06-url-canonicalization.md` (decisions D1–D16, §9). Reasoning authority: the D-sections of that document. Shape authority: the cross-part contract in §1 below. Milestone that must hold end-to-end through `canonicalize()`: `HTTPS://Example.COM:443/path/../other` → `https://example.com/other`.

**Architecture:** One PARSER-strategy capability mirroring `IP` (regex span grammar + validating rule). A single shape-only grammar, `absolute_uri_recognition`, recognizes scheme-anchored URI/IRI spans in prose (RFC 3986 §3.1 anchor, RFC 3987 §2.2 body, RFC 3986 Appendix C boundaries); it never validates or maps tokens. A single rule, `WHATWG URL Standard` (`RuleStrategy.PARSER`), runs the WHATWG basic URL parser and serializer (§4.4/§4.5) through a dedicated `parsing.py` helper over the raw span text: fatal validation errors yield no resolution (recognized-but-unvalidated → `INVALID`), silent recoveries canonicalize (`SUCCESS`). IRI hosts are punycoded via vendored UTS #46 tables in `rules/data/idna_uts46_mapping.py` (generated — zero runtime dependencies, D13). `URLNotation(text)` is the single-field notation (D15); `URLCapabilityContract` has no feature flags (D14) and one output format `"url"` (identity formatter). Provenance cites WHATWG §4.4/§4.5 with RFC 3986 §3.1 / RFC 3987 §2 grammar references.

**Tech Stack:** uv (toolchain, no Makefile/tox/nox); Python 3.11+; ruff (line-length 88, target-version py311); pyright (strict); import-linter (layer boundaries); pytest (+ pytest-cov, Hypothesis); WHATWG URL Standard (normative pipeline — D2); RFC 3986 §3.1 / RFC 3987 §2 (grammar provenance); UTS #46 15.1.0 (vendored IDNA tables).

---

## 1. Cross-Part Contract

Everything below is shared across tasks. Implementers must treat this table as authoritative for shapes; the research doc D-sections are authoritative for reasoning. **Reuse these verbatim — do not re-decide them.**

| Contract item | Value |
|---|---|
| Capability name | `"url"` (lowercase; `GrammarRule`/`Rule` metadata enforce lowercase) |
| Package | `paxman/capabilities/URL/` |
| Notation | `URLNotation(text: str)` — `@dataclass(frozen=True, slots=True)`; `as_list() -> [self.text]` (D15) |
| Contract class | `URLCapabilityContract` — `@dataclass(frozen=True)` **without** `slots=True`; `capability_name = field(default="url", init=False)`; `DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "url"`; `OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset()`; `active_grammars = ("absolute_uri_recognition",)`; `_extra_dict_fields() -> {}` |
| Contract keys | exactly `{"capability_name", "excluded_rules", "pinned_rules", "year", "output_format"}` (no feature flags — D14) |
| Capability class | `URLCapability` — `name = "url"`, `version = "1.0.0"`; one grammar, one rule; static keyword-only `create_contract` (unanimous common block only); identity `format_value` |
| Grammar | `absolute_uri_recognition` (file `grammar/absolute_uri_recognition.py`) — regex, shape-only, span-bearing `RecognitionMatch` |
| Rule | `WHATWG URL Standard` — `strategy = RuleStrategy.PARSER`; `target_grammars = frozenset({"absolute_uri_recognition"})`; `requires_features = frozenset()`; `name = "WHATWG URL Standard"` |
| Provenance | `Provenance(authority="WHATWG", specification_name="URL Standard", kind="specification", reference_url="https://url.spec.whatwg.org/", version="Living Standard", lifecycle="active", publication_year=2026)` |
| Citation | `"Section 4.4 (basic URL parser); RFC 3986 §3.1 / RFC 3987 §2 grammar"` |
| Parse helper | `parse_and_serialize(raw: str) -> str | None` in `paxman/capabilities/URL/parsing.py` — identical contract exercised in Tasks 4, 5, 9, and 11 |
| IDNA data | `rules/data/idna_uts46_mapping.py` (generated) + `rules/data/idna_uts46_mapping.txt` (committed snapshot, UTS #46 15.1.0) + `tools/regenerate_idna_uts46_data.py` (ISBN `regenerate_isbn_range_data.py` pattern, D13) |
| Test markers | `[pytest.mark.capability, pytest.mark.url]` in capability-layer test modules; `url` marker registered in pyproject (`"url: url capability tests"`) |
| Milestone test | `HTTPS://Example.COM:443/path/../other` → `https://example.com/other` — must appear in Tasks 4, 5, 9, **and** 11 |
| e2e statuses | milestone → `SUCCESS`; `"hello world"` → `MISSING`; `"http://example.com:99999/"` and `"http://[::1"` → `INVALID`; `mailto:user@example.com` → `SUCCESS` verbatim |

**§4 evidence cases that MUST ship as rule-layer/parsing tests** (research doc §7.6): percent-encoding preserved byte-for-byte including invalid escapes (`%zz`, bare `%`) and case kept (`%2f` ≠ `%2F`); empty `?` and empty `#` preserved; port 0 preserved; `010.010.010.010` → `8.8.8.8` (IPv4 leading-zero octal → decimal); backslash → `/`; default-port elision; `file://localhost/...` → `file:///...`; opaque `mailto:` verbatim; IDNA `münchen.de` → `xn--mnchen-3ya.de`; `ß` per UTS #46 deviation; no NFC (`café` ≠ `cafe\u0301`).

**Layout note (plan-level correction to research doc §7.1):** the research doc's directory tree omits `parsing.py`. The plan adds it at the package root next to `notation.py`/`contract.py`/`capability.py` — the WHATWG state machine must live in its own module (pyright-strict, `import-linter` leaf) so the rule and tests share it (Tasks 4/5/9/11 all exercise the same `parse_and_serialize`).

---

## 2. Implementation Tasks

Twelve tasks, each RED → GREEN → verify+commit. Execute strictly in §3 order (only Tasks 2 and 3 may run in parallel). Commit messages are fixed; do not rewrite history.

### Task 1: `feat(url): add URLNotation and package skeleton`

**Files:**
- Create: `paxman/capabilities/URL/__init__.py`
- Create: `paxman/capabilities/URL/notation.py`
- Create: `paxman/capabilities/URL/contract.py` (stub — body implemented in Task 6)
- Create: `paxman/capabilities/URL/capability.py` (stub — body implemented in Task 7)
- Create: `paxman/capabilities/URL/grammar/__init__.py` (empty)
- Create: `paxman/capabilities/URL/rules/__init__.py` (empty)
- Create: `tests/capabilities/url/__init__.py` (empty)
- Create: `tests/capabilities/url/test_notation.py`

- [ ] **Step 1: RED** — `tests/capabilities/url/test_notation.py` mirroring `tests/capabilities/money/test_notation.py` (`pytestmark = [pytest.mark.capability, pytest.mark.url]`):
  - `test_fields`: `URLNotation(text="https://example.com").text == "https://example.com"`.
  - `test_as_list`: `URLNotation(text="mailto:user@example.com").as_list() == ["mailto:user@example.com"]`.
  - `test_frozen`: assigning `.text` raises `FrozenInstanceError` (frozen dataclass).
  - `test_slots`: `not hasattr(URLNotation(text="x"), "__dict__")` (slots enforced — Traps §4.3).
  - `test_empty_text_valid`: shape-only notation — `URLNotation(text="").as_list() == [""]` (validity is the rule's job, D7).
- [ ] **Step 2: GREEN** —
  - `notation.py`: `URLNotation` per §1 (single `text: str` field, `as_list()`); docstring cites D15 and the "shape-only, never validates" convention.
  - `contract.py` stub: `class URLCapabilityContract(CapabilityContract):` body marked `# Task 6` (importable, not instantiable — abstract `active_grammars` unimplemented).
  - `capability.py` stub: `class URLCapability(Capability[URLNotation]):` body marked `# Task 7` (importable; abstract members unimplemented).
  - `__init__.py` mirrors the Money package export triple: `__all__ = ["URLCapability", "URLCapabilityContract", "URLNotation"]`.
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/capabilities/url -v` → pass (test_notation only). Commit `feat(url): add URLNotation and package skeleton`.

### Task 2: `feat(url): add absolute_uri_recognition grammar`

**Files:**
- Create: `paxman/capabilities/URL/grammar/absolute_uri_recognition.py`
- Create: `tests/capabilities/url/test_grammar.py`

- [ ] **Step 1: RED** — `tests/capabilities/url/test_grammar.py` (`pytestmark = [pytest.mark.capability, pytest.mark.url]`), cases from research doc §7.6 "Unit — grammar" and §6.1:
  - `test_note_colon_rejected`: `"Note:"` → no matches (D16 — no body character after the colon).
  - `test_span_in_prose_with_parens`: `"(https://example.com)"` → one match; `raw_text == "https://example.com"` (leading `(` outside the span via the scheme anchor; trailing `)` excluded as unbalanced within the span — Appendix C).
  - `test_multiline_span_keeps_tab_newline`: `"http://exa\nmple.com/"` → one match; `raw_text` contains the newline (recognition keeps it; the rule strips it pre-parse, WHATWG §4.4 step 1 — D8).
  - `test_trailing_dot_host_included`: `"http://example.com."` → `raw_text == "http://example.com."` (trailing `.` is legal in host/path; §6.2.3 treats trailing-dot hosts as distinct — D4).
  - `test_left_boundary_word_rejection`: `"ahttps://example.com"` → no matches (not preceded by a scheme-legal character); `"(https://example.com"` → one match.
  - `test_non_ascii_body`: `"mailto:user@münchen.de"` → one match covering the full IRI (ucschar body, RFC 3987 §2.2).
  - `test_shape_only_never_validates`: `"https://"` (no host) and `"http://99999/"` → recognized as spans (the rule decides validity per WHATWG — D8; grammar must not reject on shape).
  - `test_span_invariant`: for the prose set `["(https://example.com)", "see http://example.com. now", "mailto:user@münchen.de"]`, every match satisfies `0 <= start <= end <= len(text)` and `len(raw_text) == end - start` (RecognitionMatch invariant).
- [ ] **Step 2: GREEN** — `grammar/absolute_uri_recognition.py` implementing §6.1 exactly:
  - `name = "absolute_uri_recognition"`; `class AbsoluteUriRecognition(Grammar[URLNotation])` with `recognize(text) -> list[RecognitionMatch[URLNotation]]`.
  - Pattern structure (fine detail per research doc §6.1 — this is the shape, not a license to deviate):
    ```python
    # Scheme anchor (RFC 3986 §3.1 / RFC 3987 §2.1): ALPHA *( ALPHA / DIGIT / "+" / "-" / "." ) ":"
    # Left boundary: not preceded by a scheme-legal character (word rejection).
    # Body: URI/IRI code points (RFC 3986 §2 + RFC 3987 §2.2 ucschar) plus tab/newline
    #       (Appendix C multi-line URIs); at least ONE body character after the colon (D16).
    # Right boundary: whitespace, control characters (except tab/newline), "<", ">", '"'
    #       (Appendix C delimiters). Trailing "." kept.
    _ABSOLUTE_URI_PATTERN = re.compile(
        r"(?<![A-Za-z0-9+.\-])"
        r"[A-Za-z][A-Za-z0-9+.\-]*:"
        r"[^ <>\x00-\x08\x0B\x0C\x0E-\x1F\x7F]*[^ <>\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
    )
    ```
  - Post-process: strip an unbalanced trailing `)` (repeatedly, while the span has more `)` than `(`); adjust `end` so `len(raw_text) == end - start` still holds.
  - Emits `RecognitionMatch(notation=URLNotation(raw_span), start=..., end=..., raw_text=raw_span)` for each match.
  - **Purity (Traps §4.5):** no scheme table, no validation, no imports from `rules/` or `parsing.py`; the grammar↔rules purity scan (`tests/unit/test_grammar_semantic_purity.py`) checks this automatically.
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/capabilities/url -v` → pass. Commit `feat(url): add absolute_uri_recognition grammar`.

### Task 3: `feat(url): add vendored UTS #46 IDNA tables and generator`

**Files:**
- Create: `tools/regenerate_idna_uts46_data.py`
- Create: `paxman/capabilities/URL/rules/data/idna_uts46_mapping.txt` (committed source snapshot)
- Create: `paxman/capabilities/URL/rules/data/idna_uts46_mapping.py` (**generated** — never hand-edited)
- Create: `tests/capabilities/url/test_data.py`
- Create: `tests/capabilities/url/test_data_consistency.py`

- [ ] **Step 1: RED** — `tests/capabilities/url/test_data.py` (mirror `tests/capabilities/isbn/test_data.py`; `pytestmark = [pytest.mark.capability, pytest.mark.url]`):
  - `test_version_constant`: `IDNA_VERSION == "15.1.0"` (pinned UTS #46 version).
  - `test_key_rows`: spot-check the vendored tables — `IDNA_STATUS["0041"] == "valid"` (A), `IDNA_STATUS["00DF"] == "deviation"` (ß per UTS #46), `IDNA_STATUS["0000"] == "disallowed"`, `IDNA_MAPPED["00FC"]` maps ü (U+00FC) to its ASCII target sequence (so `münchen` punycodes to `xn--mnchen-3ya`).
  - `test_module_docstring_records_regeneration`: the generated module's docstring contains the `uv run python tools/regenerate_idna_uts46_data.py` command (auditable regeneration, D13).
  - `test_no_output_format_token`: `"output_format" not in module_text` (purity re-check on the generated module — Traps §4.1).
  - `test_data_consistency.py` (mirror `tests/capabilities/money/test_data_consistency.py`; `pytestmark = [pytest.mark.capability, pytest.mark.url]`):
  - `test_every_mapping_target_is_a_known_codepoint`: every hex target in every `IDNA_MAPPED` value also appears as a key in `IDNA_STATUS` (mapping closure — no dangling targets).
  - `test_statuses_are_valid_uts46`: every `IDNA_STATUS` key is 4–6 hex digits (or a `start..end` range) and every value is in `{"valid", "mapped", "deviation", "ignored", "disallowed", "disallowed_STD3_valid", "disallowed_STD3_mapped"}`.
  - `test_snapshot_matches_module`: the committed `idna_uts46_mapping.txt` header records `UTS #46 15.1.0` and agrees with `IDNA_VERSION`.
  - `test_regeneration_is_idempotent`: `regenerate_idna_uts46_data.render()` (the tool's pure emit function) returns text byte-identical to the committed `idna_uts46_mapping.py` (research doc §7.6 "generator regeneration is idempotent").
- [ ] **Step 2: GREEN** —
  - `tools/regenerate_idna_uts46_data.py` mirrors `tools/regenerate_isbn_range_data.py` exactly: stdlib only; `_REPO_ROOT` from `__file__`; `SNAPSHOT`/`OUTPUT`/`LINE_LENGTH = 88` constants; a pure `render() -> str` building the module text; `main()` writes it; header docstring `"""... — GENERATED, do not edit by hand.\n\nSource: https://www.unicode.org/Public/idna/15.1.0/IdnaMappingTable.txt\n...\nRegenerate with: uv run python tools/regenerate_idna_uts46_data.py\n"""`; and the ISBN purity guard verbatim pattern: `if "output_format" in doc: raise RuntimeError("generated module must not contain 'output_format'")` (Traps §4.1).
  - `idna_uts46_mapping.txt`: committed snapshot of UTS #46 15.1.0 `IdnaMappingTable.txt` (header lines preserve the source URL/version).
  - `idna_uts46_mapping.py`: generated — module docstring + `from __future__ import annotations` + `IDNA_VERSION = "15.1.0"` + typed tables:
    ```python
    IDNA_STATUS: dict[str, str] = {"0041": "valid", "00DF": "deviation", ...}
    IDNA_MAPPED: dict[str, str] = {"00FC": "0075 0308", ...}  # only mapped/deviation rows
    ```
  - Emit each table as ruff-format-compliant literals (single-line when ≤ 88 columns, else one entry per line with a magic trailing comma — ISBN `_emit_rule_table` pattern).
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/capabilities/url -v` → pass; `uv run python tools/regenerate_idna_uts46_data.py` → prints `wrote ...` with no diff (`git status` clean for the generated module). Commit `feat(url): add vendored UTS #46 IDNA tables and generator`.

### Task 4: `feat(url): add WHATWG URL parsing helper`

**Files:**
- Create: `paxman/capabilities/URL/parsing.py`
- Create: `tests/capabilities/url/test_parsing.py`

- [ ] **Step 1: RED** — `tests/capabilities/url/test_parsing.py` (`pytestmark = [pytest.mark.capability, pytest.mark.url]`), every row of research doc §4 as a parametrized case. Case tables (module-level constants):
  - `_FATAL_CASES` (×5, §4.1): `http://example.com:99999/` (port > 65535), `http://example.com:80x/` (non-digit port), `http://example.com:80:90/` (two port components), `http://exa mple.com/` (space in host), `http://[::1` (unclosed IPv6) → `parse_and_serialize` returns `None` for each.
  - `_RECOVERY_CASES` (×9, §4.2): `http://exa\nmple.com/` → `http://example.com/`; `http://example.com:` → `http://example.com/`; `http://example.com:0/` → `http://example.com:0/` (port 0 preserved); `http://example.com\path` → `http://example.com/path`; `http://%65xample.com/` → `http://example.com/` (host percent-decoding); `http://example.com/a b` → `http://example.com/a%20b`; `http://user name@example.com/` → `http://user%20name@example.com/`; `http://[2001:db8::1]/` → `http://[2001:db8::1]/`; `file://localhost/etc/hosts` → `file:///etc/hosts`.
  - `_PERCENT_CASES` (×5, §4.3): `http://example.com/a%2fb` → verbatim (case kept, `%2f` ≠ `%2F`); `http://example.com/%41` → verbatim (not decoded to `A`); `http://example.com/~x` → verbatim; `http://example.com/%zz` → verbatim (invalid escape preserved); `http://example.com/a%` → verbatim (bare `%` preserved).
  - `_QUERY_FRAGMENT_CASES` (×6, §4.4): `http://example.com/?a=b c` → `.../?a=b%20c`; `http://example.com/?x=%7e` → verbatim; `http://example.com/?a+b` → verbatim (`+` literal); `http://example.com/?` → verbatim (empty query preserved); `http://example.com/#` → verbatim (empty fragment preserved); `http://example.com/#a b` → `...#a%20b`.
  - `_NON_SPECIAL_CASES` (×9, §4.5): `mailto:user@example.com` → verbatim; `GIT://github.com/user/repo` → `git://github.com/user/repo`; `ssh://user@host:22/path` → verbatim (port kept, non-special); `ftp://example.com:21/a` → `ftp://example.com/a` (default port dropped); `ws://example.com:80/a` → `ws://example.com/a`; `mailto:user@münchen.de` → `mailto:user@m%C3%BCnchen.de`; `data:text/plain,hello world` → verbatim (opaque path: space raw); `git://github.com/user/my repo` → `git://github.com/user/my%20repo`; `custom:scheme with space` → verbatim (opaque).
  - `_HOST_CASES` (×7, §4.6): milestone `HTTPS://Example.COM:443/path/../other` → `https://example.com/other`; `http://010.010.010.010/` → `http://8.8.8.8/`; `http://192.168.001.001/` → `http://192.168.1.1/`; `http:///path` → `http://path/`; `http://münchen.de/` → `http://xn--mnchen-3ya.de/`; `http://caf%C3%A9.de/` → `http://xn--caf-dma.de/`; `http://café.example/` → `http://xn--caf-dma.example/`.
  - `_NFC_CASES` (×2, §4.7): `http://example.com/café` → `http://example.com/caf%C3%A9`; `http://example.com/cafe\u0301` → `http://example.com/cafe%CC%81` — **distinct** outputs (no NFC, D9).
  - One parametrized test per table (`test_fatal_cases_return_none`, `test_recovery_cases_canonicalize`, `test_percent_encoding_preserved`, `test_query_fragment_verbatim`, `test_non_special_schemes_pass_through`, `test_hosts_and_ipv4`, `test_no_unicode_normalization`) plus:
  - `test_milestone`: explicit milestone assertion (also covered in `_HOST_CASES`).
  - `test_idempotent`: for every non-`None` output `x` from the case tables, `parse_and_serialize(x) == x` (WHATWG serialization is a fixed point).
  - `test_never_raises`: `parse_and_serialize` never raises for any case input (returns `None` on fatal instead).
- [ ] **Step 2: GREEN** — `paxman/capabilities/URL/parsing.py` implementing the WHATWG basic URL parser and serializer (research doc §2.3, §7.3):
  - Public: `parse_and_serialize(raw: str) -> str | None` — returns the §4.5-serialized URL string, or `None` on a fatal validation error. Never raises.
  - Step 1 of §4.4: strip ASCII tab/newline (`\t`, `\n`, `\r`) from the input — this is what turns an Appendix C multi-line span into a canonical URL (D8 recovery path).
  - Constants: `_SPECIAL_SCHEMES: dict[str, int | None] = {"ftp": 21, "file": None, "http": 80, "https": 443, "ws": 80, "wss": 443}`; `_AUTHORITY_INVALID_CHARS`, `_HOST_PATTERN`, `_DEFAULT_PORTS` (default-port elision uses `_SPECIAL_SCHEMES` — `None` default never elides).
  - State machine per WHATWG §4.4: scheme → special/non-special split → userinfo → host → port → path → query → fragment. Host handling: percent-decode then IPv4 (leading-zero parts octal → decimal, §4.6), IPv6 literal validation, and IDNA for non-ASCII hosts via the vendored tables + stdlib punycode (RFC 3492) — import `from paxman.capabilities.URL.rules.data.idna_uts46_mapping import IDNA_MAPPED, IDNA_STATUS` (this is why Task 3 precedes Task 4 — §3 sequencing).
  - Serialize per §4.5: lowercase scheme/host, drop port equal to the scheme default, preserve existing `%HH` byte-for-byte (never normalize case, never decode unreserved — §4.3 divergence), space → `%20` in path/query/fragment, opaque paths verbatim except space-before-`?`/`#`.
  - Fatal validation errors → `None`; recoverable validation errors (WHATWG §4.4 flagged recoveries) → continue and canonicalize (D8).
  - **import-linter leaf (Traps §4.7):** `parsing.py` imports nothing from `paxman.core` and no sibling capability packages — its only intra-package import is the IDNA data module. pyright-strict, no `Any`-loosening (Traps §4.11).
  - **IDNA deviation note (documented in the module docstring):** stdlib RFC 3492 punycode differs from Node's WHATWG IDNA on some denormalized inputs; verification scope is valid IDNs only (research doc empirical-verification note).
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/capabilities/url -v` → pass. Commit `feat(url): add WHATWG URL parsing helper`.

### Task 5: `feat(url): add WHATWG URL Standard rule`

**Files:**
- Create: `paxman/capabilities/URL/rules/whatwg_url_standard.py`
- Create: `tests/capabilities/url/test_rule.py`

- [ ] **Step 1: RED** — `tests/capabilities/url/test_rule.py` (`pytestmark = [pytest.mark.capability, pytest.mark.url]`):
  - `test_rule_metadata` (homogeneity contract, mirrors Money `test_rule_metadata`):
    - `rule.name == "WHATWG URL Standard"`; `rule.strategy == RuleStrategy.PARSER`; `rule.target_grammars == frozenset({"absolute_uri_recognition"})`; `rule.requires_features == frozenset()`.
    - `rule.provenance.authority == "WHATWG"`; `.specification_name == "URL Standard"`; `.kind == "specification"`; `.reference_url == "https://url.spec.whatwg.org/"`; `.version == "Living Standard"`; `.lifecycle == "active"`; `.publication_year == 2026`.
    - `rule.citation == "Section 4.4 (basic URL parser); RFC 3986 §3.1 / RFC 3987 §2 grammar"` (matches §1 — provenance is part of the public surface).
  - `test_returns_resolution_list`: `validate(candidate, output_format="url")` returns a `list[Resolution]`.
  - `test_success_case`: `URLNotation("HTTPS://Example.COM:443/path/../other")` → one `Resolution` with `value == "https://example.com/other"` and `status == ResolutionStatus.SUCCESS`.
  - `test_success_provenance`: the resolution's `provenance` is the rule's provenance (§1).
  - `test_fatal_validation_no_resolution`: `URLNotation("http://example.com:99999/")` → `[]` (rule returns empty list → pipeline reports `INVALID`).
  - `test_silent_recovery_succeeds`: `URLNotation("http://exa\nmple.com/")` → `Resolution(value="http://example.com/", status=SUCCESS)` (D8).
  - `test_milestone_via_rule`: milestone case asserts `value == "https://example.com/other"`.
  - `test_never_raises`: no input in the §4 case corpus makes `validate` raise.
  - **§4 evidence as rule tests** (research doc §7.6 "parsing → rule"): at minimum `%zz`/bare `%` byte-preservation, empty `?`/`#`, port 0, `010.010.010.010` → `8.8.8.8`, backslash → `/`, default-port elision, `file://localhost` → `file:///`, opaque `mailto:` verbatim, `münchen.de` → `xn--mnchen-3ya.de`, ß deviation, and the two distinct no-NFC outputs — each through `validate()` (not just `parse_and_serialize`), asserting `Resolution.value`.
- [ ] **Step 2: GREEN** — `rules/whatwg_url_standard.py` mirroring `Money/rules/iso_4217_ed2015.py` and the IP parser rule:
  - `class WhatwgUrlStandard(Rule[URLNotation, Resolution])` — `name = "WHATWG URL Standard"`, `strategy = RuleStrategy.PARSER`, `target_grammars`/`requires_features` per §1, `citation` per §1, `provenance` per §1.
  - `validate(candidate, output_format="url") -> list[Resolution]` — PARSER strategy: skip regex matching entirely (the orchestrator calls the rule directly on the notation); call `parse_and_serialize(candidate.text)`; `None` → `[]`; canonical string → `[Resolution(value=canonical, status=ResolutionStatus.SUCCESS)]`.
  - Rule = one WHATWG §4.4/§4.5 publication; the state machine stays in `parsing.py` (single source shared with Task 4 tests — Traps §4.7).
  - **Purity (Traps §4.1):** no `output_format` token anywhere in the file (source-scanned by `tests/unit/test_rule_output_format_purity.py`); no reading `candidate.output_format`; no feature-gating.
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/capabilities/url -v` → pass; `uv run ruff check paxman/capabilities/URL/` → clean. Commit `feat(url): add WHATWG URL Standard rule`.

### Task 6: `feat(url): add URLCapabilityContract`

**Files:**
- Modify: `paxman/capabilities/URL/contract.py` (replace Task 1 stub)
- Create: `tests/capabilities/url/test_contract.py`

- [ ] **Step 1: RED** — `tests/capabilities/url/test_contract.py` (`pytestmark = [pytest.mark.capability, pytest.mark.url]`):
  - `test_defaults`: `URLCapabilityContract()` → `capability_name == "url"`, `excluded_rules == ()`, `pinned_rules == ()`, `year is None`, `output_format == "url"`, `active_grammars == ("absolute_uri_recognition",)`.
  - `test_output_format_validated`: `URLCapabilityContract(output_format="compact")` raises `ValueError` (not in `OFFERED_OUTPUT_FORMATS` ∪ {`DEFAULT_OUTPUT_FORMAT`}); `URLCapabilityContract(output_format="url")` is fine.
  - `test_extra_dict_fields_empty`: `URLCapabilityContract()._extra_dict_fields() == {}` (D14 — no feature flags, so no extra contract keys).
  - `test_contract_keys`: `asdict()` (recursively, flattening `CapabilityContract` base fields) has exactly `{"capability_name", "excluded_rules", "pinned_rules", "year", "output_format"}` — guard that no feature-key leaks into the replay-hash surface (Traps §4.9).
  - `test_frozen`: frozen dataclass — attribute assignment raises `FrozenInstanceError`.
  - `test_no_slots`: `hasattr(URLCapabilityContract(), "__dict__")` (contracts are `@dataclass(frozen=True)` **without** slots — project convention, enforced by the surface guard).
- [ ] **Step 2: GREEN** — `contract.py` implementing §1:
  ```python
  @dataclass(frozen=True)
  class URLCapabilityContract(CapabilityContract):
      """No feature flags (D14). Output format is always the WHATWG serialization."""

      capability_name: str = field(default="url", init=False)
      DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "url"
      OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset()
      active_grammars: tuple[str, ...] = ("absolute_uri_recognition",)

      def _extra_dict_fields(self) -> dict[str, object]:
          return {}
  ```
  - `@dataclass(frozen=True)` **without** `slots=True` (project convention; `CapabilityContract` base is `@dataclass(frozen=True)`, `output_format` resolved in `__post_init__`).
  - Docstring cites D14 and the §1 contract table.
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/capabilities/url -v` → pass. Commit `feat(url): add URLCapabilityContract`.

### Task 7: `feat(url): wire URLCapability with create_contract and format_value`

**Files:**
- Modify: `paxman/capabilities/URL/capability.py` (replace Task 1 stub)
- Modify: `paxman/capabilities/URL/__init__.py` (add `URLCapabilityContract` to exports if not already)
- Create: `tests/capabilities/url/test_capability.py`

- [ ] **Step 1: RED** — `tests/capabilities/url/test_capability.py` (`pytestmark = [pytest.mark.capability, pytest.mark.url]`):
  - `test_metadata`: `URLCapability.name == "url"`, `URLCapability.version == "1.0.0"`.
  - `test_get_grammars`: `URLCapability().get_grammars()` → exactly `{AbsoluteUriRecognition}` (one grammar).
  - `test_get_rules`: `URLCapability().get_rules()` → exactly `{WhatwgUrlStandard}` (one rule).
  - `test_create_contract_keyword_only`: calling `create_contract("url", (), (), None, "url")` positionally raises `TypeError` (static keyword-only signature — mirror Money/IP).
  - `test_create_contract_defaults`: `URLCapability().create_contract(excluded_rules=(), pinned_rules=(), year=None, output_format="url")` → contract with `capability_name == "url"`, `active_grammars == ("absolute_uri_recognition",)`.
  - `test_create_contract_excludes_rule`: `create_contract(excluded_rules=("WHATWG URL Standard",), ...)` → `pinned_rules`/`excluded_rules` propagated; the rule list in the returned contract reflects the exclusion (unanimous common block only — no feature flags, D14).
  - `test_format_value`: `format_value("https://example.com/a b", output_format="url") == "https://example.com/a b"` (identity — the WHATWG serialization IS the value; D14).
  - `test_format_value_rejects_unknown_format`: `format_value(..., output_format="compact")` raises `ValueError` (format not offered).
- [ ] **Step 2: GREEN** — `capability.py` mirroring `Phone/capability.py`/`Money/capability.py`:
  - `class URLCapability(Capability[URLNotation])` — `name = "url"`, `version = "1.0.0"`; `get_grammars() -> {AbsoluteUriRecognition}`; `get_rules() -> {WhatwgUrlStandard}`.
  - `create_contract` is `@staticmethod`, keyword-only `(excluded_rules=(), pinned_rules=(), year=None, output_format=URLCapabilityContract.DEFAULT_OUTPUT_FORMAT) -> URLCapabilityContract` — the unanimous common block only (the `CapabilityContract.__post_init__` resolves/validates `output_format`).
  - `format_value(value: str, output_format: str = "url") -> str` — identity formatter (return `value` after validating the format against the contract's offered formats).
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/capabilities/url -v` → pass; `uv run ruff check paxman/capabilities/URL/` → clean. Commit `feat(url): wire URLCapability with create_contract and format_value`.

### Task 8: `feat(url): register URL capability and extend export/surface guards`

**Files:**
- Modify: `paxman/capabilities/__init__.py` (register URL)
- Modify: `tests/unit/test_capability_exports.py` (extend to 8)
- Modify: `tests/unit/test_capability_surface.py` (extend to 8)
- Modify: `pyproject.toml` (add `url` marker)
- Modify: `tests/unit/test_grammar_semantic_purity.py` (add URL grammar to the scan)
- Modify: `README.md` (capability list + count 7 → 8)
- Modify: `AGENTS.md` (root, `paxman/capabilities/`, `tests/` — capability list + count)

- [ ] **Step 1: RED** — extend the existing guards first (each fails before the registration lands):
  - `tests/unit/test_capability_exports.py`: add a `TestURLExports` class mirroring the seven existing classes — `URL.name == "url"`; `URLCapability`, `URLCapabilityContract`, `URLNotation` importable from `paxman.capabilities`; export list contains exactly 8 names (7 + `URL`).
  - `tests/unit/test_capability_surface.py`: add `URLCapability`/`URLCapabilityContract`/`URLNotation` to `_CAPABILITY_SURFACES` (8 rows) — homogeneity assertions: `name == "url"`; `create_contract` keyword-only static; contract `@dataclass(frozen=True)` without slots; notation frozen+slots; `format_value` present.
  - `tests/unit/test_grammar_semantic_purity.py`: add `absolute_uri_recognition` to the scanned grammar glob — the purity scan now covers URL (Traps §4.5).
  - `README.md`: update the capability list (7 → 8 entries) and any "seven capabilities" wording (also in `docs/` where the count is stated — check and update).
- [ ] **Step 2: GREEN** — `paxman/capabilities/__init__.py`:
  - Add `from paxman.capabilities.URL import URLNotation, URLCapability, URLCapabilityContract` (alphabetical order: after ISBN, before Money — package `URL` sorts before `Money`? **No:** sort by package name — current order is Country, Date, Email, IP, ISBN, Money, Phone; `URL` is case-insensitive `url` → insert after Phone as the eighth entry).
  - Add `URL` to `__all__` (8 names).
  - `pyproject.toml`: append `"url = { marker = \"url\", description = \"url capability tests\" }"` after the `money` marker entry (keeps the marker block alphabetical).
- [ ] **Step 3: Verify + commit** — `uv run ruff check paxman/ tests/` → clean; `uv run pytest tests/unit -v` → pass (guards green with registration); `uv run import-linter lint` → clean (layer boundaries hold). Commit `feat(url): register URL capability and extend export/surface guards`.

### Task 9: `test(url): lock URL pipeline semantics`

**Files:**
- Create: `tests/integration/test_url_pipeline.py`
- Create: `tests/unit/test_url_contract_homogeneity.py` (if the surface guard in Task 8 does not cover the contract-key assertion)

- [ ] **Step 1: RED** — `tests/integration/test_url_pipeline.py` mirroring `tests/integration/test_money_pipeline.py` (autouse `_fresh_registry` fixture that clears and re-registers the URL capability; class-level docstring locks the semantics):
  - `test_milestone_full_pipeline`: `canonicalize("HTTPS://Example.COM:443/path/../other")` →
    - `result.capability == "url"`,
    - `result.status == ResultStatus.SUCCESS`,
    - `result.value == "https://example.com/other"` (the §1 milestone end-to-end),
    - `result.match.notation.text == "HTTPS://Example.COM:443/path/../other"` (span preserved),
    - `result.rule == "WHATWG URL Standard"`,
    - `result.provenance.authority == "WHATWG"`,
    - `result.output_format == "url"`.
  - `test_missing`: `canonicalize("no url here")` → `ResultStatus.MISSING`.
  - `test_invalid_fatal`: `canonicalize("http://example.com:99999/")` → `ResultStatus.INVALID`.
  - `test_invalid_unterminated_ipv6`: `canonicalize("http://[::1")` → `ResultStatus.INVALID`.
  - `test_silent_recovery_success`: `canonicalize("http://exa\nmple.com/")` → `SUCCESS`, `value == "http://example.com/"` (D8 — recognition kept the newline span, the rule recovered).
  - `test_verbatim_opaque`: `canonicalize("mailto:user@example.com")` → `SUCCESS`, `value == "mailto:user@example.com"` (opaque scheme preserved, §4.5).
  - `test_determinism`: same input + same contract → byte-identical result across repeated calls (provenance-first determinism; identical to `test_money_pipeline`'s determinism assertion).
  - **§4 evidence through the pipeline** (research doc §7.6 "unit → integration → e2e"): the `%zz`/bare `%` cases, empty `?`/`#`, port 0, `010.010.010.010` → `8.8.8.8`, backslash → `/`, `file://localhost` → `file:///`, `münchen.de` → `xn--mnchen-3ya.de`, and the no-NFC pair — each via `canonicalize()`, asserting `status == SUCCESS` and `value`.
- [ ] **Step 2: GREEN** — the pipeline needs no new source: Tasks 4–8 already wired the capability. This task exists to prove the full `canonicalize()` path (registry → run_capability → grammar → rule → Resolution → hash) for URL — and to catch integration regressions early (Traps §4.9: the moment URL joins the registry, every replay-hash test must still pass).
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/integration -v` → pass. Commit `test(url): lock URL pipeline semantics`.

### Task 10: `test(url): baseline replay hash for the URL capability`

**Files:**
- Modify: `tests/integration/test_default_replay_hashes.py` (add URL baseline literal)

- [ ] **Step 1: RED** — extend `tests/integration/test_default_replay_hashes.py` mirroring the seven existing cases exactly (per-case `register_capability(URLCapability())` + `canonicalize(input, year=2026)`), adding:
  - `test_url_capability_replay_hash`: `canonicalize("HTTPS://Example.COM:443/path/../other", year=2026)` → `result.replay_hash == "<URL_BASELINE_HASH>"`.
  - `BASELINE_HASHES` dict gains a `"url"` key mapping the milestone input to the hash literal.
- [ ] **Step 2: GREEN** —
  1. Run the new test **once** to observe the actual hash value (a canonicalization library's replay hash is a SHA-256 digest over the deterministic pipeline record; the literal cannot be predicted ahead of time).
  2. Fill in the `<URL_BASELINE_HASH>` placeholder with the observed literal. The milestone input + `year=2026` + the URL capability's provenance record must hash deterministically to this literal — **byte-identical across platforms and runs** (provenance-first determinism).
  3. **Hard rule (project anti-pattern):** never hand-edit a baseline literal to make a test green — the hash is a *witness* of pipeline behavior. If the observed hash changes between runs, that is a regression to fix, not a literal to update.
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/integration/test_default_replay_hashes.py -v` → pass (all 8 cases). Commit `test(url): baseline replay hash for the URL capability`.

### Task 11: `test(url): add property invariants and e2e coverage`

**Files:**
- Create: `tests/property/test_url_properties.py`
- Modify: `tests/e2e/test_canonicalize.py` (add URL e2e cases)
- Modify: `tests/unit/test_capability_exports.py` **only if** the Task 8 export-guard class missed a URL symbol (unlikely — verify, don't assume)

- [ ] **Step 1: RED** — `tests/property/test_url_properties.py` mirroring `tests/property/test_money_properties.py` (autouse fixture registering the URL capability; `@pytest.mark.property` + `@given`):
  - `test_parsing_is_total_and_canonical`: `@given(st.text())` — `parse_and_serialize(raw)` never raises; when it returns a value, `parse_and_serialize(value) == value` (idempotence/fixed point).
  - `test_serialized_output_matches_shape`: `@given(st.text())` — every non-`None` output matches `_CANONICAL_SHAPE` (scheme `:` rest, no leading/trailing whitespace, scheme lowercase):
    ```python
    _CANONICAL_SHAPE = re.compile(r"^[a-z][a-z0-9+.\-]*:.+$")
    ```
  - `test_span_invariant`: `@given(st.text())` — every `RecognitionMatch` from `AbsoluteUriRecognition.recognize(raw)` satisfies `0 <= start <= end <= len(raw)` and `len(raw_text) == end - start` (span honesty).
  - `test_recognize_subset_of_parseable`: `@given(st.text())` — every recognized span's text is accepted by `parse_and_serialize` **or** is a recognized-but-unvalidated span (grammar is a superset of the rule's domain: `recognize` never rejects what the rule could accept; the rule decides validity — D7/D8).
- [ ] **Step 2: GREEN** — extend `tests/e2e/test_canonicalize.py` (autouse `_clean_registry` fixture; `from paxman.api import canonicalize`), adding the URL e2e rows from the §1 e2e contract:
  - `test_url_capability_milestone`: `canonicalize("HTTPS://Example.COM:443/path/../other")` → `ResultStatus.SUCCESS`, `value == "https://example.com/other"` (milestone must appear in Task 11 as the final end-to-end witness — §1).
  - `test_url_missing`: `canonicalize("no url here")` → `ResultStatus.MISSING`.
  - `test_url_invalid_port`: `canonicalize("http://example.com:99999/")` → `ResultStatus.INVALID`.
  - `test_url_opaque_scheme_verbatim`: `canonicalize("mailto:user@example.com")` → `SUCCESS`, `value == "mailto:user@example.com"`.
  - Follow the existing e2e file's parametrization style (a `URL_CASES` table + one parametrized test, matching the other capabilities' rows).
- [ ] **Step 3: Verify + commit** — `uv run pytest tests/property tests/e2e -v` → pass. Commit `test(url): add property invariants and e2e coverage`.

### Task 12: `docs(url): document URL capability and update capability counts`

**Files:**
- Modify: `README.md` (capability table + count 7 → 8)
- Modify: `AGENTS.md` (root, `paxman/capabilities/`, `tests/`)
- Modify: `docs/report/` and `docs/adr/` if any capability-count table or list references "seven capabilities" (verify with a repo-wide grep for `seven`/`7 capabilities` — update only where the count is stated)

- [ ] **Step 1: RED (docs-as-spec)** — grep the repo for stale references: `rg -n "seven|7 capabilities|7 capabilities" README.md AGENTS.md docs/` → list every hit to update (no code test needed — the Task 8 surface guards already enforce the 8-capability surface; this task is the documentation mirror).
- [ ] **Step 2: GREEN** —
  - `README.md`: add the URL row to the capability table (name, WHATWG URL Standard provenance, example input/output from §1); update "seven capabilities" → "eight capabilities" and the count in any summary line.
  - Root `AGENTS.md`: update the capability count (7 → 8) and the package tree (`paxman/capabilities/URL/`); add `URL` to any capability enumeration.
  - `paxman/capabilities/AGENTS.md`: add the URL package to the capability layout documentation.
  - `tests/AGENTS.md`: if it enumerates capability test directories, add `tests/capabilities/url/`.
  - `docs/`: update only verified stale count/list references.
- [ ] **Step 3: Final pre-PR gate (authoritative, `.github/workflows/ci.yml`)** — run the full merge-blocking suite and confirm green:
  ```bash
  uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run import-linter lint && uv run pytest
  uv run coverage report --include="paxman/{core,capabilities,engine,api}/*" --fail-under=95
  ```
  - Coverage must stay ≥ 95% global and per-package with the new `parsing.py` and generated `rules/data/idna_uts46_mapping.py` counted — if the WHATWG state machine's branches dip the package below 95%, **add the missing case tests** (do not weaken the floor; research doc §7.6 anticipates this).
  - Commit `docs(url): document URL capability and update capability counts`.

---

## 3. Sequencing and Parallelism

- **Strict linear chain:** Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12.
- **Only parallel pair:** Tasks 2 and 3 are independent (grammar vs. IDNA data) — may run in parallel if dispatched as separate workers; every other task depends on its predecessor (test-first, so the RED of N+1 needs the GREEN of N's source).
- **Hard dependencies:**
  - Task 4 (`parsing.py`) imports `paxman.capabilities.URL.rules.data.idna_uts46_mapping` → **Task 3 must land first** (IDNA data before the parser).
  - Task 5's rule imports `parse_and_serialize` from Task 4's `parsing.py` → Task 4 before Task 5.
  - Task 7's capability imports the Task 6 contract → Task 6 before Task 7.
  - Tasks 9/10/11 all exercise `canonicalize()` end-to-end → Task 8 (registry registration) must be green first.
  - Task 10's replay-hash literal depends on the Task 7 `create_contract` + Task 8 registration producing the final pipeline record — do not baseline the hash before Task 8 lands.
- **Milestone checkpoint:** after Task 9, `canonicalize("HTTPS://Example.COM:443/path/../other")` must equal `"https://example.com/other"` through the full pipeline (Task 4/5 prove it at unit level; Task 9 proves it at integration level; Task 11 re-witnesses it at e2e level).

## 4. Traps (call out explicitly in the plan doc)

- **4.1 Rules purity gate:** `tests/unit/test_rule_output_format_purity.py` source-scans `paxman/capabilities/*/rules/*.py` for the token `output_format` — the URL rule and the *generated* `idna_uts46_mapping.py` must never contain it (the generator's `RuntimeError` guard exists for exactly this).
- **4.2 Grammar semantic purity:** `tests/unit/test_grammar_semantic_purity.py` forbids mapping tokens to canonical values and rule-layer imports — `absolute_uri_recognition` must stay shape-only and must not import `parsing.py` or the IDNA tables.
- **4.3 Slots/frozen discipline:** notation is `@dataclass(frozen=True, slots=True)`; contract is `@dataclass(frozen=True)` **without** slots — the surface guard in Task 8 asserts both. Getting this backwards fails homogeneity.
- **4.4 Replay-hash sensitivity:** the moment URL joins the registry (Task 8), `tests/integration/test_default_replay_hashes.py` runs against 8 capabilities — the URL baseline literal must be captured only after Tasks 7+8 are final, and never hand-edited to green (anti-pattern; witness, not knob).
- **4.5 Coverage floor is 95%:** the WHATWG state machine (`parsing.py`) has many branches (scheme/host/port/path/query/fragment × special/non-special × fatal/recovery). The `_FATAL_CASES`/`_RECOVERY_CASES`/`_HOST_CASES`/`_NON_SPECIAL_CASES` tables are load-bearing for the floor — do not trim them to "reduce noise."
- **4.6 No NFC:** UTS #46 is applied to hosts only; path/query/fragment keep raw code points (percent-encoded on output). `café` vs `cafe\u0301` must produce distinct serializations (D9). Do not "helpfully" normalize.
- **4.7 Single parser source:** `parse_and_serialize` lives only in `parsing.py`; the rule (Task 5), integration tests (Task 9), and property tests (Task 11) must all import it — never re-implement the state machine in a test or rule copy (would fork semantics and break the replay hash).
- **4.8 import-linter leaf:** `parsing.py` may import only the IDNA data module; the rule may import only `parsing.py`; no cross-capability imports, no `paxman.core` imports from capabilities (existing layer rules already enforced — URL must not be the first violator).
- **4.9 Feature-flag leak:** `URLCapabilityContract` must add **no** extra `_extra_dict_fields()` keys (D14) — any added key changes the contract-key set asserted by the surface guard AND the replay hash (Traps 4.4).
- **4.10 stdlib vs WHATWG IDNA deviation:** Node's `new URL()` uses full WHATWG IDNA; stdlib `codecs`/`punycode` (RFC 3492) differs on denormalized inputs. Verification scope is valid IDNs only; the deviation is documented in `parsing.py`'s docstring, not papered over.
- **4.11 Strict pyright:** no `as Any`, no `# type: ignore`, no broad exception suppression in `paxman/` source (project anti-pattern). The state machine's error handling is explicit `return None` on fatal paths, never `except Exception: pass`.
- **4.12 Marker discipline:** all URL test modules use `[pytest.mark.capability, pytest.mark.url]`; the `url` marker must be registered in pyproject before any `pytest -m url` run (Task 8 adds it — do not run `-m url` earlier).

