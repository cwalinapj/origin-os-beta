"""Ed25519 signing of attestation payloads."""

from __future__ import annotations

from origin_protocol_core.canonical import canonical_json

from .payloads import AttestationPayload

SUPPORTED_SIGNATURE_ALGS = frozenset({"ed25519"})


def sign_attestation(payload: AttestationPayload, private_key_bytes: bytes) -> bytes:
    """Sign *payload* with an Ed25519 private key.

    *private_key_bytes* must be 32 bytes of raw Ed25519 seed material.

    Returns the 64-byte raw Ed25519 signature.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    message = canonical_json(payload.to_dict()).encode("utf-8")
    return private_key.sign(message)
