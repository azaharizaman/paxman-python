# ExecutionArtifact `replay_hash`

## What it's for

Mandate Law 12 — **replayability**: `replay(artifact, contract) == artifact` byte-for-byte. The hash is the integrity guard that proves the artifact hasn't been tampered with between production and replay.

## How it's produced

1. **`ExecutionArtifact.__attrs_post_init__`** (artifact.py:67-76) — called automatically after construction. It calls `self.canonical_bytes()` and hashes the result:

   ```python
   hashlib.sha256(self.canonical_bytes()).hexdigest()
   ```

2. **`canonical_bytes()`** (artifact.py:78-142) — produces the deterministic byte serialization. It builds a dict of all meaningful fields and serializes with `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. The critical inputs are:
   - `status`, `value`, `candidates`
   - `evidence` — each as `(rule, detail, (authority.name, authority.version, authority.kind, authority.retrieved_at))` triples. Authority citation is included so a changed/stale edition breaks the hash.
   - `contract` — serialized via `contract.as_dict()`
   - `version_stamp` — `paxman_version`, `contract_version`, `capabilities_hash`, `configuration_version`
   - `authorities` — sorted by name for byte-stability, each with full edition metadata (name, edition, kind, version, publisher, lifecycle, checksum, etc.)

3. **`_compute_replay_hash()`** (replay.py:97-108) — the verification side. Independently recomputes `sha256(canonical_bytes())` during replay, *without* trusting the stored value. This catches forged artifacts where fields were mutated after construction (even though `@attrs.frozen` prevents reassignment, deserialization or manual object construction could bypass it).

## How it's verified

During `replay()` (replay.py:77-80):

```python
if artifact.replay_hash != _compute_replay_hash(artifact):
    raise CanonicalizationError("replay_hash mismatch: artifact content does not match its stored hash")
```

The hash verification runs **before** edition interpretation — if the artifact is forged or corrupted, you fail fast with a clear integrity error rather than producing nonsensical results.

## Why it breaks on edition changes

The `authorities` tuple is serialized into `canonical_bytes()`. If you ship a new edition of (say) ISO 3166-1, an artifact produced with the old edition will have a different `canonical_bytes()` than one produced with the new edition — even for the same input — because the authority metadata differs. This is intentional: it pins the artifact to the exact provenance context that produced it.
