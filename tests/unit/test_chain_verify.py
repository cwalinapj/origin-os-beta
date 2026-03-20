"""Tests for chain verification."""

import pytest
from origin_protocol_core.manifest import ManifestV1
from origin_chain_verify import verify_chain


def make_step(step_index: int, previous_digest: str | None, **kwargs) -> ManifestV1:
    defaults = {
        "run_id": "run-chain-test",
        "step_index": step_index,
        "agent_id": "agent-x",
        "action": f"action_{step_index}",
        "inputs": {},
        "outputs": {},
        "timestamp_utc": f"2026-01-01T00:00:0{step_index}Z",
        "previous_step_digest": previous_digest,
        "metadata": {},
    }
    defaults.update(kwargs)
    return ManifestV1(**defaults)


def test_two_step_chain_passes():
    step0 = make_step(0, None)
    step1 = make_step(1, step0.digest())
    summary = verify_chain([step0, step1])
    assert summary.passed


def test_single_step_passes():
    step0 = make_step(0, None)
    summary = verify_chain([step0])
    assert summary.passed


def test_broken_previous_step_digest_fails():
    step0 = make_step(0, None)
    step1 = make_step(1, "0" * 64)  # wrong digest
    summary = verify_chain([step0, step1])
    assert not summary.passed
    # Find the failing chain result
    failing = [r for r in summary.chain_results if not r.passed]
    assert len(failing) >= 1
    assert "hash_linkage" in failing[0].check


def test_first_step_with_previous_fails():
    step0 = make_step(0, "a" * 64)  # should be None
    summary = verify_chain([step0])
    assert not summary.passed


def test_wrong_step_index_fails():
    step0 = make_step(0, None)
    # Manually set wrong step_index
    step1 = ManifestV1(
        run_id="run-chain-test",
        step_index=5,  # wrong
        agent_id="agent-x",
        action="action_1",
        inputs={},
        outputs={},
        timestamp_utc="2026-01-01T00:00:01Z",
        previous_step_digest=step0.digest(),
        metadata={},
    )
    summary = verify_chain([step0, step1])
    assert not summary.passed
