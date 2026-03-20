"""Ed25519 key generation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@dataclass
class Ed25519KeyPair:
    """A raw Ed25519 key pair (seed bytes + public key bytes)."""

    private_bytes: bytes  # 32-byte seed
    public_bytes: bytes   # 32-byte public key


def generate_keypair() -> Ed25519KeyPair:
    """Generate a fresh Ed25519 key pair."""

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()
    public_bytes = private_key.public_key().public_bytes_raw()
    return Ed25519KeyPair(private_bytes=private_bytes, public_bytes=public_bytes)


@dataclass(frozen=True)
class Ed25519Signer:
    """Local Ed25519 signer backed by raw private key bytes."""

    private_bytes: bytes

    def sign(self, message: bytes) -> bytes:
        return Ed25519PrivateKey.from_private_bytes(self.private_bytes).sign(message)

    @property
    def public_bytes(self) -> bytes:
        return (
            Ed25519PrivateKey.from_private_bytes(self.private_bytes)
            .public_key()
            .public_bytes_raw()
        )
