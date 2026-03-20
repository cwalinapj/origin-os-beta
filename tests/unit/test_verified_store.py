"""Tests for VerifiedChainStore."""

import pytest
from origin_backend_memory import MemoryChainStore
from origin_chain_verify import VerifiedChainStore
from origin_protocol_core.manifest import ManifestV1


def _step(step_index: int, previous_digest: str | None, run_id: str = "run-verified") -> ManifestV1:
    return ManifestV1(
        run_id=run_id,
        step_index=step_index,
        agent_id="agent-verified",
        action=f"action-{step_index}",
        inputs={},
        outputs={},
        timestamp_utc=f"2026-01-01T00:00:0{step_index}Z",
        previous_step_digest=previous_digest,
        metadata={},
    )


def test_verified_store_accepts_valid_append_sequence() -> None:
    store = VerifiedChainStore(MemoryChainStore())
    step0 = _step(0, None)
    step1 = _step(1, step0.digest())

    store.append(step0)
    store.append(step1)

    manifests = store.list_run("run-verified")
    assert len(manifests) == 2
    assert manifests[0].step_index == 0
    assert manifests[1].step_index == 1


def test_verified_store_rejects_non_contiguous_step_index() -> None:
    store = VerifiedChainStore(MemoryChainStore())

    with pytest.raises(ValueError, match="expected step_index=0, got 1"):
        store.append(_step(1, "0" * 64))


def test_verified_store_rejects_wrong_previous_step_digest() -> None:
    store = VerifiedChainStore(MemoryChainStore())
    step0 = _step(0, None)
    store.append(step0)

    with pytest.raises(ValueError, match="previous_step_digest"):
        store.append(_step(1, "0" * 64))


def test_verified_store_rejects_invalid_manifest_fields() -> None:
    store = VerifiedChainStore(MemoryChainStore())

    with pytest.raises(ValueError, match="manifest validation failed"):
        store.append(
            ManifestV1(
                run_id="run-verified",
                step_index=0,
                agent_id="agent-verified",
                action="",
                inputs={},
                outputs={},
                timestamp_utc="2026-01-01T00:00:00Z",
                previous_step_digest=None,
                metadata={},
            )
        )


def test_verified_store_get_and_list_are_passthroughs() -> None:
    store = VerifiedChainStore(MemoryChainStore())
    step0 = _step(0, None)
    store.append(step0)

    assert store.get("run-verified", 0).digest() == step0.digest()
    assert [m.step_index for m in store.list_run("run-verified")] == [0]


def test_verified_store_audit_run_reverifies_chain() -> None:
    store = VerifiedChainStore(MemoryChainStore())
    step0 = _step(0, None)
    step1 = _step(1, step0.digest())
    store.append(step0)
    store.append(step1)

    summary = store.audit_run("run-verified")
    assert summary.passed
