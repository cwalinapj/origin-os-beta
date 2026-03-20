"""Origin Attestation — build, sign, and verify chain attestations."""

from .payloads import AttestationPayload, build_attestation_payload
from .signing import SUPPORTED_SIGNATURE_ALGS, sign_attestation
from .verification import verify_attestation_signature
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
    "sign_attestation",
    "verify_attestation_signature",
    "AgentSigningKey",
    "SecretStore",
    "derive_key_id",
    "load_or_create_agent_signing_key",
    "revoke_agent_signing_key",
]
