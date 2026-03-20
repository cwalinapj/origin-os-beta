"""Tests for signer abstractions."""

from origin_attestation import LocalEd25519Signer, build_attestation_payload, sign_attestation
from origin_crypto import generate_keypair
from origin_protocol_core.manifest import ManifestV1


def _make_chain() -> list[ManifestV1]:
    step0 = ManifestV1(
        run_id="run-signers-test",
        step_index=0,
        agent_id="agent-signers",
        action="start",
        inputs={},
        outputs={},
        timestamp_utc="2026-01-01T00:00:00Z",
        previous_step_digest=None,
        metadata={},
    )
    return [step0]


def test_local_ed25519_signer_properties_and_signing() -> None:
    keypair = generate_keypair()
    signer = LocalEd25519Signer(keypair.private_bytes)
    payload = build_attestation_payload(_make_chain(), timestamp_utc="2026-01-01T00:01:00Z")
    signature = sign_attestation(payload, signer)

    assert signer.public_key_bytes == keypair.public_bytes
    assert len(signer.key_id) == 64
    assert len(signature) == 64
