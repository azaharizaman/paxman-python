"""Engine orchestrator — runs the recognition → validation pipeline."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import version as _get_version
from typing import Any

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import freeze_registry, get_capability
from paxman.core.domain import (
    Candidate,
    GrammarRule,
    Provenance,
    RecognizedRep,
    Resolution,
    Rule,
    VersionStamp,
)
from paxman.core.errors import ContractError, RecognitionError, ValidationError


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

    all_rules = capability.get_rules()
    _validate_affinity(capability, all_rules)
    recognitions = _recognize(text, capability, contract)
    had_recognitions = len(recognitions) > 0

    rules = _filter_rules(all_rules, contract)
    candidates = _collect_candidates(recognitions, rules)

    status = _determine_status(candidates, had_recognitions)
    canonical_value = _extract_canonical_value(candidates, status)
    version_stamp = _build_version_stamp(text, candidates, contract, status)

    return ExecutionResult(
        status=status,
        canonicalized_value=canonical_value,
        candidates=tuple(candidates),
        contract=contract,
        version_stamp=version_stamp,
    )


def _recognize(
    text: str, capability: Capability[Any], contract: Contract
) -> list[RecognizedRep[Any]]:
    """Run active grammars and return all recognitions."""
    active_grammar_names = set(contract.active_grammars)
    all_grammars = capability.get_grammars()
    active_grammars = [g for g in all_grammars if g.name in active_grammar_names]

    recognitions: list[RecognizedRep[Any]] = []
    for grammar in active_grammars:
        try:
            notations = grammar.recognize(text)
        except Exception as exc:
            raise RecognitionError(
                rule=grammar.name,
                message=f"Grammar failed: {exc}",
                original_error=exc,
            ) from exc
        grammar_ref = GrammarRule(
            capability_name=capability.name, grammar_name=grammar.name
        )
        for notation in notations:
            recognitions.append(
                RecognizedRep(notation=notation, contract=contract, grammar=grammar_ref)
            )
    return recognitions


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


def _validate_affinity(capability: Capability[Any], rules: list[Rule[Any]]) -> None:
    """Ensure every rule's declared grammars exist in the capability.

    A dangling grammar name would silently exclude a rule from ever running, so
    fail fast at pipeline start rather than producing a wrong (e.g. INVALID) result.
    """
    known_grammars = {g.name for g in capability.get_grammars()}
    for rule in rules:
        unknown = [g for g in rule.target_grammars if g not in known_grammars]
        if unknown:
            raise ContractError(
                f"Rule {rule.name!r} declares unknown grammar(s) "
                f"{sorted(unknown)}; available: {sorted(known_grammars)}"
            )


def _collect_candidates(
    recognitions: list[RecognizedRep[Any]], rules: list[Rule[Any]]
) -> list[Candidate]:
    """Match recognitions against rules and collect candidates.

    Routes each recognition only to rules whose ``target_grammars`` includes the
    producing grammar's name (ARCHITECTURE.md:201), then dedups identical
    candidate tuples so the replay hash is stable regardless of routing.
    """
    candidates: list[Candidate] = []
    for recognition in recognitions:
        grammar_name = recognition.grammar.grammar_name
        for rule in rules:
            if grammar_name not in rule.target_grammars:
                continue
            try:
                if rule.matches(recognition.notation, recognition.contract):
                    canonical = rule.normalize(
                        recognition.notation, recognition.contract
                    )
                    candidates.append(
                        Candidate(
                            value=canonical,
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
    under any future over-declaration of ``target_grammars``.
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


def _build_version_stamp(
    text: str,
    candidates: Sequence[Candidate],
    contract: Contract,
    status: Resolution,
) -> VersionStamp:
    """Compute replay-safe version stamp."""
    replay_hash = _compute_replay_hash(text, candidates, contract, status)
    return VersionStamp(paxman_version=PAXMAN_VERSION, replay_hash=replay_hash)


def _provenance_to_dict(prov: Provenance) -> dict[str, Any]:
    """Serialize a Provenance to a deterministic dict."""
    return {
        "authority": prov.authority,
        "specification_name": prov.specification_name,
        "kind": prov.kind,
        "reference_url": prov.reference_url,
        "version": prov.version,
        "lifecycle": prov.lifecycle,
        "publication_year": prov.publication_year,
    }


def _candidate_to_dict(c: Candidate) -> dict[str, Any]:
    """Serialize a Candidate to a deterministic dict."""
    return {
        "value": c.value,
        "recognition_rule": c.recognition_rule,
        "validation_rule": c.validation_rule,
        "provenance": sorted(
            [_provenance_to_dict(p) for p in c.provenance],
            key=lambda x: x["authority"],
        ),
    }


def _compute_replay_hash(
    text: str,
    candidates: Sequence[Candidate],
    contract: Contract,
    status: Resolution,
) -> str:
    """SHA-256 of canonical bytes for deterministic replay."""
    canonical_bytes: dict[str, Any] = {
        "input": text,
        "contract": contract.as_dict(),
        "status": status.value,
        "candidates": sorted(
            [_candidate_to_dict(c) for c in candidates],
            key=lambda x: (x["value"], x["validation_rule"]),
        ),
    }
    canonical_json = json.dumps(canonical_bytes, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
