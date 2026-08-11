"""Engine orchestrator — runs the recognition → validation pipeline."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import version as _get_version
from typing import Any

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import freeze_registry, get_capability
from paxman.core.domain import (
    Candidate,
    Grammar,
    GrammarRule,
    RecognitionMatch,
    RecognizedRep,
    Resolution,
    Rule,
    VersionStamp,
)
from paxman.core.errors import (
    CapabilityError,
    ContractError,
    RecognitionError,
    ValidationError,
)
from paxman.core.extensions import get_extended_grammars, get_extended_rules


def _resolve_version() -> str:
    """Resolve the installed paxman package version."""
    try:
        return _get_version("paxman")
    except Exception:
        return "0.1.0"


PAXMAN_VERSION = _resolve_version()


@dataclass(frozen=True)
class ExecutionResult:
    """Final output from the orchestration pipeline."""

    status: Resolution
    canonicalized_value: str | None
    candidates: tuple[Candidate, ...]
    contract: Contract
    version_stamp: VersionStamp


def run_capability(text: str, contract: Contract) -> ExecutionResult:
    """Run the full pipeline: recognition → validation → result."""
    freeze_registry()
    capability = get_capability(contract.capability_name)

    shipped_grammars = capability.get_grammars()
    all_grammars = [
        *shipped_grammars,
        *get_extended_grammars(capability.name),
    ]
    _assert_unique_names("grammar", all_grammars)
    all_rules = [*capability.get_rules(), *_activated_rules(capability, contract)]
    _assert_unique_names("rule", all_rules)
    _validate_affinity(all_grammars, all_rules)
    recognitions = _recognize(
        text,
        all_grammars,
        [g.name for g in shipped_grammars],
        contract,
    )
    had_recognitions = len(recognitions) > 0

    rules = _filter_rules(all_rules, contract)
    candidates = _collect_candidates(capability, recognitions, rules)

    status = _determine_status(candidates, had_recognitions)
    canonical_value = _extract_canonical_value(candidates, status)
    version_stamp = VersionStamp(paxman_version=PAXMAN_VERSION)

    return ExecutionResult(
        status=status,
        canonicalized_value=canonical_value,
        candidates=tuple(candidates),
        contract=contract,
        version_stamp=version_stamp,
    )


def _assert_unique_names(kind: str, items: Sequence[Grammar[Any] | Rule[Any]]) -> None:
    """Fail fast when a composed grammar or rule name is duplicated.

    Shipped names must never be shadowed or duplicated by community
    extensions: a duplicate would make grammar-name routing and provenance
    attribution ambiguous, so reject it at composition time (D4).
    """
    names = [item.name for item in items]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise CapabilityError(f"Duplicate {kind} name(s): {duplicates}")


def _recognize(
    text: str,
    all_grammars: Sequence[Grammar[Any]],
    shipped_names: Sequence[str],
    contract: Contract,
) -> list[RecognizedRep[Any]]:
    """Run active grammars, dedup contained matches per grammar, and order.

    Every match is validated against the span contract (bounds within the
    input, ``raw_text`` equal to the matched slice) before dedup; a grammar
    returning a malformed match raises ``RecognitionError`` naming the
    grammar. The engine owns all cross-match policy: containment dedup runs
    strictly within a single grammar's output (never across grammars, so
    cross-grammar ambiguity stays observable), and recognitions are emitted
    in the total order (start, end, active set index, grammar name) where the
    index follows the composed active set: ``contract.active_grammars``
    first, then any opt-in ``contract.extra_grammars`` names (unknown extra
    names are silently skipped, D4).

    A contract whose ``active_grammars`` is ``None`` (the base-class default)
    falls back to ``shipped_names`` — every shipped grammar in
    ``get_grammars()`` declaration order — so adding a shipped grammar to a
    capability activates it with no contract edit. Community grammars stay
    opt-in via ``extra_grammars`` in both cases.
    """
    supported_names = {g.name for g in all_grammars}
    extra_grammars = getattr(contract, "extra_grammars", ())
    declared = contract.active_grammars
    active_source = shipped_names if declared is None else declared
    # Deduplicate contract names, keeping first occurrence: each supported
    # grammar runs at most once and grammar_index stays aligned with
    # active_grammars (a duplicate contract entry must not double-run it).
    # Community grammars opt in via extra_grammars and keep their declared
    # order after the shipped slots.
    active_names = list(
        dict.fromkeys(
            n for n in [*active_source, *extra_grammars] if n in supported_names
        )
    )
    grammar_index = {name: i for i, name in enumerate(active_names)}
    by_name = {g.name: g for g in all_grammars}
    active_grammars = [by_name[name] for name in active_names]

    ordered: list[tuple[int, int, int, str, RecognitionMatch[Any]]] = []
    for grammar in active_grammars:
        try:
            matches = grammar.recognize(text)
        except Exception as exc:
            raise RecognitionError(
                rule=grammar.name,
                message=f"Grammar failed: {exc}",
                original_error=exc,
            ) from exc
        for match in matches:
            if not 0 <= match.start <= match.end <= len(text):
                raise RecognitionError(
                    rule=grammar.name,
                    message=(
                        f"Grammar '{grammar.name}' returned a match with span "
                        f"[{match.start}, {match.end}) outside the input "
                        f"bounds [0, {len(text)}]"
                    ),
                )
            if match.raw_text != text[match.start : match.end]:
                raise RecognitionError(
                    rule=grammar.name,
                    message=(
                        f"Grammar '{grammar.name}' returned a match whose "
                        f"raw_text {match.raw_text!r} does not equal "
                        f"text[{match.start}:{match.end}] = "
                        f"{text[match.start : match.end]!r}"
                    ),
                )
        for match in _dedup_spans(matches):
            ordered.append(
                (
                    match.start,
                    match.end,
                    grammar_index[grammar.name],
                    grammar.name,
                    match,
                )
            )

    ordered.sort(key=lambda item: (item[0], item[1], item[2], item[3]))

    recognitions: list[RecognizedRep[Any]] = []
    for start, end, _index, grammar_name, match in ordered:
        grammar_ref = GrammarRule(
            capability_name=contract.capability_name,
            grammar_name=grammar_name,
        )
        recognitions.append(
            RecognizedRep(
                notation=match.notation,
                contract=contract,
                grammar=grammar_ref,
                start=start,
                end=end,
                raw_text=match.raw_text,
            )
        )
    return recognitions


def _dedup_spans(
    matches: list[RecognitionMatch[Any]],
) -> list[RecognitionMatch[Any]]:
    """Drop matches fully contained in a longer match from the SAME grammar.

    ``longer wins``: when two matches from one grammar overlap, the match
    covering more of the input survives; an exact tie keeps the first.
    Runs strictly within one grammar's output — overlapping matches from
    different grammars are preserved so cross-grammar ambiguity stays
    observable.
    """
    ordered = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))
    kept: list[RecognitionMatch[Any]] = []
    for match in ordered:
        if any(other.start <= match.start and match.end <= other.end for other in kept):
            continue
        kept.append(match)
    return kept


def _filter_rules(all_rules: list[Rule[Any]], contract: Contract) -> list[Rule[Any]]:
    """Return rules based on pinning, exclusion, year, and feature filters.

    When pinned_rules is set, ONLY those rules run (excluded_rules is ignored).

    Feature gating runs LAST, after pin/exclude and year selection: a rule
    whose required contract features are present-but-false is dropped (a
    recognized input then yields INVALID), and a rule naming a feature the
    contract does not have is a metadata/contract mismatch that fails fast
    with ContractError rather than silently excluding the rule.
    """
    if contract.pinned_rules is not None:
        pinned_set = set(contract.pinned_rules)
        known_names = {r.name for r in all_rules}
        unknown = pinned_set - known_names
        if unknown:
            raise ContractError(f"Unknown pinned rule(s): {sorted(unknown)}")
        active_rules = [r for r in all_rules if r.name in pinned_set]
    else:
        excluded = set(contract.excluded_rules)
        active_rules = [r for r in all_rules if r.name not in excluded]

    if contract.year is not None:
        active_rules = [
            r for r in active_rules if r.provenance.publication_year <= contract.year
        ]

    for rule in active_rules:
        missing = [
            feature
            for feature in rule.requires_features
            if not hasattr(contract, feature)
        ]
        if missing:
            raise ContractError(
                f"Rule {rule.name!r} requires missing contract feature(s): "
                f"{sorted(missing)}"
            )

    return [
        r
        for r in active_rules
        if all(getattr(contract, feature, False) for feature in r.requires_features)
    ]


def _validate_affinity(
    all_grammars: Sequence[Grammar[Any]], rules: list[Rule[Any]]
) -> None:
    """Ensure every rule's declared grammars exist in the composition.

    The composition covers shipped and community grammars alike; a dangling
    grammar name would silently exclude a rule from ever running, so fail
    fast at pipeline start rather than producing a wrong (e.g. INVALID) result.
    """
    known_grammars = {g.name for g in all_grammars}
    for rule in rules:
        unknown = [g for g in rule.target_semantics if g not in known_grammars]
        if unknown:
            raise ContractError(
                f"Rule {rule.name!r} declares unknown grammar(s) "
                f"{sorted(unknown)}; available: {sorted(known_grammars)}"
            )


def _collect_candidates(
    capability: Capability[Any],
    recognitions: list[RecognizedRep[Any]],
    rules: list[Rule[Any]],
) -> list[Candidate]:
    """Match recognitions against rules and collect candidates.

    Routes each recognition only to rules whose ``target_semantics`` includes the
    producing grammar's name (ARCHITECTURE.md:201), formats each validated
    value through the capability's ``format_value()`` seam, then dedups
    identical candidate tuples so the candidate multiset is stable regardless
    of routing.
    """
    candidates: list[Candidate] = []
    for recognition in recognitions:
        grammar_name = recognition.grammar.grammar_name
        for rule in rules:
            if grammar_name not in rule.target_semantics:
                continue
            try:
                if rule.matches(recognition.notation, recognition.contract):
                    canonical = rule.normalize(
                        recognition.notation, recognition.contract
                    )
                    value = capability.format_value(
                        canonical,
                        recognition.contract.output_format,
                        recognition.notation,
                    )
                    candidates.append(
                        Candidate(
                            value=value,
                            recognition_rule=grammar_name,
                            validation_rule=rule.name,
                            provenance=(rule.provenance,),
                        )
                    )
            except Exception as exc:
                raise ValidationError(
                    rule=rule.name,
                    message=f"Validation failed: {exc}",
                    original_error=exc,
                ) from exc
    return _dedup_candidates(candidates)


def _dedup_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Drop identical (value, recognition_rule, validation_rule) tuples.

    Provenance is deterministic per (rule, grammar) pair, so collapsing on this
    key preserves all information while keeping the candidate multiset stable
    under any future over-declaration of ``target_semantics``.
    """
    seen: set[tuple[str, str, str]] = set()
    deduped: list[Candidate] = []
    for candidate in candidates:
        key = (
            candidate.value,
            candidate.recognition_rule,
            candidate.validation_rule,
        )
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    return deduped


def _determine_status(
    candidates: Sequence[Candidate], had_recognitions: bool
) -> Resolution:
    """Determine resolution status from candidates."""
    if not candidates:
        if had_recognitions:
            return Resolution.INVALID
        return Resolution.MISSING
    values = {c.value for c in candidates}
    if len(values) == 1:
        return Resolution.SUCCESS
    return Resolution.AMBIGUOUS


def _extract_canonical_value(
    candidates: Sequence[Candidate], status: Resolution
) -> str | None:
    """Extract canonical value if status is SUCCESS."""
    if status == Resolution.SUCCESS and candidates:
        return candidates[0].value
    return None


def _activated_rules(
    capability: Capability[Any], contract: Contract
) -> list[Rule[Any]]:
    """Community rules opt in like grammars: a rule runs only when the
    contract names one of its ``target_semantics`` in ``extra_grammars``.

    An un-opted community rule — even one targeting a shipped grammar —
    never affects results, keeping extension behavior deterministic per
    contract.
    """
    extra_grammars = set(getattr(contract, "extra_grammars", ()))
    return [
        rule
        for rule in get_extended_rules(capability.name)
        if extra_grammars & rule.target_semantics
    ]
