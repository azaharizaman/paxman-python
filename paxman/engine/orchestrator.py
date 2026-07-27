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
from paxman.core.errors import RecognitionError, ValidationError


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

    recognitions = _recognize(text, capability, contract)
    had_recognitions = len(recognitions) > 0

    rules = _filter_rules(capability, contract)
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


def _filter_rules(capability: Capability[Any], contract: Contract) -> list[Rule[Any]]:
    """Return rules based on pinning, exclusion, and year filter.

    When pinned_rules is set, ONLY those rules run (excluded_rules is ignored).
    """
    all_rules = capability.get_rules()

    if contract.pinned_rules is not None:
        pinned_set = set(contract.pinned_rules)
        active_rules = [r for r in all_rules if r.name in pinned_set]
    else:
        excluded = set(contract.excluded_rules)
        active_rules = [r for r in all_rules if r.name not in excluded]

    if contract.year is not None:
        active_rules = [
            r for r in active_rules if r.provenance.publication_year <= contract.year
        ]
    return active_rules


def _collect_candidates(
    recognitions: list[RecognizedRep[Any]], rules: list[Rule[Any]]
) -> list[Candidate]:
    """Match recognitions against rules and collect candidates."""
    candidates: list[Candidate] = []
    for recognition in recognitions:
        for rule in rules:
            try:
                if rule.matches(recognition.notation, recognition.contract):
                    canonical = rule.normalize(
                        recognition.notation, recognition.contract
                    )
                    candidates.append(
                        Candidate(
                            value=canonical,
                            recognition_rule=recognition.grammar.grammar_name,
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
    return candidates


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
