# ADR 0001: Canonical JSON for Digest Computation

**Status**: Accepted

## Context

Manifest digests must be deterministic across platforms and implementations.

## Decision

Use canonical JSON serialisation: keys sorted, no extra whitespace, UTF-8 encoded, then SHA-256 hashed.

## Consequences

All implementations must strip non-canonical fields before hashing. The `to_canonical_dict()` method defines what is included.
