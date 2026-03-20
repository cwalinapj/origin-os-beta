"""Tests for attestation signing and verification."""

from origin_protocol_core.manifest import ManifestV1
from origin_attestation import (
    LocalEd25519Signer,
    SUPPORTED_SIGNATURE_ALGS,
    build_attestation_payload,
    sign_attestation,
    verify_attestation_signature,
)
from origin_crypto import generate_keypair


def make_chain() -> list[ManifestV1]:
    step0 = ManifestV1(
        run_id="run-attest-test",
        step_index=0,
        agent_id="agent-y",
        action="start",
        inputs={},
        outputs={},
        timestamp_utc="2026-01-01T00:00:00Z",
        previous_step_digest=None,
        metadata={},
    )
    step1 = ManifestV1(
        run_id="run-attest-test",
        step_index=1,
        agent_id="agent-y",
        action="end",
        inputs={},
        outputs={},
        timestamp_utc="2026-01-01T00:00:01Z",
        previous_step_digest=step0.digest(),
        metadata={},
    )
    return [step0, step1]


def test_attestation_sign_and_verify():
    chain = make_chain()
    keypair = generate_keypair()
    payload = build_attestation_payload(chain, timestamp_utc="2026-01-01T00:01:00Z")
    signature = sign_attestation(payload, LocalEd25519Signer(keypair.private_bytes))
    assert verify_attestation_signature(payload, signature, keypair.public_bytes)


def test_attestation_verify_wrong_key_fails():
    chain = make_chain()
    keypair1 = generate_keypair()
    keypair2 = generate_keypair()
    payload = build_attestation_payload(chain, timestamp_utc="2026-01-01T00:01:00Z")
    signature = sign_attestation(payload, LocalEd25519Signer(keypair1.private_bytes))
    assert not verify_attestation_signature(payload, signature, keypair2.public_bytes)


def test_attestation_verify_tampered_payload_fails():
    chain = make_chain()
    keypair = generate_keypair()
    payload = build_attestation_payload(chain, timestamp_utc="2026-01-01T00:01:00Z")
    signature = sign_attestation(payload, LocalEd25519Signer(keypair.private_bytes))
    # Tamper with payload
    payload.step_count = 999
    assert not verify_attestation_signature(payload, signature, keypair.public_bytes)


def test_attestation_sign_with_raw_private_key_bytes_still_supported():
    chain = make_chain()
    keypair = generate_keypair()
    payload = build_attestation_payload(chain, timestamp_utc="2026-01-01T00:01:00Z")
    signature = sign_attestation(payload, keypair.private_bytes)
    assert verify_attestation_signature(payload, signature, keypair.public_bytes)


def test_supported_signature_algs_exposes_ed25519():
    assert "ed25519" in SUPPORTED_SIGNATURE_ALGS
