# Architecture Overview

> Placeholder — full architecture document coming soon.

## Components

- **protocol-core**: defines `ManifestV1`, canonical JSON, and the `ChainStore` protocol interface.
- **chain-verify**: stateless validators that operate on manifests and chains.
- **attestation**: signs and verifies chain attestations using Ed25519.
- **crypto**: low-level cryptographic primitives (Ed25519, SHA-256, Merkle).
- **backends**: concrete `ChainStore` implementations.
- **tools/cli**: command-line interface for chain inspection and verification.

## Data Flow

```
Agent Step → ManifestV1 → ChainStore.append()
                              ↓
                       verify_chain() → ChainVerificationSummary
                              ↓
                  build_attestation_payload() → sign_attestation()
```
