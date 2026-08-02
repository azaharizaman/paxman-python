# Plan: Unify the Capability Contract & Rule Surface (NH-1 … NH-6)

- **Status:** Draft (analysis → plan only; NOT implemented, NOT committed)
- **Branch context:** built on top of `refactor/output_format_silence`
  (the `output_format` *behavioral* policy is already homogeneous and committed).
- **Goal of this plan:** make the *surface* that capability authors implement
  against unanimous, so future contributors cannot accidentally reintroduce the
  drift we just removed. Concrete domain differences (notation shape, grammar
  strategy, `active_grammars` conditional-vs-always-all) remain permitted.

---

## 1. Goal & non-goals

**Goal:** every capability follows ONE implementation for the cross-cutting
contract/rule mechanics:

- `output_format` field declaration
- `create_contract()` common-parameter signature
- `as_dict()` serialization (replay-safety)
- `normalize()` failure policy
- `Rule` identity metadata declaration

**Non-goals:**

- Changing the *behavior* of the already-committed `output_format` policy.
- Changing per-capability notation shapes, grammar strategies, or rule logic.
- Adding new capabilities or new validation rules.

---

## 2. The unanimous rules (target state)

| Area | Single unanimous implementation |
|------|----------------------------------|
| `output_format` field | `output_format: str | None = None` on **every** contract; resolved to the concrete default via `resolve_output_format`. Never a non-optional `str`. |
| `create_contract` signature | A fixed common-parameter block in this order: `excluded_rules`, `pinned_rules`, `year`, `output_format` (all `str | None = None`, with `excluded_rules`/`pinned_rules` as `Sequence[str] | None = None`), **keyword-only** (`*`), followed by capability-specific params. Enforced by a `ContractFactory` interface. |
| `as_dict()` | Derived from a shared base: always emits `capability_name`, `excluded_rules`, `pinned_rules`, `year`, `output_format`, plus a per-capability `_extra_dict_fields()` hook. Output must be **byte-identical** to today's per-capability `as_dict` to preserve existing replay hashes. |
| `normalize()` failure policy | `normalize()` (and `matches()`) **never raise** for a value that passed `matches()`. Rule code must not raise `ValidationError`/`RecognitionError`/`ContractError`. Contract-level misconfigurations are caught in `__post_init__`, not in rule methods. |
| `Rule` metadata | `name`, `strategy`, `provenance`, `citation` are **enforced** on every `Rule` subclass (fail at class-definition time if missing). |

---

## 3. Findings recap (current → target)

- **NH-1 (HIGH):** `output_format` field is `str` (non-optional) in
  `Country/contract.py:38` and `Phone/contract.py:64`; `str | None = None` in
  Email/Date/IP. → make all `str | None = None`.
- **NH-2 (HIGH):** `create_contract` common-parameter order/types drift across
  all five; `output_format` is even placed *before* the common trio in Phone and
  typed `str` there. Not enforced by any interface. → fix order/types + enforce
  via `ContractFactory`.
- **NH-3 (HIGH):** `as_dict()` hand-rolled 5 ways → a missed field silently
  breaks `replay_hash`. → derive from a shared base.
- **NH-4 (MED):** `normalize()` failure policy splits three ways
  (defensive-total Email/IP; `ValueError` guards Phone/Country; `ContractError`
  Date). → single defensive policy; remove Date's `ContractError` guards.
- **NH-5 (LOW):** `Rule.name`/`strategy`/`provenance`/`citation` are plain
  annotations, not enforced. → enforce at class-definition time.
- **NH-6 (structural root cause):** the `Capability` ABC only enforces
  `get_grammars`/`get_rules`; the contract surface is convention. → introduce a
  `CapabilityContract` base + `ContractFactory` protocol so the unanimous
  surface is *structural*, not documentary.

---

## 4. Implementation steps (ordered)

### Step 0 — Foundation: `CapabilityContract` base + `ContractFactory` protocol (NH-6)
**Files:** new `paxman/core/capability_contract.py`; `paxman/core/contract.py`
(export); `paxman/core/capability.py` (add `ContractFactory` protocol).

- Add `CapabilityContract` (frozen dataclass) providing:
  - `DEFAULT_OUTPUT_FORMAT: ClassVar[str]` and
    `OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]]` (overridden per subclass).
  - Standard fields: `capability_name: str = field(init=False)`,
    `excluded_rules: tuple[str, ...] = ()`,
    `pinned_rules: tuple[str, ...] | None = None`, `year: int | None = None`,
    `output_format: str | None = None`.
  - A base `__post_init__` that calls `resolve_output_format(...)` using the
    subclass `DEFAULT_OUTPUT_FORMAT`/`OFFERED_OUTPUT_FORMATS` and reassigns
    `output_format` via `object.__setattr__` (resolves NH-1 and centralizes
    validation).
  - A base `as_dict()` emitting the standard keys (replay-deterministic form)
    then `self._extra_dict_fields()` (resolves NH-3).
  - `active_grammars` remains an abstract/overridden `@property` per subclass
    (capability-specific; not part of the homogeneity mandate).
- Add `ContractFactory` (`Protocol`, runtime_checkable) requiring
  `create_contract(...) -> CapabilityContract` with the unanimous common block.
- **Why first:** NH-1/NH-2/NH-3 are realized by migrating the five contracts
  onto this base.

### Step 1 — Migrate the five contracts onto `CapabilityContract` (NH-1, NH-2, NH-3)
**Files:** `paxman/capabilities/{Email,Date,Country,IP,Phone}/contract.py`
(same five touched by the prior commit), plus each
`paxman/capabilities/<Name>/capability.py` (`create_contract`).

For each capability:
- Make the contract class inherit `CapabilityContract`.
- Set `capability_name` via `field(default="<name>", init=False)` as before.
- Set `DEFAULT_OUTPUT_FORMAT` / `OFFERED_OUTPUT_FORMATS` class vars
  (Email=`"email"`/`{}`; IP=`"ip"`/`{}`; Date=`"ISO"`/`{"US"}`;
  Country=`"alpha2"`/`{"alpha3","numeric","name"}`; Phone=`"e164"`/`{"rfc3966","national"}`).
- Remove the now-duplicated `__post_init__` `resolve_output_format` call and the
  hand-written `as_dict()`; replace `as_dict()` body with
  `_extra_dict_fields()` returning exactly the capability-specific keys
  currently emitted (e.g. Email: `include_obfuscated`, `include_localhost`;
  Date: `two_digit_base_year`; Country: `include_localized`, `include_historical`;
  IP: `include_ipv6`; Phone: `default_country`).
- Change `output_format` field to `str | None = None` (Country/Phone).
- In each `create_contract`, reorder to the unanimous common block
  (`excluded_rules`, `pinned_rules`, `year`, `output_format`) **keyword-only**
  (`*`), then capability-specific params; change `output_format` param to
  `str | None = None` (Country/Phone). Verify no call site uses positional args
  (tests/README use keyword args — confirm via grep).

### Step 2 — Enforce `Rule` metadata (NH-5)
**File:** `paxman/core/domain.py` (`Rule` ABC).
- Add `__init_subclass__` to `Rule` that asserts `name`, `strategy`,
  `provenance`, `citation` are defined on the subclass (raise `TypeError` at
  class-definition time). Minimal, structural, no behavior change.

### Step 3 — Unify `normalize()` failure policy (NH-4)
**Files:**
- `paxman/capabilities/Date/rules/en_50160_ed2010.py` (`:54`)
- `paxman/capabilities/Date/rules/us_federal_rules_ed2023.py` (`:54`)
- `paxman/capabilities/Phone/rules/{e164_ed2010.py:78, rfc_3966_ed2004.py:76, nanp_ed2024.py:148, :202}`
- `paxman/capabilities/Country/rules/iso_3166_historical_ed2020.py` (`:117`)

Changes:
- **Date:** remove the two `raise ContractError` in `_interpret_two_digit_year`;
  when the contract is not a `DateContract` (shouldn't happen in-pipeline) or
  `two_digit_base_year` is unset, default to `two_digit_base_year or 2000`
  (matching the defensive style of the ISO rule). No rule method raises a core
  error type anymore.
- **Phone:** the four `ValueError` guards split into two distinct triggers:
  - `e164_ed2010.py:78` (in `_canonical`, used by Section 6.1/6.2) and
    `rfc_3966_ed2004.py:76` fire when `output_format == "national"` and no
    country code is assigned — a genuine *contract* misconfiguration. Move it
    into `PhoneContract.__post_init__`: raise `ContractError` at construction
    when `output_format == "national"` and `default_country is None`.
  - `nanp_ed2024.py:148` and `:202` fire when `_nanp_digits` returns `None`
    (an invalid NANP digit string) — i.e. only when `matches()` did **not**
    pass. These are unreachable post-`matches()`, so simply drop the `raise`
    and let `normalize()` be defensive (best-effort, no raise).
  In both cases `normalize()` ends up exception-free. *Decision point for
  implementer:* the alternative is to keep the `ValueError` guards but document
  them as the unanimous convention — the recommended choice is
  construction-time `ContractError` (national case only) + defensive
  `normalize()`, which keeps rule methods exception-free.
- **Country-historical:** remove the unreachable `raise ValueError` in
  `normalize()` (defensive; `matches()` already gates the shape).

### Step 4 — Pin the policy in `HOW_TO_ADD_NEW_CAPABILITY.md`
**File:** `HOW_TO_ADD_NEW_CAPABILITY.md` (already edited for `output_format`).
- Add a short "Unanimous contract & rule surface" section restating the rules
  from §2, with the `CapabilityContract` base shown as the recommended pattern
  and the `normalize()`-never-raises rule stated explicitly (currently the doc
  only says "handle edge cases defensively").

### Step 5 — Guard tests (prevent regressions)
**Files:** new/updated under `tests/`.
- A test asserting all five capability contracts are subclasses of
  `CapabilityContract` and satisfy `ContractFactory`.
- A test asserting every `Rule` subclass defines `name`/`strategy`/
  `provenance`/`citation` (the `__init_subclass__` already enforces this; add a
  positive test + one negative compile-time example if feasible).
- Keep existing `output_format` tests (they already encode the homogeneous
  policy).

---

## 5. Dependency order & parallelization

1. **Step 0** (foundation) — must land first; everything else depends on it.
2. **Step 1** (contract migration) — sequential per capability is fine, but the
   five migrations are independent of each other → can be fanned out to parallel
   agents.
3. **Step 2** (Rule enforcement) and **Step 3** (normalize policy) — independent
   of Step 1; can run in parallel with Step 1.
4. **Step 4** (docs) and **Step 5** (tests) — after the code steps.

---

## 6. Risks / decisions to confirm during implementation

- **Replay-hash preservation:** the derived `as_dict()` MUST emit the exact same
  keys/values as today (modulo the already-committed concrete `output_format`).
  Add a test that snapshots `as_dict()` for each capability before/after, or
  compare against the committed behavior. **Highest-risk item.**
- **`create_contract` positional callers:** confirm none exist before reordering
  params; make the methods keyword-only (`*`) to prevent future positional use.
- **Protocol vs ABC philosophy:** introducing `CapabilityContract` as a base for
  *internal* capability contracts does NOT break the documented "Contract is a
  Protocol for external users" stance — external users may still pass any
  Protocol-satisfying object. Note this in the plan/PR description.
- **Phone national-without-country:** chose construction-time `ContractError`
  (recommended) vs keeping defensive `normalize()` with no error. Confirm with
  the user if they prefer a different failure mode.

---

## 7. Verification gates (all must pass)

```
uv run pyright --strict          # 0 errors (incl. new base + protocol)
uv run ruff check paxman/ tests/
uv run ruff format --check paxman/ tests/
uv run pytest tests/ -q          # all pass; replay-hash snapshots unchanged
import-linter lint              # boundaries intact (capabilities import only paxman.core)
```

---

## 8. Out of scope

- Any change to the `output_format` *behavioral* policy (already committed).
- New capabilities, new grammars, or new validation rules.
- Engine/orchestrator changes (rule filtering and candidate production are
  already centralized and unanimous — verified, not touched).
