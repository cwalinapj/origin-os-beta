"""Typed attestation models."""

from __future__ import annotations

from dataclasses import dataclass

from .payloads import AttestationPayload


@dataclass(frozen=True)
class SignedAttestation:
    """Typed representation of a signed attestation envelope."""

    payload: AttestationPayload
    signature: str
    signature_alg: str
    key_id: str
    signed_fields_sha256: str

    def to_dict(self) -> dict:
        return {
            "payload": self.payload.to_dict(),
            "signature": self.signature,
            "signature_alg": self.signature_alg,
            "key_id": self.key_id,
            "signed_fields_sha256": self.signed_fields_sha256,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SignedAttestation":
        return cls(
            payload=AttestationPayload.from_dict(data["payload"]),
            signature=data["signature"],
            signature_alg=data["signature_alg"],
            key_id=data["key_id"],
            signed_fields_sha256=data["signed_fields_sha256"],
        )
