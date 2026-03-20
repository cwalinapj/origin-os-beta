"""Simple Merkle root computation over a list of hex digests."""

from __future__ import annotations

import hashlib


def _sha256_pair(left: str, right: str) -> str:
    """Return SHA-256 hex digest of the concatenation of two hex strings."""
    combined = (left + right).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def merkle_root(digests: list[str]) -> str:
    """Compute the Merkle root of a list of hex digests.

    Uses a simple binary tree: if the number of leaves is odd, the last leaf
    is duplicated.

    Returns the root as a hex digest string.  Returns the empty string for an
    empty input.
    """
    if not digests:
        return ""
    layer = list(digests)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])  # duplicate last element
        layer = [_sha256_pair(layer[i], layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0]
