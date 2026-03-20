"""Ed25519 signing of attestation payloads."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

import hashlib
from origin_protocol_core.canonical import canonical_json

from .key_management import derive_key_id
from .payloads import AttestationPayload
from .types import SignedAttestation

if TYPE_CHECKING:
    from origin_protocol_core.manifest import ManifestV1

SUPPORTED_SIGNATURE_ALGS = frozenset({"ed25519"})


class AttestationStore(Protocol):
    """Minimal persistence protocol for signed attestations."""

    def put_signed_attestation(self, run_id: str, signed_attestation: dict) -> None:
        ...


class RunChainStore(Protocol):
    """Minimal run-chain read protocol needed by attestation flow."""

    def list_run(self, run_id: str) -> list["ManifestV1"]:
        ...


def sign_attestation(payload: AttestationPayload, private_key_bytes: bytes) -> bytes:
    """Sign *payload* with an Ed25519 private key.

    *private_key_bytes* must be 32 bytes of raw Ed25519 seed material.

    Returns the 64-byte raw Ed25519 signature.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    message = canonical_json(payload.to_dict()).encode("utf-8")
    return private_key.sign(message)


def audit_and_sign_attestation(
    *,
    run_id: str,
    chain_store: RunChainStore,
    attestation_store: AttestationStore,
    timestamp_utc: str,
    private_key_bytes: bytes,
) -> dict:
    """Load, verify, build, sign, and persist a signed attestation for a run."""
    from .payloads import build_attestation_payload
    from .verification import verify_run_or_raise
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    manifests = chain_store.list_run(run_id)
    verify_run_or_raise(run_id, manifests)
    payload = build_attestation_payload(manifests, timestamp_utc=timestamp_utc)
    signature = sign_attestation(payload, private_key_bytes)
    signed_fields_sha256 = hashlib.sha256(
        canonical_json(payload.to_dict()).encode("utf-8")
    ).hexdigest()
    public_key_bytes = (
        Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        .public_key()
        .public_bytes_raw()
    )
    signed_attestation = SignedAttestation(
        payload=payload,
        signature=signature.hex(),
        signature_alg="ed25519",
        key_id=derive_key_id(public_key_bytes),
        signed_fields_sha256=signed_fields_sha256,
    )
    signed_attestation_dict = signed_attestation.to_dict()
    attestation_store.put_signed_attestation(run_id, signed_attestation_dict)
    return signed_attestation_dict
