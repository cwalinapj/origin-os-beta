# ADR 0002: ManifestV1 Scope and ManifestV2 Evolution

**Status**: Accepted

## Context

The codebase currently implements `ManifestV1` as a compact, deterministic execution-step record and uses it in digest computation, chain verification, fixtures, and tests.

Design discussions also include a richer provenance model (for example `step_id`, `sequence_no`, and structured execution metadata). We need a clear decision on whether current V1 is the long-term contract or a stepping stone.

## Decision

1. `ManifestV1` is a **stable contract** for current hash-chain integrity, not a full provenance model.
2. `ManifestV1` intentionally remains minimal and linear (`step_index` + `previous_step_digest`).
3. `ManifestV2` will extend provenance and identity semantics.
4. `step_index` remains canonical in V1.
5. V2 will move canonical ordering to `step_id + sequence_no`, with `step_index` supported as a compatibility field during migration.
6. Stored V1 manifests are preserved as historical source records; migration to V2 is additive, not destructive.

## Consequences

- Existing V1 chains and fixtures remain valid without rewriting historical data.
- Implementations can evolve to richer provenance without breaking current verification behavior.
- Parsers/verifiers must become version-aware.
- Documentation and schema governance must clearly separate V1 and V2 canonicalization rules.

## Alternatives considered

### A) Keep V1 as the only long-term format

Rejected because it constrains provenance features (stable per-step identity, richer execution metadata, and future non-linear references).

### B) Replace V1 immediately and drop support

Rejected because it would break fixture compatibility and historical chain auditability.

### C) Treat V1 as stable for its scope and evolve to V2 with compatibility

Accepted. This minimizes operational risk while enabling richer protocol evolution.
