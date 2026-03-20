"""Attestation payload construction."""

from __future__ import annotations

from dataclasses import dataclass

from origin_protocol_core.manifest import ManifestV1
from origin_protocol_core.types import Digest


@dataclass
class AttestationPayload:
    """The data that is signed to produce an attestation.

    *chain_digest* is the SHA-256 digest of the canonical JSON of all manifest
    digests in order (i.e. the Merkle-like root of the chain).
    """

    run_id: str
    step_count: int
    first_step_digest: Digest
    last_step_digest: Digest
    chain_digest: Digest
    timestamp_utc: str

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "step_count": self.step_count,
            "first_step_digest": self.first_step_digest,
            "last_step_digest": self.last_step_digest,
            "chain_digest": self.chain_digest,
            "timestamp_utc": self.timestamp_utc,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttestationPayload":
        return cls(
            run_id=data["run_id"],
            step_count=data["step_count"],
            first_step_digest=data["first_step_digest"],
            last_step_digest=data["last_step_digest"],
            chain_digest=data["chain_digest"],
            timestamp_utc=data["timestamp_utc"],
        )


def build_attestation_payload(
    manifests: list[ManifestV1], timestamp_utc: str
) -> AttestationPayload:
    """Build an :class:`AttestationPayload` from a verified chain.

    *manifests* must be ordered by step_index.
    """
    from origin_protocol_core.canonical import canonical_digest

    if not manifests:
        raise ValueError("Cannot attest an empty chain")

    digests = [m.digest() for m in manifests]
    # chain_digest = digest of the ordered list of step digests
    chain_digest = canonical_digest(digests)

    return AttestationPayload(
        run_id=manifests[0].run_id,
        step_count=len(manifests),
        first_step_digest=digests[0],
        last_step_digest=digests[-1],
        chain_digest=chain_digest,
        timestamp_utc=timestamp_utc,
    )
