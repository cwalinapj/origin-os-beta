"""Tests for execution harness manifest wiring."""

from origin_backend_memory import MemoryChainStore
from origin_protocol_core.execution_harness import StepExecutionRecord, append_execution_step


def test_append_execution_step_captures_hashes_and_streams():
    store = MemoryChainStore()
    record = StepExecutionRecord(
        run_id="run-harness",
        step_index=0,
        agent_id="agent-h",
        action="sandbox_exec",
        inputs={"cmd": "echo hi"},
        result={"exit_code": 0, "result": {"ok": True}},
        source_snapshot=b"print('hello')\n",
        stdout=b"hello\n",
        stderr=b"",
    )
    manifest = append_execution_step(store, record)
    loaded = store.get("run-harness", 0)

    assert loaded.digest() == manifest.digest()
    assert loaded.outputs["stdout"] == "hello\n"
    assert loaded.outputs["stderr"] == ""
    assert len(loaded.metadata["source_snapshot_sha256"]) == 64
    assert len(loaded.metadata["stdout_sha256"]) == 64
    assert len(loaded.metadata["stderr_sha256"]) == 64
    assert len(loaded.metadata["results_sha256"]) == 64
    assert loaded.previous_step_digest is None


def test_append_execution_step_links_previous_digest():
    store = MemoryChainStore()
    first = append_execution_step(
        store,
        StepExecutionRecord(
            run_id="run-harness-link",
            step_index=0,
            agent_id="agent-h",
            action="step0",
            inputs={},
            result={"exit_code": 0},
            source_snapshot=b"a",
            stdout=b"",
            stderr=b"",
        ),
    )
    second = append_execution_step(
        store,
        StepExecutionRecord(
            run_id="run-harness-link",
            step_index=1,
            agent_id="agent-h",
            action="step1",
            inputs={},
            result={"exit_code": 0},
            source_snapshot=b"b",
            stdout=b"",
            stderr=b"",
        ),
    )
    assert second.previous_step_digest == first.digest()
