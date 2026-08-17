# Independent Architecture Review — Paxman

**Date:** 2026-08-17
**Reviewer scope:** Long-term longevity, contributor scalability, extensibility to future capabilities, and mandates worth enforcing. Based solely on the current codebase (commit on `feature/CURRENCY-capability`, ~34.5K LOC of `paxman/` source across 545 files, 1,625 tests, 6 ADRs, CI workflow, and all contributor-facing docs).
**Nature:** Independent review. Praise and criticism are both earned by evidence in the repo, not by history or intent.

---

## 1. Executive Summary

**Verdict: The architecture is genuinely strong and unusually disciplined for a 0.2.0 library. The core abstractions — recognition/validation separation, semantic affinity routing, the formatting seam, engine-owned cross-match policy, and the provenance-first contract — are the right ones, and they are enforced structurally (base classes, `__init_subclass__` checks, CI source scans, import-linter), not just documented. This is the single strongest predictor of long-term longevity the repo has going for it.**

The risks are not in the abstractions. They are in:

1. **Ergonomics** — the global registry + freeze lifecycle and the manual `register_capability()` bootstrap are a first-five-minutes barrier that will deter casual adopters and contributors.
2. **Dual sources of truth** — `Contract` (Protocol) vs `CapabilityContract` (ABC) overlap and have already drifted; legacy artifacts (`Notation = list[str]`, `as_list()`) contradict the typed-notation reality and will mislead new contributors.
3. **Contribution cost** — the bar to add a capability correctly is high (unanimous surface, semantics ids, provenance metadata, data-placement rules, purity rules, 5 test layers, strict pyright, 95% coverage). The 62KB HOW_TO guide is thorough but is a reading tax, not a scaffolding tool.
4. **Data isolation cost** — the cross-capability import ban (correct!) has already produced duplicated CLDR/ISO 4217 tables in Currency and Money with no shared-regeneration story for them.

None of these are fatal. All are addressable without architectural surgery. Section 9 gives a ranked roadmap.

**For the Python community:** the niche — uniform, provenance-carrying, ambiguity-honest canonicalization across many domains with zero dependencies — is real and unoccupied. `babel`, `phonenumbers`, `iso3166`, and friends each solve one domain with no uniform contract, no provenance, and no ambiguity-as-status model. If Paxman reaches 1.0 with the current invariants intact, it has a credible claim to being the canonicalization layer for data-cleaning pipelines. The architecture aids that goal; the onboarding friction and packaging polish (Section 6) are what stand in the way.

---

## 2. What Was Reviewed

Read in full or in depth:

- `paxman/core/`: `domain.py`, `contract.py`, `capability_contract.py`, `capability.py`, `discovery.py`, `extensions.py`, `errors.py`
- `paxman/engine/orchestrator.py` (all phases: `_recognize`, `_filter_rules`, `_validate_affinity`, `_collect_candidates`, `_enforce_single_value_invariant`, `_dedup_candidates`, `_determine_status`, `_activated_rules`)
- `paxman/api/canonicalize.py`, `paxman/__init__.py`, `paxman/core/__init__.py`
- Capability implementations sampled across the difficulty spectrum: Email (protocol-small), IP/Date (typed-notation), Country/Currency (data-heavy, feature-gated), Money/Phone (cast-to-typed-contract rules), SI Unit (complex grammar, ADR-0005/0006), URL (15K-line generated IDNA table)
- All six ADRs, `ARCHITECTURE.md`, `capability_homogeneity_audit.md`, `CONTRIBUTING.md`, `TESTING_STRATEGY.md`, headers of `HOW_TO_ADD_NEW_CAPABILITY.md` (62KB) and `HOW_TO_ADD_NEW_GRAMMAR.md`, nested `capabilities/AGENTS.md`
- `pyproject.toml`, `.github/workflows/ci.yml`, test tree statistics (1,147 capability / 203 integration / 170 unit / 60 e2e / 45 property tests)
- Enforcement tests: `test_rule_output_format_purity.py` (CI source scan), `test_capability_exports.py`

---

## 3. Decision-by-Decision Assessment

### 3.1 Recognition/validation separation, with the engine owning all cross-match policy — **RIGHT, and unusually well executed**

`Grammar.recognize()` may only emit span-bearing `RecognitionMatch` objects; the engine validates span bounds and `raw_text == text[start:end]` per match (`orchestrator._recognize`), owns per-grammar containment dedup, total-order emission `(start, end, active-set index, grammar name)`, candidate dedup, and status determination. Grammars cannot validate, dedup, order, or map tokens to canonical values — and the F3 audit finding shows the project actually found and fixed a violation of this (Country's recognition-time canonicalization).

This is the load-bearing wall of the architecture, and it is straight. Evidence that it works in practice: two grammars reading the same span (`01/02/2026` US vs European) both survive to produce honest AMBIGUOUS. A future capability cannot quietly bend this — the span contract is enforced in the engine, not in convention.

### 3.2 Semantic affinity routing (ADR-0003) — **RIGHT**

`Grammar.semantics` (meaning claim) + `Rule.target_semantics` (meaning requirement) replaced name-based affinity. Consequences that matter long-term:

- A grammar whose meaning is already validated is a **one-file addition** — no rule edit. This is the difference between "extension seam" and "extension ceremony."
- Rules declare intent, not implementation coupling.
- F1 (the cartesian-product defect — every rule validating every grammar's output) cannot return via routing; affinity is explicit, fail-fast on dangling declarations (`_validate_affinity`), deterministic per contract.

The known residual risk is honest and documented in the ADR: a grammar falsely claiming a shipped `semantics` id with divergent field mapping would mis-canonicalize silently until a test catches it. The consistency-guard test is the mitigation. This trade (test-time guarantee over runtime introspection) is correct for a performance-sensitive, deterministic engine — but it must stay a *maintained* guarantee as grammars multiply (see Section 8, Mandate M6).

### 3.3 The formatting seam + CI purity scan — **RIGHT, and the enforcement mechanism is the best idea in the repo**

`normalize()` always returns the default canonical form; `Capability.format_value()` is the only presentation seam; and `tests/unit/test_rule_output_format_purity.py` scans the raw source of every `paxman/capabilities/*/rules/*.py` for the token `output_format` — in code, comments, or docstrings — and fails CI.

This is architecture-as-law rather than architecture-as-documentation. The homogeneity audit shows why it's needed: F4 (`output_format` honored inconsistently, Phone's `_canonical` triplication) was a real defect class. The scan makes regression mechanically impossible. Future capabilities inherit the guarantee for free.

### 3.4 Feature gating at two loci (`active_grammars` → MISSING; `requires_features` → INVALID) — **RIGHT, non-obvious, and now engine-enforced**

The audit's Oracle verdict (one single mechanism would be *wrong* because input-shape features and authority features have different failure statuses) is correct and is now engine-enforced in `_filter_rules()`: a rule requiring a feature the contract lacks fails fast with `ContractError` (metadata/contract mismatch), a present-but-false feature drops the rule (→ INVALID). No casts inside `matches()` for gating.

This distinction (a disabled grammar makes input *unseen*; a dropped rule makes input *seen but unvalidated*) is subtle, correct, and — importantly for contributors — decided by the engine, not by each rule author's judgment.

### 3.5 Provenance-first, ambiguity-as-status, single-value invariant (ADRs 0001/0004) — **RIGHT; these are the product**

- No authority → INVALID, never a best-effort value.
- AMBIGUOUS means exactly one thing after ADR-0004: genuine single-mention spec conflict. Multi-entity input fails fast with `MultipleMentionsError`, with span-overlap clustering so cross-grammar reads of one mention stay AMBIGUOUS.
- Caller-owned segmentation is a hard invariant, not a convention.

This triad (deterministic, provenance-carrying, ambiguity-honest) is the entire differentiation vs every incumbent library. It is also the set of properties most likely to come under pressure from future capability requests ("just pick the most likely country," "add fuzzy matching"). Section 8 codifies the pushback.

### 3.6 Explicit registry with freeze-on-first-run — **DEFENSIBLE, but the highest-friction decision in the codebase**

Determinism argument: the composed grammar/rule set is fixed per process, so results cannot shift mid-run. Real costs:

- Every program begins with `register_capability(Email())` boilerplate (README quick-start shows it). Nothing auto-registers shipped capabilities; there is no entry-point or lazy default registration path.
- Registration after the first `canonicalize()` raises. Long-running applications that discover a need for another capability later must call the test-only `reset_registry()` (which is exactly what `tools/si_unit_canonicalize.py` does — a tool mutating global state is the smell made visible).
- Registration is not thread-safe (module-level dict + flag, no lock). Post-freeze reads are safe; concurrent first-use registration in a multithreaded app can race.

This is a deliberate explicitness-over-convenience trade, and at 0.x it is recoverable. But it is the single biggest "why is this hard to start using?" contributor, and Section 9 proposes a compatible mitigation (a sanctioned bulk registration helper / shipped-capabilities preset that preserves freeze semantics).

### 3.7 Community extension seam (`register_grammar` / `register_rule` + `extra_grammars` opt-in) — **RIGHT**

Opt-in only, name-collision fail-fast, unknown extra names silently skipped for grammar activation (deterministic identical behavior whether or not an extension is installed — a thoughtful property), dangling rule semantics fail fast. The README's worked example is genuinely copy-pasteable and works against shipped rules. This is the correct "open for extension, closed for modification" mechanism, and it lets downstream users extend *without upstreaming*, which lowers the community bar in the right way.

### 3.8 Capability isolation via import-linter layers — **RIGHT, with one real cost**

`api → engine → capabilities → core`, capabilities never import siblings, core imports nothing. Enforced by import-linter in CI. The cost is already visible: Currency and Money each maintain their own `grammar/data/currency_symbols.py` + `currency_words.py`, and Country/Phone duplicate ISO 3166 knowledge implicitly. Two copies of CLDR-derived tables in one library is a drift hazard *today*, and it grows with every locale-adjacent capability added. The isolation mandate is correct; the missing piece is a data strategy: shared source snapshots that *regenerate into* per-capability tables (the pattern already exists for ISBN/SIUnit/URL generated data — it just doesn't cover the hand-maintained shared-vocabulary tables).

### 3.9 Determinism by construction, zero runtime dependencies — **RIGHT**

`dependencies = []` is a major trust asset for a library that wants to sit at the bottom of data pipelines. Determinism is scoped honestly (fixed library snapshot, including registry contents and rule-data tables). No clock, no network, no locale-dependent casing — every canonicalization library predecessor has been bitten by locale-dependent `.upper()`/`.lower()`; keeping this invariant will require vigilance (e.g., future Unicode-heavy capabilities).

### 3.10 ADR discipline + preserved audit trail — **RIGHT**

Six ADRs with real alternatives-considered sections; `capability_homogeneity_audit.md` preserved as historical record with resolution addenda (F1–F4 all resolved). This is the mechanism by which the *next* maintainer will understand why the code is shaped this way. For a project seeking community contribution, this documentation of reasoning is as valuable as the enforcement tests.

### 3.11 Test architecture — **EXEMPLARY**

Five layers (unit / capability / integration / e2e / property with Hypothesis), markers wired into pyproject, per-package 95% coverage gates in CI on three Python versions, domain-object property tests (immutability, hashability). Property tests for domain contracts are exactly right for a library whose core value objects are frozen dataclasses.

---

## 4. Weaknesses and Risks (ranked)

### W1 — Contract surface has two overlapping sources of truth, and they have drifted

`Contract` is a runtime-checkable Protocol ("user flexibility"); `CapabilityContract` is an ABC that every shipped contract MUST inherit ("homogeneity mandate"). In practice the ABC won — the capabilities' AGENTS.md says MUST inherit — so the Protocol is now the documentary interface with drift:

- `Contract` does not declare `extra_grammars`; the engine probes with `getattr(contract, "extra_grammars", ())` (`orchestrator._recognize`, `_activated_rules`). A third-party duck-typed contract satisfying the Protocol silently loses the extension seam.
- `Contract.output_format` is typed `str | None`, but `CapabilityContract.__post_init__` always resolves it to a concrete `str` — the Protocol's type is a lie for every real contract.
- `ContractFactory` docstring still says "the five capability classes satisfy it" — there are ten.

Risk level: moderate now (confuses contributors, invites wrong duck-typed implementations), high later (if the Protocol is treated as the public contract promise, every drift becomes a compat bug). Recommendation in Section 9.

### W2 — Legacy artifacts contradict the typed-notation reality

`paxman/core/domain.py` still defines `Notation = list[str]` ("list[str] is the generic contract" — false: every capability defines a frozen dataclass notation and rules are `Rule[CountryNotation]` etc.), and every notation carries an `as_list()` bridging method from the abandoned generic-list interface. Tests still exercise `as_list()` (45 references), cementing the legacy. A new contributor reading `domain.py` first — the natural order — will infer the wrong notation model. This is cheap to fix and pure debt removal.

### W3 — The `cast(WhateverContract, contract)` pattern inside rules

The sanctioned pattern for reading capability-specific contract fields is a runtime-unchecked `cast` (Money, Phone, SI Unit rules). It works, it's governed ("cast only for validity-affecting parameters"), but a mistyped cast in a community rule surfaces as `AttributeError` wrapped in `ValidationError` at pipeline time — diagnosable, yet avoidable. The root cause is that `Rule` is parameterized only on notation: `Rule[NotationT]`. A future `Rule[NotationT, ContractT]` (breaking, 1.0 material) would eliminate the cast class entirely. Not urgent; worth an ADR before 1.0.

### W4 — Import-time weight of capability registration

`from paxman.capabilities import Email` executes the capabilities `__init__`, which imports all ten capability packages — including URL's 15,019-line generated IDNA table and the full Country/SIUnit data modules. Registering one capability pays for all ten. At current scale (~34.5K LOC) this is imperceptible; at twenty capabilities with heavy generated data it becomes a real import-time cost for the most common usage pattern. Mitigation exists (PEP 562 module-level `__getattr__` lazy exports) and can be adopted later without breaking the API, but it should be decided *before` the capability count doubles.

### W5 — Exhaustive pipeline cost model is fine now, uninstrumented later

Every active grammar runs over the full input; every recognition is offered to every affinity-matched active rule; each `matches()` + `normalize()` re-does parse work (e.g., Money's `parse_amount` runs in both). At 10 capabilities × ≤7 rules this is nothing. A future capability with dozens of grammars (locale-aware name recognition is the obvious candidate) or long multi-mention inputs (the invariant limits mentions, helpfully) could change that. There is no benchmark harness in the repo. Not a today-problem; note it so it is a measured decision later, not a surprise.

### W6 — Packaging and docs polish gaps that matter for community trust

- `pyproject.toml`: no `license` field (LICENSE.md exists but is undeclared), no `project.urls`, no readme pointer, classifiers lack License; `dev` dependencies declared twice (`[project.optional-dependencies].dev` and `[dependency-groups].dev`) with divergent floors (`import-linter>=2.10` vs `>=2.13`).
- `CONTRIBUTING.md` says `cd paxman-alternative` (stale repo name) and gives a setup command that differs from CI's `uv sync --all-extras`; it links ARCHITECTURE.md but never mentions the two HOW_TO guides — the actual contributor manuals.
- No CHANGELOG, no examples/ directory, no docs site. For a library whose pitch is "trust me, I cite authorities," the packaging surface undercuts the message.
- Capability `version` field (`SIUnitCapability.version = "1.0.0"`) is dead metadata — nothing consumes it (`VersionStamp` records only `paxman_version`). Either wire it into provenance stamps or remove it; dead version fields mislead.

### W7 — CapWords package directories

`paxman/capabilities/SIUnit/` violates PEP 8 module naming, forces awkward imports (`from paxman.capabilities.SIUnit.capability import SIUnitCapability`), and requires N-code scoped ignores for acronym aliases. Deliberate and consistent — but it is a permanent wart whose only fix (rename) is maximally breaking. If it is ever done, it must be at 1.0; realistically it never will be. Accept and document.

### W8 — Registration thread-safety

Module-level registries without locks. Fine for the canonical usage (register at import, canonicalize later) and for CI; racy for concurrent first-use registration in multithreaded embedders. A one-paragraph contract statement ("register from a single thread before first use") or a lock at registration time closes it.

---

## 5. Will This Architecture Attract or Deter Community Contributors?

**Both — deliberately, and mostly in the right direction. It deters drive-by contributors and rewards sustained ones. That is a defensible position for a correctness-critical library, but only if the friction that deters is *essential* friction (invariant enforcement) rather than *accidental* friction (ergonomics and stale docs). Today the repo has both kinds.**

### What aids contribution

1. **The extension seam is the best contributor funnel.** A downstream user who needs `YYYY.MM.DD` dates never has to touch the library or pass review — `register_grammar` + `extra_grammars` and they're done, validated by shipped ISO rules (ADR-0003's design goal, delivered). Most "I wish it supported X" requests end here, with zero maintainer load.
2. **Homogeneity makes capability code legible across domains.** Having read one capability package, you can navigate all ten. The unanimous surface (contract base class, notation, grammar/rule metadata, `create_contract` common block) means a contributor's second capability is dramatically cheaper than their first — this is the architecture compounding.
3. **Enforcement replaces review pedantry.** `__init_subclass__` metadata checks, the purity scan, import-linter, and export-completeness tests mean CI catches architecture violations mechanically. Contributors get fast, objective feedback instead of style debates. This is exactly how you scale a project past bus-factor-one.
4. **The HOW_TO guides are genuinely thorough** — 12 steps with pitfalls, patterns, test-layer expectations, and a separate grammar guide that explains the semantics-id decision fork (reuse meaning vs add rule). Few libraries document their extension protocol this completely.
5. **ADR trail + preserved audit** means a contributor can understand *why* the constraints exist — including that the constraints were earned from real defects (F1–F4), not taste.

### What deters contribution

1. **The reading tax before the first line of code.** 62KB HOW_TO + dense nested AGENTS.md governance + ARCHITECTURE.md. There is no scaffolding tool: a contributor implements the unanimous surface *by hand from prose* (notation, contract with class vars and `field(init=False)`, capability wiring, `create_contract` with the exact common block, package inits with `__all__`, five test layers). A `scripts/new_capability.py` scaffolder emitting the skeleton with TODOs would convert most of that 62KB from reading to verification. This is the single highest-leverage contributor investment available.
2. **Strict pyright + zero suppression + 95% per-package coverage + TDD.** Correct for this project's claims; genuinely filtering for casual contributors. Keep it — but pair it with good-first-issue-shaped tasks that are data-adds (alias tables, spelling variants — explicitly cheap after ADR-0002 killed the replay-hash ceremony) so the bar has an on-ramp.
3. **The bootstrap ritual** (W-registry in §3.6): every example, test, and tool starts with registration dance + autouse `_clean_registry` fixtures. Contributors internalize it; evaluators bounce off it.
4. **Stale/contradictory docs** (W1, W6): "five capability classes," `paxman-alternative`, Protocol-vs-ABC drift, `Notation = list[str]`. Each individually small; collectively they signal a project whose docs lag its code — the opposite of the ADR discipline elsewhere.
5. **CI only runs on PRs to `main`.** Feature-branch workflows (this repo's own pattern — work happens on `feature/*` branches) get no CI signal until they target main. Fix is one line in the workflow trigger.

**Net:** the architecture *aids* the contributors the project should want, and the deterrents are mostly curable accidents rather than the essential enforcement. The essential friction (strictness) is exactly what a canonicalization authority should impose.

---

## 6. Scalability to Future Capabilities (Planned and Unplanned)

The pipeline has absorbed ten capabilities of genuinely different shapes — pure-regex (Email), typed-positional (Date), table-lookup (Country, Currency), grammar-compound (SI Unit), full-parser (URL with generated 15K-line IDNA data) — without the core growing capability knowledge. That is the strongest scalability evidence available: the engine (`orchestrator.py`) contains zero domain conditionals. Stress-testing against plausible future capabilities:

| Future capability | Architectural fit | Notes |
|---|---|---|
| Time / Timezone | **Good** | No clock access = no `now()` temptation possible; IANA tz names are a lookup table + provenance. Deterministic by construction. |
| Language codes (BCP-47), Locale | **Good** | Currency/Country shape: codes + names + CLDR tables. Will *sharpen* W-duplication (CLDR data shared with Country/Currency) — needs the shared-snapshot strategy first. |
| National identifiers (SSN, passport formats) | **Good, with scope care** | Regex + checksum rules fit perfectly (ISBN is the template). Provenance = national registries; `lifecycle` field already exists for deprecations. |
| Names (person-name normalization) | **Poor — and correctly so** | No authoritative spec yields one canonical personal name; the architecture would honestly return AMBIGUOUS/INVALID forever. The provenance-first invariant is the scope guard; it should be *cited* when declining such requests. |
| Fuzzy/approximate matching | **Rejected by design** | No fuzzy logic is an explicit determinism clause. Confidence scores would corrupt the Resolution model. This is a feature; guard it (M4). |
| Multi-entity extraction ("find all emails in text") | **Correctly out of scope** | ADR-0004 assigns segmentation to the caller. A companion recipe/docs (regex-segment-then-canonicalize loop) would serve the demand without bending scope. |
| Capability with 20+ grammars (locale names) | **Fits, watch W4/W5** | Import weight and exhaustive-match cost become measurable; lazy exports + a benchmark would keep it a data decision. |
| Streaming / batch APIs | **Unplanned, fits** | Pipeline is pure per-call; a batch wrapper is trivial and needs no core change. |

**Structural verdict:** the seam inventory (Notation, Grammar with `semantics`/`single_value`, Rule with `target_semantics`/`requires_features`/provenance, `CapabilityContract`, `format_value`, extension registries) has so far been sufficient for every shipped shape, and the two ADR-driven refactors (semantics, formatting) were absorbed *because* the seams were narrow. The engine is the most stable layer and has never needed domain knowledge — that is what "scalable" should mean.

**Honest ceiling:** the single-value invariant and caller-owned segmentation cap the library at mention-level canonicalization forever. That is the right product, but it should be said loudly (M1) so nobody plans a document-extractor on top and blames the architecture.

---

## 7. Is the Implementation Strong Enough for Unplanned Capabilities?

Yes, with three preconditions already identified above:

1. **Shared-vocabulary data strategy** (before more CLDR/ISO-adjacent capabilities): regenerate-into-per-capability-tables from a shared snapshot; duplication is the one cost of isolation that compounds.
2. **Scaffolder tooling**: the unanimous surface is now large enough that hand-assembly from prose is the bottleneck and error source; generate the skeleton instead.
3. **Decide W1 (Protocol vs ABC) and W3 (`Rule[NotationT, ContractT]`) before 1.0**, because both are public-surface decisions that are cheap to fix at 0.x and breaking after.

---

## 8. Mandates to Voice Loudly

These are the invariants that keep future capabilities aligned with the project's direction. They exist in code or ADRs today, but several are enforced only by convention + review and deserve to be stated as admission criteria in the contributor docs (and eventually on a "Scope & Philosophy" page).

- **M1 — One entity per call, forever.** Paxman canonicalizes a single presumed mention; segmentation belongs to the caller (ADR-0004). Any proposal whose shape is "extract N entities from text" is out of scope by charter, not by limitation.
- **M2 — Determinism is constitutional.** No clock, no network, no environment, no locale-dependent behavior, no randomness — across recognition, validation, and formatting. Any capability that cannot be a pure function of (input, contract, library snapshot) is not a Paxman capability. This will be tested by temptation (exchange rates, "current" tz data): the answer is snapshot-with-publication-year tables (the `year` temporal filter already exists for exactly this).
- **M3 — Provenance-first: no authority, no canonical value.** INVALID — never best-effort output. Best-effort modes are opt-in contract flags with reject-by-default (the ADR-0005/0006 pattern: `allow_multi_solidus`, `allow_split_word_prefixes`, `default_currency`). New ambiguity must default to rejection.
- **M4 — No fuzzy matching, no confidence, no ML.** Ambiguity is a status (AMBIGUOUS), not a probability. Suggestions otherwise change the product's identity.
- **M5 — Grammars recognize; rules validate; `format_value()` presents.** Never moved, never shared. Grammars emit spans and stop; authority data lives only in `rules/data/`; the purity scan holds the line. Recognition keys never carry canonical meaning (the F3 lesson).
- **M6 — `semantics` ids are a semantic contract.** Every grammar claiming an id must agree on notation field mapping and canonicalization expectation; the per-id consistency test is mandatory for every new grammar. This is the one ADR-0003 residual risk that grows with grammar count.
- **M7 — Strict by default, permissive by opt-in.** Conservative default contracts; every relaxation is an explicit, documented, named flag that resolves shared-symbol/ambiguous input only under user assertion (Currency's candidate-checked `default_currency` is the model).
- **M8 — Capability isolation is absolute; shared data regenerates, never imports.** Sibling imports stay banned; shared vocabularies (CLDR, ISO) get a shared snapshot tool that writes each capability's local tables.
- **M9 — Contracts inherit `CapabilityContract`; rules carry full provenance metadata.** The unanimous surface is the homogeneity guarantee; a capability with a hand-rolled contract surface or uncited data tables does not merge.
- **M10 — Resolution statuses are not overloaded.** MISSING = unseen, INVALID = seen unvalidated, SUCCESS = one value, AMBIGUOUS = one mention, many values. New capabilities use these four; they do not invent statuses or smuggle multi-entity results into AMBIGUOUS.
- **M11 — Every data table cites its authority.** No hand-invented mappings without a specification; generated tables regenerate from snapshots via `tools/`, never by hand.
- **M12 — Breaking changes at 0.x are budgeted; at 1.0 they are semver-major with deprecation.** The ADR-0002/0003 precedent (break-at-0.x, document in ADR) is the pattern; a published deprecation policy precedes 1.0.

---

## 9. Recommendations (ranked by leverage)

**Near-term (ergonomics & trust, no architecture change):**
1. Ship a capability scaffolder (`tools/new_capability.py` or a cookiecutter) generating the unanimous surface skeleton + test stubs; shrink the 62KB guide from *instructions* to *commentary*.
2. Add a sanctioned bootstrap helper — e.g., `register_all_shipped()` or per-capability lazy registration through PEP 562 — preserving freeze semantics; document "register from one thread before first use" (closes W8 and most of §3.6's friction).
3. Fix the stale/drifted surfaces: `Notation = list[str]` + `as_list()` removal plan, `ContractFactory` "five classes" docstring, `CONTRIBUTING.md` repo name + setup drift + HOW_TO links, `pyproject` license/urls/readme/classifiers + dev-deps dedup, CI trigger for feature branches, consume-or-remove `Capability.version`.
4. Write the segmentation recipe doc (split-then-canonicalize loop) to serve extraction demand without scope bend.

**Mid-term (structural debt, before capability count grows):**
5. Resolve Protocol-vs-ABC formally (ADR): either shrink `Contract` to what the engine actually requires (including `extra_grammars`, typed `str` for resolved `output_format`) or declare `CapabilityContract` the only sanctioned base and demote the Protocol to engine-internal. Kill the `getattr` probes.
6. Stand up the shared-vocabulary data pipeline (M8) — starting with the already-duplicated Currency/Money tables.
7. Add a minimal benchmark harness (one scenario per capability, tracked in CI or nightly) so W5 is a measured decision.
8. Consider PEP 562 lazy exports for `paxman.capabilities` before the next data-heavy capability lands (W4).

**Before 1.0 (public-surface commitments):**
9. ADR on `Rule[NotationT, ContractT]` (eliminating rule-side casts, W3) — adopt or explicitly decline.
10. Publish versioning/deprecation policy (M12), CHANGELOG, and the Scope & Philosophy page carrying M1–M12 as admission criteria.
11. Compatibility audit of the community seam (`register_grammar`/`register_rule` signatures, `extra_grammars` semantics) — this is the de-facto plugin API; freeze it deliberately.

---

## 10. Bottom Line

The hard decisions were made well, made explicitly (ADRs), and made enforceable (CI). The engine is domain-free, the seams are narrow, the extension model is real, and the test architecture is exemplary. The failure modes that kill canonicalization libraries — presentation logic creeping into validation, per-capability drift, best-effort guesswork, untracked data provenance — have each already happened here once, been caught, and been fenced off structurally.

What stands between this repo and community traction is not architecture. It is the first-five-minutes experience (registration boilerplate, no scaffolder, packaging polish), a handful of drifted surfaces that contradict the otherwise-immaculate documentation discipline, and a data-duplication cost that will compound quietly with each locale-adjacent capability. All are tractable. The mandates in Section 8, stated loudly and enforced at admission, are what will keep capability #20 as honest as capability #1.
