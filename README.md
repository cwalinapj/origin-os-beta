# Origin OS Beta

Origin OS Beta is the next-generation core of Origin OS, focused on verifiable agent execution, execution storage protocols, and signed attestations.

It is designed for systems that:
1. generate or modify code
2. run it in isolated environments
3. observe outputs and failures
4. patch and retry
5. preserve a tamper-evident execution history

## Core focus

Origin OS Beta is centered on:

- canonical execution manifests
- cryptographic hash chains across steps
- chain verification
- provenance and policy validation
- signed attestations
- pluggable chain-store backends
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
- runner, VM, and model metadata
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
├── .gitignore
├── .github/
│   └── workflows/
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
├── tools/
│   └── cli/
└── tests/
    ├── unit/
    ├── integration/
    ├── compatibility/
    └── e2e/
```

## Quick start

```bash
# Install all libs in development mode
pip install -e libs/protocol-core
pip install -e libs/crypto
pip install -e libs/chain-verify
pip install -e libs/attestation
pip install -e backends/memory
pip install -e tools/cli

# Run tests
pytest tests/

# Verify a fixture chain
origin-verify verify fixtures/valid/chain_two_steps.json
```

## Implementation status

| Component | Status |
|---|---|
| `libs/protocol-core` | Implemented — `ManifestV1`, canonical JSON, `ChainStore` protocol |
| `libs/chain-verify` | Implemented — step/chain validators, `verify_chain()` |
| `libs/attestation` | Implemented — Ed25519 sign/verify, payload builder |
| `libs/crypto` | Implemented — key generation, fingerprints, Merkle root |
| `backends/memory` | Implemented — in-memory store for testing |
| `backends/sqlite` | Implemented — SQLite-backed store |
| `tools/cli` | Implemented — `origin-verify verify` command |
| `backends/postgres` | Placeholder |
| `specs/` | Placeholder — stubs in place |
| `docs/` | Placeholder — stubs in place |

## Current priorities

1. Stabilise `ManifestV1` schema and canonical digest
2. Complete chain verification with full error reporting
3. Add SQLite backend with migration support
4. Publish fixture compatibility test suite
5. CLI tool for chain inspection and verification

## License

MIT — see [LICENSE](LICENSE)
