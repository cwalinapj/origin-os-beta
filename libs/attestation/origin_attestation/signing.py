"""Ed25519 signing of attestation payloads."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

import hashlib
from origin_protocol_core.canonical import canonical_json

from .signers import LocalEd25519Signer, Signer
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


def sign_attestation(payload: AttestationPayload, signer: Signer | bytes) -> bytes:
    """Sign *payload* with a signer.

    If *signer* is raw 32-byte Ed25519 seed material, a local signer is used.

    Returns the 64-byte raw Ed25519 signature.
    """
    active_signer = _as_signer(signer)
    return active_signer.sign(payload)


def _as_signer(signer: Signer | bytes) -> Signer:
    return LocalEd25519Signer(signer) if isinstance(signer, bytes) else signer


def audit_and_sign_attestation(
    *,
    run_id: str,
    chain_store: RunChainStore,
    attestation_store: AttestationStore,
    timestamp_utc: str,
    signer: Signer | bytes,
) -> dict:
    """Load, verify, build, sign, and persist a signed attestation for a run."""
    from .payloads import build_attestation_payload
    from .verification import verify_run_or_raise

    manifests = chain_store.list_run(run_id)
    verify_run_or_raise(run_id, manifests)
    payload = build_attestation_payload(manifests, timestamp_utc=timestamp_utc)
    active_signer = _as_signer(signer)
    signature = sign_attestation(payload, active_signer)
    signed_fields_sha256 = hashlib.sha256(
        canonical_json(payload.to_dict()).encode("utf-8")
    ).hexdigest()
    signed_attestation = SignedAttestation(
        payload=payload,
        signature=signature.hex(),
        signature_alg="ed25519",
        key_id=active_signer.key_id,
        signed_fields_sha256=signed_fields_sha256,
    )
    signed_attestation_dict = signed_attestation.to_dict()
    attestation_store.put_signed_attestation(run_id, signed_attestation_dict)
    return signed_attestation_dict
