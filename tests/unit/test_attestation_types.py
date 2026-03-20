"""Tests for attestation typed models and serialization."""

import pytest

from origin_attestation import AttestationPayload, SignedAttestation


def test_signed_attestation_serialization_roundtrip() -> None:
    payload = AttestationPayload(
        run_id="run-attestation-types",
        step_count=2,
        first_step_digest="a" * 64,
        last_step_digest="b" * 64,
        chain_digest="c" * 64,
        timestamp_utc="2026-01-01T00:02:00Z",
    )
    signed_attestation = SignedAttestation(
        payload=payload,
        signature="d" * 128,
        signature_alg="ed25519",
        key_id="e" * 64,
        signed_fields_sha256="f" * 64,
    )

    assert SignedAttestation.from_dict(signed_attestation.to_dict()) == signed_attestation


def test_signed_attestation_from_dict_missing_required_field_raises() -> None:
    with pytest.raises(ValueError, match="missing required signed attestation field: key_id"):
        SignedAttestation.from_dict(
            {
                "payload": {
                    "run_id": "run-attestation-types",
                    "step_count": 1,
                    "first_step_digest": "a" * 64,
                    "last_step_digest": "a" * 64,
                    "chain_digest": "a" * 64,
                    "timestamp_utc": "2026-01-01T00:02:00Z",
                },
                "signature": "d" * 128,
                "signature_alg": "ed25519",
                "signed_fields_sha256": "f" * 64,
            }
        )
