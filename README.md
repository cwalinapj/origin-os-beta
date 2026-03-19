# Origin OS Beta

Origin OS Beta is the next-generation core of Origin OS: a platform for verifiable agent execution, execution storage protocols, and signed attestations.

It is being designed for systems that:
1. generate or modify code
2. run it in isolated environments
3. observe outputs and failures
4. patch and retry
5. preserve a tamper-evident execution history

## Core focus

Origin OS Beta is centered on:

- execution manifests
- cryptographic hash chains across steps
- chain verification
- provenance and policy validation
- signed attestations
- chain-store backends
- artifact indexing, archival, and retention design

## Why this repo exists

The earlier Origin OS repository grew around service orchestration, tool integrations, and UI workflows.

This repository starts from a different center of gravity:
- execution integrity
- replayability
- auditability
- storage protocols
- verifiable agent behavior

## Core concepts

### Manifest
A canonical record of one execution step.

A manifest can include:
- `run_id`
- `step_id`
- `sequence_no`
- `agent_id`
- runner / VM / model metadata
- timestamps
- exit code
- hashes of source, stdout, stderr, and results
- `previous_step_digest`

### Chain
An ordered sequence of manifests linked by digest.

### Verification
Validation of:
- structure
- digest integrity
- linkage
- sequence consistency
- timestamp consistency
- provenance constraints
- policy constraints

### Attestation
A signed summary of a completed run, suitable for external verification or registry anchoring.

## Repository layout

```text
origin-os-beta/
├── README.md
├── LICENSE
├── .github/
├── docs/
│   ├── architecture/
│   ├── protocols/
│   ├── adr/
│   └── runbooks/
├── specs/
│   ├── manifests/
│   ├── chain-verification/
│   ├── attestation/
│   └── chain-store/
├── schemas/
│   ├── jsonschema/
│   └── migrations/
├── fixtures/
│   ├── valid/
│   ├── invalid/
│   ├── chains/
│   └── attestations/
├── libs/
│   ├── protocol-core/
│   ├── chain-verify/
│   ├── attestation/
│   └── crypto/
├── backends/
│   ├── memory/
│   ├── sqlite/
│   └── postgres/
├── services/
├── tools/
└── tests/


Planned library boundaries
	•	libs/protocol-core/ — manifests, shared types, canonicalization
	•	libs/chain-verify/ — step and chain validators, verification engine
	•	libs/attestation/ — attestation payloads, signing, verification
	•	libs/crypto/ — Ed25519 helpers, fingerprints, Merkle utilities
	•	backends/ — chain-store implementations

Verification model

Each execution step is sealed into a canonical manifest and linked to the previous step digest.

This makes a run:
	•	replayable
	•	tamper-evident
	•	attributable
	•	auditable

Verification is expected at two levels:
	•	append-time validation at the persistence boundary
	•	full-chain audit verification before attestation

Attestation model

Completed runs can be reduced to a compact attestation payload and signed with Ed25519.

This is intended to support:
	•	external verification
	•	registry anchoring
	•	compact proof of a full execution trace without publishing every step

Current priorities
	•	stabilize ManifestV1
	•	finalize chain verification behavior
	•	implement signed attestation flow
	•	define ChainStore backends
	•	add valid/invalid fixtures
	•	build compatibility and audit tests

Contributing

For protocol changes, please include:
	•	spec updates
	•	schema updates where applicable
	•	fixtures for valid and invalid cases
	•	tests for verification and compatibility behavior

Status

Early active development.
