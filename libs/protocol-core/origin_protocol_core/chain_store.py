"""ChainStore protocol — the interface all backend implementations must satisfy."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .manifest import ManifestV1
from .types import Digest


@runtime_checkable
class ChainStore(Protocol):
    """Read/write interface for manifest chains.

    Implementations must be provided by backend packages (e.g.
    ``origin-backend-memory``, ``origin-backend-sqlite``).  The protocol is
    intentionally minimal so that backends stay decoupled from service logic.
    """

    def append(self, manifest: ManifestV1) -> None:
        """Persist *manifest* to the store.

        The store SHOULD validate that ``manifest.step_index`` is the next
        expected index for ``manifest.run_id`` and raise
        :exc:`~origin_protocol_core.errors.ChainStoreError` on conflict.
        """
        ...

    def get(self, run_id: str, step_index: int) -> ManifestV1:
        """Return the manifest at *step_index* for *run_id*.

        Raises :exc:`KeyError` if not found.
        """
        ...

    def list_run(self, run_id: str) -> list[ManifestV1]:
        """Return all manifests for *run_id*, ordered by *step_index*."""
        ...

    def run_ids(self) -> list[str]:
        """Return all run IDs known to this store."""
        ...
