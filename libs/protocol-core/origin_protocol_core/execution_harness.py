"""Execution harness helpers for producing and appending ManifestV1 records."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, TypeVar

from .chain_store import ChainStore
from .manifest import ManifestV1
from .types import JsonDict


def _timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class StepExecutionRecord:
    """Input/output material captured around one sandboxed execution step."""

    run_id: str
    step_index: int
    agent_id: str
    action: str
    inputs: JsonDict
    result: JsonDict
    source_snapshot: bytes
    stdout: bytes = b""
    stderr: bytes = b""
    metadata: JsonDict | None = None


AttestationT = TypeVar("AttestationT")


class RunLifecycleHarness:
    """Minimal execution harness interface for run lifecycle management."""

    def __init__(self, store: ChainStore) -> None:
        self._store = store
        self._run_id: str | None = None
        self._finalized = False

    def start_run(self, run_id: str) -> None:
        self._run_id = run_id
        self._finalized = False

    def emit_step_manifest(self, record: StepExecutionRecord) -> ManifestV1:
        if self._run_id is None:
            raise ValueError("run not started")
        if record.run_id != self._run_id:
            raise ValueError("record run_id does not match started run")
        return _build_manifest_from_record(self._store, record)

    def append_to_store(self, manifest: ManifestV1) -> None:
        if self._run_id is None:
            raise ValueError("run not started")
        if manifest.run_id != self._run_id:
            raise ValueError("manifest run_id does not match started run")
        self._store.append(manifest)

    def finalize_run(self) -> list[ManifestV1]:
        if self._run_id is None:
            raise ValueError("run not started")
        self._finalized = True
        return self._store.list_run(self._run_id)

    def generate_attestation(
        self,
        timestamp_utc: str,
        build_payload: Callable[[list[ManifestV1], str], AttestationT],
    ) -> AttestationT:
        if self._run_id is None:
            raise ValueError("run not started")
        if not self._finalized:
            raise ValueError("run not finalized")
        return build_payload(self._store.list_run(self._run_id), timestamp_utc)


def _build_manifest_from_record(store: ChainStore, record: StepExecutionRecord) -> ManifestV1:
    previous_step_digest = None
    if record.step_index > 0:
        previous_step_digest = store.get(record.run_id, record.step_index - 1).digest()

    outputs = dict(record.result)
    outputs.setdefault("stdout", record.stdout.decode("utf-8", errors="replace"))
    outputs.setdefault("stderr", record.stderr.decode("utf-8", errors="replace"))

    metadata = dict(record.metadata or {})
    metadata.setdefault("source_snapshot_sha256", _sha256_hex_bytes(record.source_snapshot))
    metadata.setdefault("stdout_sha256", _sha256_hex_bytes(record.stdout))
    metadata.setdefault("stderr_sha256", _sha256_hex_bytes(record.stderr))
    metadata.setdefault(
        "results_sha256",
        _sha256_hex_bytes(
            json_dumps_canonical_bytes(record.result),
        ),
    )

    return ManifestV1(
        run_id=record.run_id,
        step_index=record.step_index,
        agent_id=record.agent_id,
        action=record.action,
        inputs=dict(record.inputs),
        outputs=outputs,
        timestamp_utc=_timestamp_utc(),
        previous_step_digest=previous_step_digest,
        metadata=metadata,
    )


def append_execution_step(store: ChainStore, record: StepExecutionRecord) -> ManifestV1:
    """Build a ManifestV1 from *record* and append it as the final step action."""
    manifest = _build_manifest_from_record(store, record)
    store.append(manifest)
    return manifest


def json_dumps_canonical_bytes(value: JsonDict) -> bytes:
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
