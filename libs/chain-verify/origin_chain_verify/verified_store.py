"""Write-validating wrapper around any protocol-core ChainStore."""

from __future__ import annotations

from typing import Generic, TypeVar

from origin_protocol_core.chain_store import ChainStore
from origin_protocol_core.manifest import ManifestV1

from .validators_step import run_step_validators
from .verifier import verify_chain

TChainStore = TypeVar("TChainStore", bound=ChainStore)


class VerifiedChainStore(Generic[TChainStore]):
    """ChainStore wrapper that verifies the run chain before each append."""

    def __init__(self, inner: TChainStore) -> None:
        self._inner = inner

    def append(self, manifest: ManifestV1) -> None:
        chain = self._inner.list_run(manifest.run_id)
        expected_index = len(chain)
        if manifest.step_index != expected_index:
            raise ValueError(
                f"append rejected: expected step_index={expected_index}, got {manifest.step_index}"
            )

        expected_previous = chain[-1].digest() if chain else None
        if manifest.previous_step_digest != expected_previous:
            raise ValueError(
                "append rejected: previous_step_digest does not match current head digest"
            )

        step_results = run_step_validators(manifest, expected_index=manifest.step_index)
        if not all(result.passed for result in step_results):
            raise ValueError("append rejected: manifest validation failed")

        summary = verify_chain(chain + [manifest])
        if not summary.passed:
            raise ValueError("append rejected: chain verification failed")

        self._inner.append(manifest)

    def get(self, run_id: str, step_index: int) -> ManifestV1:
        return self._inner.get(run_id, step_index)

    def list_run(self, run_id: str) -> list[ManifestV1]:
        return self._inner.list_run(run_id)

    def audit_run(self, run_id: str):
        return verify_chain(self._inner.list_run(run_id))

    def run_ids(self) -> list[str]:
        return self._inner.run_ids()
