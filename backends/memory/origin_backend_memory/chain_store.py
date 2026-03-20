"""In-memory implementation of ChainStore."""

from __future__ import annotations

from collections import defaultdict

from origin_protocol_core.errors import ChainStoreError
from origin_protocol_core.manifest import ManifestV1


class MemoryChainStore:
    """A non-persistent, in-memory :class:`~origin_protocol_core.ChainStore`.

    Suitable for unit tests and short-lived runs.  Not thread-safe.
    """

    def __init__(self) -> None:
        self._store: dict[str, list[ManifestV1]] = defaultdict(list)

    def append(self, manifest: ManifestV1) -> None:
        """Append *manifest* to its run's chain.

        Raises :exc:`ChainStoreError` if the step_index is not the next
        expected index for the run.
        """
        chain = self._store[manifest.run_id]
        expected_index = len(chain)
        if manifest.step_index != expected_index:
            raise ChainStoreError(
                f"Expected step_index={expected_index} for run '{manifest.run_id}', "
                f"got {manifest.step_index}"
            )
        chain.append(manifest)

    def get(self, run_id: str, step_index: int) -> ManifestV1:
        """Return the manifest at *step_index* for *run_id*.

        Raises :exc:`KeyError` if not found.
        """
        chain = self._store.get(run_id)
        if chain is None or step_index >= len(chain):
            raise KeyError(f"No manifest at run_id={run_id!r}, step_index={step_index}")
        return chain[step_index]

    def list_run(self, run_id: str) -> list[ManifestV1]:
        """Return all manifests for *run_id*, ordered by step_index."""
        return list(self._store.get(run_id, []))

    def run_ids(self) -> list[str]:
        """Return all run IDs in the store."""
        return list(self._store.keys())
