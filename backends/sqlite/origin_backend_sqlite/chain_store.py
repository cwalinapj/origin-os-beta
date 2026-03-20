"""SQLite-backed implementation of ChainStore."""

from __future__ import annotations

import json
import os
import sqlite3

from origin_protocol_core.errors import ChainStoreError
from origin_protocol_core.manifest import ManifestV1

_DDL = """
CREATE TABLE IF NOT EXISTS manifests (
    run_id       TEXT    NOT NULL,
    step_index   INTEGER NOT NULL,
    data         TEXT    NOT NULL,
    PRIMARY KEY (run_id, step_index)
);
"""


class SqliteChainStore:
    """A SQLite-backed :class:`~origin_protocol_core.ChainStore`.

    *path* is the SQLite database file path.  Pass ``":memory:"`` for an
    in-process database useful in testing.
    """

    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            parent = os.path.dirname(os.path.abspath(path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(_DDL)
        self._conn.commit()

    def append(self, manifest: ManifestV1) -> None:
        """Append *manifest* to its run's chain.

        Raises :exc:`ChainStoreError` if the step_index conflicts.
        """
        existing = self.list_run(manifest.run_id)
        expected_index = len(existing)
        if manifest.step_index != expected_index:
            raise ChainStoreError(
                f"Expected step_index={expected_index} for run '{manifest.run_id}', "
                f"got {manifest.step_index}"
            )
        data = manifest.canonical_json()
        try:
            self._conn.execute(
                "INSERT INTO manifests (run_id, step_index, data) VALUES (?, ?, ?)",
                (manifest.run_id, manifest.step_index, data),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ChainStoreError(str(exc)) from exc

    def get(self, run_id: str, step_index: int) -> ManifestV1:
        row = self._conn.execute(
            "SELECT data FROM manifests WHERE run_id = ? AND step_index = ?",
            (run_id, step_index),
        ).fetchone()
        if row is None:
            raise KeyError(f"No manifest at run_id={run_id!r}, step_index={step_index}")
        return ManifestV1.from_dict(json.loads(row[0]))

    def list_run(self, run_id: str) -> list[ManifestV1]:
        rows = self._conn.execute(
            "SELECT data FROM manifests WHERE run_id = ? ORDER BY step_index",
            (run_id,),
        ).fetchall()
        return [ManifestV1.from_dict(json.loads(r[0])) for r in rows]

    def run_ids(self) -> list[str]:
        rows = self._conn.execute("SELECT DISTINCT run_id FROM manifests").fetchall()
        return [r[0] for r in rows]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
