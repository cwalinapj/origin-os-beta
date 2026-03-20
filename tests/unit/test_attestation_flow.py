"""Tests for end-to-end attestation audit-and-sign flow."""

import pytest
from origin_attestation import (
    AttestationPayload,
    audit_and_sign_attestation,
    verify_attestation_signature,
)
from origin_backend_memory import InMemoryChainStore
from origin_crypto import generate_keypair
from origin_protocol_core.manifest import ManifestV1


class InMemoryAttestationStore:
    def __init__(self) -> None:
        self.by_run_id: dict[str, dict] = {}

    def put_signed_attestation(self, run_id: str, signed_attestation: dict) -> None:
        self.by_run_id[run_id] = signed_attestation


def _step(
    *,
    run_id: str,
    step_index: int,
    previous_step_digest: str | None,
) -> ManifestV1:
    return ManifestV1(
        run_id=run_id,
        step_index=step_index,
        agent_id="agent-attest-flow",
        action=f"action-{step_index}",
        inputs={},
        outputs={},
        timestamp_utc=f"2026-01-01T00:00:0{step_index}Z",
        previous_step_digest=previous_step_digest,
        metadata={},
    )


def test_audit_and_sign_attestation_successful_sign_store() -> None:
    run_id = "run-attestation-flow-success"
    chain_store = InMemoryChainStore()
    attestation_store = InMemoryAttestationStore()
    keypair = generate_keypair()

    step0 = _step(run_id=run_id, step_index=0, previous_step_digest=None)
    step1 = _step(run_id=run_id, step_index=1, previous_step_digest=step0.digest())
    chain_store.append(step0)
    chain_store.append(step1)

    signed = audit_and_sign_attestation(
        run_id=run_id,
        chain_store=chain_store,
        attestation_store=attestation_store,
        timestamp_utc="2026-01-01T00:02:00Z",
        private_key_bytes=keypair.private_bytes,
    )

    assert attestation_store.by_run_id[run_id] == signed
    assert signed["signature_alg"] == "ed25519"
    assert signed["payload"]["run_id"] == run_id
    assert "key_id" in signed
    assert "signed_fields_sha256" in signed


def test_audit_and_sign_attestation_rejects_invalid_chain() -> None:
    run_id = "run-attestation-flow-invalid"
    chain_store = InMemoryChainStore()
    attestation_store = InMemoryAttestationStore()
    keypair = generate_keypair()

    step0 = _step(run_id=run_id, step_index=0, previous_step_digest=None)
    step1 = _step(run_id=run_id, step_index=1, previous_step_digest="0" * 64)
    chain_store.append(step0)
    chain_store.append(step1)

    with pytest.raises(ValueError, match="chain verification failed"):
        audit_and_sign_attestation(
            run_id=run_id,
            chain_store=chain_store,
            attestation_store=attestation_store,
            timestamp_utc="2026-01-01T00:02:00Z",
            private_key_bytes=keypair.private_bytes,
        )

    assert run_id not in attestation_store.by_run_id


def test_attestation_signature_verification_roundtrip() -> None:
    run_id = "run-attestation-flow-roundtrip"
    chain_store = InMemoryChainStore()
    attestation_store = InMemoryAttestationStore()
    keypair = generate_keypair()

    step0 = _step(run_id=run_id, step_index=0, previous_step_digest=None)
    chain_store.append(step0)

    signed = audit_and_sign_attestation(
        run_id=run_id,
        chain_store=chain_store,
        attestation_store=attestation_store,
        timestamp_utc="2026-01-01T00:02:00Z",
        private_key_bytes=keypair.private_bytes,
    )
    payload = AttestationPayload.from_dict(signed["payload"])
    signature = bytes.fromhex(signed["signature"])

    assert verify_attestation_signature(payload, signature, keypair.public_bytes)
