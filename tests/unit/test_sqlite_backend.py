"""Tests for SQLite backend."""

from origin_protocol_core.errors import ChainStoreError
from origin_protocol_core.manifest import ManifestV1
from origin_backend_sqlite import SqliteChainStore


def make_manifest(step_index: int, prev_digest: str | None) -> ManifestV1:
    return ManifestV1(
        run_id="run-sqlite-test",
        step_index=step_index,
        agent_id="agent-s",
        action=f"action_{step_index}",
        inputs={},
        outputs={},
        timestamp_utc=f"2026-01-01T00:00:0{step_index}Z",
        previous_step_digest=prev_digest,
        metadata={},
    )


def test_persists_across_reopen(tmp_path):
    db_path = tmp_path / "chain.sqlite3"
    store = SqliteChainStore(str(db_path))
    m0 = make_manifest(0, None)
    m1 = make_manifest(1, m0.digest())
    store.append(m0)
    store.append(m1)
    store.close()

    reopened = SqliteChainStore(str(db_path))
    listed = reopened.list_run("run-sqlite-test")
    assert [m.step_index for m in listed] == [0, 1]
    assert listed[1].previous_step_digest == m0.digest()
    reopened.close()


def test_out_of_order_raises():
    store = SqliteChainStore(":memory:")
    m1 = make_manifest(1, "x" * 64)
    try:
        store.append(m1)
    except ChainStoreError:
        pass
    else:
        raise AssertionError("Expected ChainStoreError for out-of-order step")
    finally:
        store.close()
