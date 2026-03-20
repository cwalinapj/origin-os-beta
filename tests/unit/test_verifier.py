"""Basic unit tests for chain verification."""

from origin_chain_verify import verify_chain
from origin_protocol_core.manifest import ManifestV1


def _step(idx: int, previous_step_digest: str | None) -> ManifestV1:
    return ManifestV1(
        run_id="run-verify",
        step_index=idx,
        agent_id="agent-v",
        action=f"step-{idx}",
        inputs={},
        outputs={},
        timestamp_utc=f"2026-01-01T00:00:0{idx}Z",
        previous_step_digest=previous_step_digest,
        metadata={},
    )


def test_verifier_accepts_linked_chain() -> None:
    step0 = _step(0, None)
    step1 = _step(1, step0.digest())
    assert verify_chain([step0, step1]).passed


def test_verifier_rejects_broken_link() -> None:
    step0 = _step(0, None)
    step1 = _step(1, "0" * 64)
    assert not verify_chain([step0, step1]).passed
