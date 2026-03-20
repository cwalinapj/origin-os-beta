"""Canonical JSON serialisation and SHA-256 digest helpers."""

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """Return canonical JSON string: keys sorted, no whitespace, UTF-8 safe."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: str | bytes) -> str:
    """Return the lowercase hex SHA-256 digest of *data*.

    Accepts a string (UTF-8 encoded) or raw bytes.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_digest(obj: Any) -> str:
    """Return the SHA-256 digest of the canonical JSON of *obj*."""
    return sha256_hex(canonical_json(obj))
