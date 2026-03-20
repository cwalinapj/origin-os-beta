"""Canonical JSON serialisation and SHA-256 digest helpers."""

import hashlib
import json
from datetime import datetime
from typing import Any


def canonical_json(obj: Any) -> str:
    """Return canonical JSON string: keys sorted, no whitespace, UTF-8 safe."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: str | bytes) -> str:
    """Return the lowercase hex SHA-256 digest of *data*."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_hex(data: str | bytes) -> str:
    """Return the lowercase hex SHA-256 digest of *data*.

    Accepts a string (UTF-8 encoded) or raw bytes.
    """
    return sha256_bytes(data)


def parse_rfc3339(ts: str) -> datetime:
    """Parse an RFC3339 UTC timestamp string (supports trailing ``Z``)."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def is_hex_sha256(value: Any) -> bool:
    """Return ``True`` if *value* is a valid 64-char lowercase SHA-256 hex string."""
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value.lower())
    )


def canonical_digest(obj: Any) -> str:
    """Return the SHA-256 digest of the canonical JSON of *obj*."""
    return sha256_hex(canonical_json(obj))
