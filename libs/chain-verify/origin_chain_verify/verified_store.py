"""Write-validating wrapper around any protocol-core ChainStore."""

from __future__ import annotations

from typing import Generic, TypeVar

from origin_protocol_core.chain_store import ChainStore
from origin_protocol_core.manifest import ManifestV1

from .verifier import verify_chain

TChainStore = TypeVar("TChainStore", bound=ChainStore)


class VerifiedChainStore(Generic[TChainStore]):
    """ChainStore wrapper that verifies the run chain before each append."""

    def __init__(self, inner: TChainStore) -> None:
        self._inner = inner

    def append(self, manifest: ManifestV1) -> None:
        chain = self._inner.list_run(manifest.run_id)
        chain.append(manifest)
        summary = verify_chain(chain)
        if not summary.passed:
            raise ValueError("append rejected: chain verification failed")
        self._inner.append(manifest)

    def get(self, run_id: str, step_index: int) -> ManifestV1:
        return self._inner.get(run_id, step_index)

    def list_run(self, run_id: str) -> list[ManifestV1]:
        return self._inner.list_run(run_id)

    def run_ids(self) -> list[str]:
        return self._inner.run_ids()

