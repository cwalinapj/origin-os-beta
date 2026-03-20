"""Ed25519 key lifecycle helpers with pluggable secret backends (e.g. Vault)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@dataclass(frozen=True)
class AgentSigningKey:
    """Agent signing key material used by attestation and chain signing flows."""

    private_key_bytes: bytes
    public_key_bytes: bytes
    key_id: str


class SecretStore(Protocol):
    """Minimal secret store protocol used for Vault integration adapters."""

    def read(self, path: str) -> bytes | None:
        """Return secret bytes for *path*, or ``None`` when not found."""
        ...

    def write(self, path: str, value: bytes) -> None:
        """Persist *value* at *path*."""
        ...

    def delete(self, path: str) -> None:
        """Delete secret value at *path* if it exists."""
        ...


def derive_key_id(public_key_bytes: bytes) -> str:
    """Return deterministic key_id = sha256(pubkey_bytes)."""

    return hashlib.sha256(public_key_bytes).hexdigest()


def _generate_private_key_bytes() -> bytes:
    return Ed25519PrivateKey.generate().private_bytes_raw()


def _public_from_private(private_key_bytes: bytes) -> bytes:
    return (
        Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        .public_key()
        .public_bytes_raw()
    )


def load_or_create_agent_signing_key(store: SecretStore, path: str) -> AgentSigningKey:
    """Load an Ed25519 key from *store* or generate and persist it if missing."""

    private_key_bytes = store.read(path)
    if private_key_bytes is None:
        private_key_bytes = _generate_private_key_bytes()
        store.write(path, private_key_bytes)

    public_key_bytes = _public_from_private(private_key_bytes)
    return AgentSigningKey(
        private_key_bytes=private_key_bytes,
        public_key_bytes=public_key_bytes,
        key_id=derive_key_id(public_key_bytes),
    )


def revoke_agent_signing_key(store: SecretStore, path: str) -> None:
    """Revoke (delete) a previously stored agent signing key."""

    store.delete(path)
