"""Compatibility tests using attestation JSON fixtures."""

import json
from pathlib import Path

from origin_attestation import AttestationPayload, verify_attestation_signature

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "attestations"


def load_attestation(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def verify_fixture(path: Path) -> bool:
    fixture = load_attestation(path)
    payload = AttestationPayload.from_dict(fixture["payload"])
    signature = bytes.fromhex(fixture["signature"])
    public_key = bytes.fromhex(fixture["public_key"])
    return verify_attestation_signature(payload, signature, public_key)


def test_valid_signed_payload_fixture():
    assert verify_fixture(FIXTURES_DIR / "valid" / "signed_payload.json")


def test_invalid_mutated_payload_after_signing_fixture():
    assert not verify_fixture(FIXTURES_DIR / "invalid" / "mutated_payload_after_signing.json")


def test_invalid_wrong_public_key_verification_fixture():
    assert not verify_fixture(FIXTURES_DIR / "invalid" / "wrong_public_key_verification.json")
