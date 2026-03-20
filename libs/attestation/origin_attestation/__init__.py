"""Origin Attestation — build, sign, and verify chain attestations."""

from .payloads import AttestationPayload, build_attestation_payload
from .signing import SUPPORTED_SIGNATURE_ALGS, AttestationStore, audit_and_sign_attestation, sign_attestation
from .verification import verify_attestation_signature, verify_run_or_raise
from .key_management import (
    AgentSigningKey,
    SecretStore,
    derive_key_id,
    load_or_create_agent_signing_key,
    revoke_agent_signing_key,
)

__all__ = [
    "AttestationPayload",
    "build_attestation_payload",
    "SUPPORTED_SIGNATURE_ALGS",
    "AttestationStore",
    "audit_and_sign_attestation",
    "sign_attestation",
    "verify_attestation_signature",
    "verify_run_or_raise",
    "AgentSigningKey",
    "SecretStore",
    "derive_key_id",
    "load_or_create_agent_signing_key",
    "revoke_agent_signing_key",
]
