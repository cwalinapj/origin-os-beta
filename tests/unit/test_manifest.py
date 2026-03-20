"""Basic unit tests for ManifestV1."""

import pytest

from origin_protocol_core.errors import ManifestValidationError
from origin_protocol_core.manifest import ManifestV1


def _manifest() -> ManifestV1:
    return ManifestV1(
        run_id="run-1",
        step_index=0,
        agent_id="agent-a",
        action="start",
        inputs={"k": "v"},
        outputs={"ok": True},
        timestamp_utc="2026-01-01T00:00:00Z",
        previous_step_digest=None,
        metadata={"env": "test"},
    )


def test_manifest_digest_is_stable() -> None:
    m1 = _manifest()
    m2 = _manifest()
    assert m1.digest() == m2.digest()


def test_manifest_from_dict_requires_fields() -> None:
    with pytest.raises(ManifestValidationError):
        ManifestV1.from_dict({"run_id": "run-1"})
