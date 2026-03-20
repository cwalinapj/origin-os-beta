"""Integration smoke flow for verify + attestation pipeline."""

from origin_attestation import (
    build_attestation_payload,
    sign_attestation,
    verify_attestation_signature,
)
from origin_backend_memory import InMemoryChainStore
from origin_chain_verify import VerifiedChainStore, verify_chain
from origin_crypto import generate_keypair
from origin_protocol_core.manifest import ManifestV1


def _step(step_index: int, previous_step_digest: str | None) -> ManifestV1:
    return ManifestV1(
        run_id="run-smoke",
        step_index=step_index,
        agent_id="agent-smoke",
        action=f"action-{step_index}",
        inputs={},
        outputs={},
        timestamp_utc=f"2026-01-01T00:00:0{step_index}Z",
        previous_step_digest=previous_step_digest,
        metadata={},
    )


def test_smoke_flow_end_to_end() -> None:
    store = VerifiedChainStore(InMemoryChainStore())

    step0 = _step(0, None)
    store.append(step0)
    step1 = _step(1, step0.digest())
    store.append(step1)

    chain = store.list_run("run-smoke")
    summary = verify_chain(chain)
    assert summary.passed

    keypair = generate_keypair()
    payload = build_attestation_payload(chain, timestamp_utc="2026-01-01T00:01:00Z")
    signature = sign_attestation(payload, keypair.private_bytes)
    assert verify_attestation_signature(payload, signature, keypair.public_bytes)
