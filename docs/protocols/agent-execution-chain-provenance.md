# Agent Execution Chain Provenance

This document captures the architecture and trust model for Origin OS Beta
agent execution chain provenance.

## Architecture

The implementation is split into focused modules:

- `origin_protocol_core.manifest.ManifestV1` and `GENESIS` define the core step
  record and genesis linkage marker.
- `origin_protocol_core.canonical` provides canonicalization/hash/date helpers.
- `origin_protocol_core.types` provides common verification result and validator
  types.
- `origin_protocol_core.chain_store.ChainStore` defines the backend storage
  protocol.
- `origin_chain_verify` contains step validators, chain validators,
  `verify_chain()`, and `VerifiedChainStore`.
- `origin_attestation` contains attestation payload construction plus signing and
  signature verification.
- `origin_backend_memory` contains `InMemoryChainStore` as a reference backend.

## Trust model

The provenance chain is tamper-evident through canonical JSON hashing and
step-to-step digest linkage.

Attestations are signed with Ed25519. Verifiers must bind the attestation key to
its expected owner identity (for example through an external key registry) so a
payload cannot claim one identity while being signed by an unrelated key.
