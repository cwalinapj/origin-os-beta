"""Integration test for minimal execution harness run lifecycle."""

from origin_attestation import build_attestation_payload
from origin_backend_memory import InMemoryChainStore
from origin_protocol_core.execution_harness import RunLifecycleHarness, StepExecutionRecord


def test_execution_flow_lifecycle_with_memory_backend() -> None:
    store = InMemoryChainStore()
    harness = RunLifecycleHarness(store)
    harness.start_run("run-exec-flow")

    manifest0 = harness.emit_step_manifest(
        StepExecutionRecord(
            run_id="run-exec-flow",
            step_index=0,
            agent_id="agent-exec-flow",
            action="sandbox_exec",
            inputs={"cmd": "echo hello"},
            result={"exit_code": 0},
            source_snapshot=b"print('hello')\n",
            stdout=b"hello\n",
            stderr=b"",
        )
    )
    harness.append_to_store(manifest0)

    manifest1 = harness.emit_step_manifest(
        StepExecutionRecord(
            run_id="run-exec-flow",
            step_index=1,
            agent_id="agent-exec-flow",
            action="sandbox_exec",
            inputs={"cmd": "echo world"},
            result={"exit_code": 0},
            source_snapshot=b"print('world')\n",
            stdout=b"world\n",
            stderr=b"",
        )
    )
    harness.append_to_store(manifest1)

    manifests = harness.finalize_run()
    payload = harness.generate_attestation(
        timestamp_utc="2026-01-01T00:05:00Z",
        build_payload=build_attestation_payload,
    )

    assert len(manifests) == 2
    assert manifests[0].run_id == "run-exec-flow"
    assert manifests[1].previous_step_digest == manifests[0].digest()
    assert payload.run_id == "run-exec-flow"
    assert payload.step_count == 2
    assert payload.last_step_digest == manifests[-1].digest()
