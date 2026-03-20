"""SHA-256 fingerprint helpers."""

from __future__ import annotations

import hashlib


def sha256_fingerprint(data: bytes) -> str:
    """Return a colon-separated SHA-256 fingerprint of *data*.

    Example: ``"a1:b2:c3:..."``
    """
    digest = hashlib.sha256(data).digest()
    return ":".join(f"{b:02x}" for b in digest)
