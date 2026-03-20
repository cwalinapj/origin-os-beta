"""Tests for agent key lifecycle helpers."""

from origin_attestation import (
    derive_key_id,
    load_or_create_agent_signing_key,
    revoke_agent_signing_key,
)


class _MemorySecretStore:
    def __init__(self):
        self._data: dict[str, bytes] = {}

    def read(self, path: str) -> bytes | None:
        return self._data.get(path)

    def write(self, path: str, value: bytes) -> None:
        self._data[path] = value

    def delete(self, path: str) -> None:
        self._data.pop(path, None)


def test_load_or_create_persists_and_reloads_same_key():
    store = _MemorySecretStore()
    path = "secret/agent/keys/agent-1"

    k1 = load_or_create_agent_signing_key(store, path)
    k2 = load_or_create_agent_signing_key(store, path)

    assert k1.private_key_bytes == k2.private_key_bytes
    assert k1.public_key_bytes == k2.public_key_bytes
    assert k1.key_id == k2.key_id
    assert k1.key_id == derive_key_id(k1.public_key_bytes)


def test_revoke_deletes_stored_key():
    store = _MemorySecretStore()
    path = "secret/agent/keys/agent-2"
    _ = load_or_create_agent_signing_key(store, path)
    assert store.read(path) is not None

    revoke_agent_signing_key(store, path)
    assert store.read(path) is None
