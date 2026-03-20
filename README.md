# origin-os-beta

Origin OS Beta is the next-generation core of Origin OS — a verifiable execution substrate for agent-driven workflows.

## Purpose

This repository implements:
- **Canonical execution manifests** — deterministic, hash-addressable records of each agent step
- **Cryptographic hash chains** — each step commits to the digest of the previous step
- **Chain verification** — validate integrity and continuity of execution chains
- **Signed attestations** — cryptographic proof that a run happened as recorded
- **Pluggable chain-store backends** — in-memory (tests), SQLite (local), extensible to cloud
- **Fixture-driven compatibility testing** — golden fixtures to guard protocol stability

## Core Concepts

| Concept | Description |
|---|---|
| `ManifestV1` | A single agent execution step record |
| `digest` | SHA-256 of canonical JSON of a manifest |
| `previous_step_digest` | Links this step to the prior step, forming a chain |
| `ChainStore` | Protocol interface for reading/writing manifests |
| `Attestation` | Ed25519-signed payload certifying a chain |

## Repository Layout

```
origin-os-beta/
  libs/
    protocol-core/    # ManifestV1, canonical JSON, ChainStore protocol
    chain-verify/     # Step and chain validators, verify_chain()
    attestation/      # Payload builder, sign, verify
    crypto/           # Ed25519, fingerprints, Merkle helpers
  backends/
    memory/           # In-memory ChainStore (testing)
    sqlite/           # SQLite-backed ChainStore (local dev)
  tools/
    cli/              # origin-verify CLI tool
  tests/              # unit, integration, compatibility, e2e
  fixtures/           # valid/invalid JSON fixture chains
  specs/              # Protocol specifications
  docs/               # Architecture and runbooks
  schemas/            # JSON Schema definitions
```

## Quick Start

```bash
# Install protocol-core in development mode
pip install -e libs/protocol-core

# Install chain-verify
pip install -e libs/chain-verify

# Run tests
pytest tests/
```

## Current Priorities

1. Stabilise `ManifestV1` schema and canonical digest
2. Complete chain verification with full error reporting
3. Add SQLite backend with migration support
4. Publish fixture compatibility test suite
5. CLI tool for chain inspection and verification

## License

MIT — see [LICENSE](LICENSE)
