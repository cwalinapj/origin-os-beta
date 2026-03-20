"""Ed25519 key generation helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Ed25519KeyPair:
    """A raw Ed25519 key pair (seed bytes + public key bytes)."""

    private_bytes: bytes  # 32-byte seed
    public_bytes: bytes   # 32-byte public key


def generate_keypair() -> Ed25519KeyPair:
    """Generate a fresh Ed25519 key pair."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()
    public_bytes = private_key.public_key().public_bytes_raw()
    return Ed25519KeyPair(private_bytes=private_bytes, public_bytes=public_bytes)
