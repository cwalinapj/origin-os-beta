"""Origin Attestation — build, sign, and verify chain attestations."""

from .payloads import AttestationPayload, build_attestation_payload
from .signing import SUPPORTED_SIGNATURE_ALGS, sign_attestation
from .verification import verify_attestation_signature

__all__ = [
    "AttestationPayload",
    "build_attestation_payload",
    "SUPPORTED_SIGNATURE_ALGS",
    "sign_attestation",
    "verify_attestation_signature",
]
