"""Tests for in-memory backend."""

import pytest
from origin_protocol_core.errors import ChainStoreError
from origin_protocol_core.manifest import ManifestV1
from origin_backend_memory import MemoryChainStore


def make_manifest(step_index: int, prev_digest: str | None) -> ManifestV1:
    return ManifestV1(
        run_id="run-mem-test",
        step_index=step_index,
        agent_id="agent-z",
        action=f"action_{step_index}",
        inputs={},
        outputs={},
        timestamp_utc=f"2026-01-01T00:00:0{step_index}Z",
        previous_step_digest=prev_digest,
        metadata={},
    )


def test_append_and_list():
    store = MemoryChainStore()
    m0 = make_manifest(0, None)
    m1 = make_manifest(1, m0.digest())
    store.append(m0)
    store.append(m1)
    result = store.list_run("run-mem-test")
    assert len(result) == 2
    assert result[0].step_index == 0
    assert result[1].step_index == 1


def test_get():
    store = MemoryChainStore()
    m0 = make_manifest(0, None)
    store.append(m0)
    fetched = store.get("run-mem-test", 0)
    assert fetched.digest() == m0.digest()


def test_out_of_order_raises():
    store = MemoryChainStore()
    m1 = make_manifest(1, "x" * 64)
    with pytest.raises(ChainStoreError):
        store.append(m1)


def test_run_ids():
    store = MemoryChainStore()
    m0 = make_manifest(0, None)
    store.append(m0)
    assert "run-mem-test" in store.run_ids()
