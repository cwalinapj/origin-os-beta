# Solana Registry Integration Specification

This document defines the stable integration boundary between Origin attestation
verification and a Solana-backed key registry.

Scope:

- Defines identity lookup semantics for `(owner_agent_id, key_id)`.
- Defines public-key resolution behavior expected by verifiers.
- Defines payload fields that MUST be covered by signatures.
- Defines PDA seed conventions for deterministic address derivation.
- Does **not** require or define on-chain program implementation details beyond
  the compatibility boundary.

## 1. Lookup model

The registry identity key is the ordered tuple:

`(owner_agent_id, key_id)`

Normative requirements:

1. `owner_agent_id` MUST be a non-empty UTF-8 string identifying the logical
   Origin agent owner.
2. `key_id` MUST be a non-empty UTF-8 string scoped under `owner_agent_id`.
3. The tuple MUST be treated as case-sensitive and byte-exact.
4. The tuple is the only logical lookup key for key resolution. Verifiers MUST
   NOT resolve by public key alone when owner binding is required.

## 2. Public-key resolution flow

Given an attestation payload with `owner_agent_id` and `key_id`, verifiers
resolve keys as follows:

1. Parse tuple values from the signed payload.
2. Derive the registry account address using the PDA seed convention in
   [Section 4](#4-pda-seed-convention).
3. Fetch the registry account data at that address.
4. Validate that stored `owner_agent_id` and `key_id` exactly match payload
   tuple values.
5. Validate key status is active (not revoked or otherwise disabled by the
   registry semantics in force).
6. Extract the Ed25519 public key bytes.
7. Verify the signature over the canonical payload bytes using the resolved
   public key.

If any step fails, verification MUST fail.

## 3. Signed payload fields (identity binding)

To prevent identity/key substitution, the signed payload MUST include at least:

- `owner_agent_id`
- `key_id`

Implementations SHOULD also include any additional replay or context fields
required by attestation semantics (for example, chain digest, timestamp,
purpose/version, and nonce/run identifiers), but those fields are outside this
registry-boundary contract.

Verifier requirement:

- Signature verification is only valid when payload `(owner_agent_id, key_id)`
  and resolved registry `(owner_agent_id, key_id)` are exact matches.

## 4. PDA seed convention

For compatibility with the current Solana registry program shape, the `agent_key`
PDA MUST be derived from:

- static seed prefix: `b"agent_key"`
- `sha256(owner_agent_id UTF-8 bytes)`
- `sha256(key_id UTF-8 bytes)`

In notation:

`PDA("agent_key", SHA256(owner_agent_id), SHA256(key_id))`

Notes:

- The hashed component convention is normative for this boundary.
- Raw unhashed `owner_agent_id`/`key_id` seeds are out of spec.
- Future on-chain implementations MUST preserve this seed convention for
  cross-implementation compatibility.

## 5. Non-goals

- Defining Solana instruction formats.
- Defining account rent/space policy.
- Requiring a specific program ID at this stage.

Those details may be added later without breaking this boundary, provided
Sections 1-4 remain stable.
