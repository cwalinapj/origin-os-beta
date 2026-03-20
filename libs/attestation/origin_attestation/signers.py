"""Signer abstractions for attestation signing."""

from __future__ import annotations

from typing import Protocol

from origin_crypto.ed25519 import Ed25519Signer
from origin_protocol_core.canonical import canonical_json

from .key_management import derive_key_id
from .payloads import AttestationPayload


class Signer(Protocol):
    """Abstract signer used by attestation flows."""

    def sign(self, payload: AttestationPayload) -> bytes:
        """Sign an attestation payload and return raw signature bytes."""
        ...

    @property
    def public_key_bytes(self) -> bytes:
        ...

    @property
    def key_id(self) -> str:
        ...


class LocalEd25519Signer:
    """Local Ed25519 signer backed by raw private key bytes."""

    def __init__(self, private_key_bytes: bytes) -> None:
        self._signer = Ed25519Signer(private_key_bytes)

    def sign(self, payload: AttestationPayload) -> bytes:
        message = canonical_json(payload.to_dict()).encode("utf-8")
        return self._signer.sign(message)

    @property
    def public_key_bytes(self) -> bytes:
        return self._signer.public_bytes

    @property
    def key_id(self) -> str:
        return derive_key_id(self.public_key_bytes)
