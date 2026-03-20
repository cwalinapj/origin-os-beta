# Manifest Evolution Plan (V1 → V2)

## Purpose of ManifestV1

`ManifestV1` is the **stable execution-step integrity contract** used by current libraries, fixtures, and verification flows.

Its primary purpose is to provide a deterministic, hash-chainable record for each execution step with:

- step ordering (`step_index`)
- step linkage (`previous_step_digest`)
- minimal execution identity (`run_id`, `agent_id`, `action`)
- canonical digest inputs (`inputs`, `outputs`, `timestamp_utc`, optional `metadata`)

`ManifestV1` is intentionally optimized for:

- deterministic canonical JSON digesting
- simple cross-language implementation
- straightforward chain verification in constrained environments

## What ManifestV1 intentionally does **not** include

`ManifestV1` is not a full provenance graph model. It intentionally excludes:

- globally unique step identifiers (`step_id`)
- richer ordering semantics beyond one run-local integer index
- explicit parent references beyond linear `previous_step_digest`
- typed execution environment fields (runner/model/VM/tool versions)
- artifact-level digest registries (stdout/stderr/source/result digests as first-class fields)
- policy/enforcement metadata beyond generic `metadata`

These are deferred to a future version to keep V1 stable and easy to verify.

## ManifestV2 proposed additions

`ManifestV2` should extend the model while preserving V1 verifiability:

1. **Step identity and ordering**
   - Add `step_id` (stable unique identifier for a step).
   - Add `sequence_no` (explicit ordinal for deterministic ordering).
2. **Provenance detail**
   - Add structured execution context (runner, model, sandbox/runtime metadata).
   - Add explicit artifact digest fields for important outputs.
3. **Relationship modeling**
   - Allow richer parent/reference fields for non-linear or merged execution histories.
4. **Schema versioning**
   - Introduce explicit manifest schema/version field for multi-version parsers.

## Canonical ordering decision (`step_index` vs `step_id + sequence_no`)

**Decision:** `step_index` remains canonical for ManifestV1 and for V1 verification logic.  
For ManifestV2, canonical ordering should move to `step_id + sequence_no`, with `step_index` treated as a compatibility alias during migration.

This keeps existing chains stable while enabling richer identity semantics in V2.

## Backward-compatibility strategy

1. **Version-aware parsing**
   - Parsers detect manifest version and apply version-specific validation rules.
2. **V1 support window**
   - V1 read/verify remains supported for existing stored chains and fixtures.
3. **Dual-write period (recommended)**
   - During rollout, producers may emit V2 manifests and include `step_index` for compatibility where required by old tooling.
4. **Canonical digest separation**
   - V1 and V2 digest canonicalization are version-scoped; do not mix fields across versions when computing digests.

## Migration strategy for stored manifests

Migration should be append-only and reproducible:

1. Inventory stored chains by version (all current chains are V1 unless explicitly marked otherwise).
2. For each V1 step, derive:
   - `step_id` deterministically (e.g., namespaced derivation from `run_id` + `step_index`, or stored mapping table).
   - `sequence_no = step_index`.
3. Persist migrated V2 representation alongside original V1 record (do not mutate/delete historical V1 bytes).
4. Re-verify the migrated chain using V2 rules and store migration metadata (`migrated_from=v1`, migration timestamp/tool version).
5. Keep V1 verifier available for historical audit and dispute resolution.
