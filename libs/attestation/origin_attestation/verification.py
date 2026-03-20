"""Ed25519 verification of attestation signatures."""

from __future__ import annotations

from origin_protocol_core.canonical import canonical_json

from .payloads import AttestationPayload


def verify_attestation_signature(
    payload: AttestationPayload,
    signature: bytes,
    public_key_bytes: bytes,
) -> bool:
    """Verify that *signature* is a valid Ed25519 signature of *payload*.

    *public_key_bytes* must be 32 bytes of raw Ed25519 public key material.

    Returns ``True`` on success, ``False`` if the signature is invalid.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    message = canonical_json(payload.to_dict()).encode("utf-8")
    try:
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        return False
