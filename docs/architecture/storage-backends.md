# Storage Backends

This document describes the behavior and intended use of the built-in `ChainStore` backends.

## Backend matrix

| Backend | Persistence | Ordering assumptions | Concurrency / thread-safety | Intended use |
| --- | --- | --- | --- | --- |
| `InMemoryChainStore` (`MemoryChainStore`) | Non-persistent. Data lives only in process memory and is lost on process exit. | Appends must be contiguous per `run_id` (`step_index` must be exactly the next index, starting at `0`). `list_run()` returns manifests in step order. | **Not thread-safe**. No locking is used around internal state. | Unit tests, local experiments, and short-lived single-process runs. |
| `SqliteChainStore` | Persistent when using a filesystem path. Non-persistent when using `":memory:"`. | Same contiguous append rule (`step_index == len(existing run)`), and `list_run()` is returned ordered by `step_index`. | A single SQLite connection is opened with `check_same_thread=False`, but the backend does not provide application-level locking. Concurrent writers should use external synchronization. | Local development, single-node deployments, and test scenarios that need optional durability. |

## Detailed guarantees and limitations

### In-memory backend (`InMemoryChainStore`)

- **Persistence:** None. State is process-local only.
- **Ordering:** Enforces append-only contiguous ordering per run by validating `step_index`.
- **Concurrency/thread-safety:** Not thread-safe.
- **Intended use:** Fast, ephemeral storage for tests and short-lived workflows.
- **Limitations:** No durability or cross-process sharing.

### SQLite backend (`SqliteChainStore`)

- **Persistence:** Durable across reopen when configured with a file path.
- **Ordering:** Enforces contiguous `step_index` appends; reads are sorted by `step_index`.
- **Concurrency/thread-safety:** Does not guarantee safe concurrent append semantics by itself; synchronize concurrent writers at the application layer.
- **Intended use:** Simple durable backend for local/dev usage and integration tests.
- **Limitations:** Not a distributed store and not designed for high-contention multi-writer workloads without coordination.
